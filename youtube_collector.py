"""
YouTube Collector
유튜브 채널 자막 추출 및 요약 — 주 3회 (월·수·금)

Al Jazeera English / DW News / 연합뉴스TV
youtube-transcript-api로 자막 추출 → Claude API 한국어 요약

출력: data/youtube/yt_summary_YYYYMMDD.json
"""

import json
import logging
import time
from datetime import date, datetime
from pathlib import Path

import feedparser
import requests

from config import (
    YT_DIR, YOUTUBE_CHANNELS, YOUTUBE_SCHEDULE_DAYS,
    ANTHROPIC_API_KEY, CLAUDE_MODEL, USER_AGENT, KEYWORDS_EN, KEYWORDS_KO,
)

logger = logging.getLogger(__name__)

try:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
    YT_AVAILABLE = True
except ImportError:
    YT_AVAILABLE = False
    logger.warning("youtube-transcript-api 미설치. pip install youtube-transcript-api")

import anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def should_run_today() -> bool:
    """오늘 유튜브 수집 실행 여부 (월·수·금)"""
    return datetime.today().weekday() in YOUTUBE_SCHEDULE_DAYS


def get_channel_videos(channel_id: str, max_videos: int = 5) -> list:
    """채널 RSS로 최신 영상 목록 가져오기"""
    videos = []
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        r = requests.get(rss_url, headers={"User-Agent": USER_AGENT}, timeout=10)
        feed = feedparser.parse(r.text)
        for entry in feed.entries[:max_videos]:
            video_id = entry.get("yt_videoid", "")
            if not video_id:
                link = entry.get("link", "")
                if "watch?v=" in link:
                    video_id = link.split("watch?v=")[-1].split("&")[0]
            if video_id:
                videos.append({
                    "video_id":  video_id,
                    "title":     entry.get("title", ""),
                    "published": entry.get("published", ""),
                    "url":       f"https://www.youtube.com/watch?v={video_id}",
                })
    except Exception as e:
        logger.warning(f"[YT RSS] {channel_id} 실패: {e}")
    return videos


def is_iran_related(text: str) -> bool:
    text_lower = text.lower()
    return (
        any(kw.lower() in text_lower for kw in KEYWORDS_EN) or
        any(kw in text for kw in KEYWORDS_KO)
    )


def extract_transcript(video_id: str, lang: str = "en") -> str:
    """자막 추출"""
    if not YT_AVAILABLE:
        return ""
    try:
        lang_codes = ["ko", "en"] if lang == "ko" else ["en", "ko"]
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=lang_codes)
        text = " ".join(t["text"] for t in transcript_list)
        return text[:6000]  # 토큰 절약
    except Exception as e:
        logger.warning(f"[자막] {video_id} 실패: {e}")
        return ""


def summarize_with_claude(title: str, transcript: str, channel_name: str, lang: str) -> dict:
    """Claude API로 자막 요약"""
    if not transcript:
        return {"summary_ko": "", "key_points": [], "iran_relevance": "낮음"}

    prompt = f"""다음 유튜브 영상의 자막을 분석해서 JSON으로 반환하세요.

채널: {channel_name}
영상 제목: {title}
자막 내용:
{transcript}

반환 형식:
{{
  "summary_ko": "한국어 요약 3줄 (각 줄 • 시작, \\n 구분)",
  "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
  "iran_relevance": "높음|중간|낮음",
  "suwon_connection": "수원시 민생과의 연결점 (1줄, 없으면 빈 문자열)"
}}

이란전쟁·에너지·민생 관련 내용이 없으면 iran_relevance를 낮음으로 설정."""

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            system="당신은 이란전쟁 전문 분석가입니다. JSON만 반환하세요.",
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"[Claude 요약] 실패: {e}")
        return {"summary_ko": f"요약 실패: {title}", "key_points": [], "iran_relevance": "중간"}


def run(target_date: str = None) -> Path:
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")

    logger.info(f"=== YouTubeCollector 시작: {target_date} ===")

    if not should_run_today():
        logger.info("오늘은 유튜브 수집 스케줄 아님 (월·수·금만 실행)")
        # 빈 파일 생성 후 반환
        date_str = target_date.replace("-", "")
        out_path = YT_DIR / f"yt_summary_{date_str}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"date": target_date, "summaries": [], "note": "비수집일"}, f, ensure_ascii=False)
        return out_path

    all_summaries = []

    for ch_key, ch_cfg in YOUTUBE_CHANNELS.items():
        logger.info(f"[YT] {ch_cfg['name']} 처리 중...")
        videos = get_channel_videos(ch_cfg["channel_id"], max_videos=5)

        for video in videos:
            # 이란 관련 영상만 처리
            if not is_iran_related(video["title"]):
                continue

            logger.info(f"  → 자막 추출: {video['title'][:50]}")
            transcript = extract_transcript(video["video_id"], ch_cfg["lang"])
            time.sleep(1)

            analysis = summarize_with_claude(
                video["title"], transcript,
                ch_cfg["name"], ch_cfg["lang"]
            )

            if analysis.get("iran_relevance") == "낮음":
                continue

            all_summaries.append({
                "channel":        ch_cfg["name"],
                "channel_key":    ch_key,
                "credibility":    ch_cfg["credibility"],
                "video_id":       video["video_id"],
                "title":          video["title"],
                "url":            video["url"],
                "published":      video["published"],
                "summary_ko":     analysis.get("summary_ko", ""),
                "key_points":     analysis.get("key_points", []),
                "iran_relevance": analysis.get("iran_relevance", "중간"),
                "suwon_connection": analysis.get("suwon_connection", ""),
                "collected_at":   datetime.utcnow().isoformat(),
                "data_type":      "youtube",
            })
            time.sleep(2)

    date_str = target_date.replace("-", "")
    out_path = YT_DIR / f"yt_summary_{date_str}.json"
    output = {
        "date":      target_date,
        "total":     len(all_summaries),
        "summaries": all_summaries,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"=== YouTubeCollector 완료: {len(all_summaries)}건 → {out_path} ===")
    return out_path


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    run(sys.argv[1] if len(sys.argv) > 1 else None)
