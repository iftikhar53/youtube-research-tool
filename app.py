

import argparse
import time
from datetime import datetime, timezone
from dateutil import parser as dateparser
from typing import List, Dict, Any, Optional

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def build_youtube(api_key: AIzaSyDg6RszNQ01SVAj5bLDi39sIcb4f8nDGoA):
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


def parse_iso_duration(iso_duration: str) -> int:
    """Return duration in seconds from ISO8601 format (e.g., PT5M12S)."""
    # Simple manual parse to avoid extra deps
    total = 0
    if not iso_duration or not iso_duration.startswith("P"):
        return total
    # Remove leading 'P'
    s = iso_duration[1:]
    time_part = ""
    date_part = ""
    if "T" in s:
        date_part, time_part = s.split("T", 1)
    else:
        date_part, time_part = s, ""

    # We only care about time components
    num = ""
    units = {"H": 3600, "M": 60, "S": 1}
    for ch in time_part:
        if ch.isdigit():
            num += ch
        else:
            if ch in units and num:
                total += int(num) * units[ch]
            num = ""
    return total


def safe_int(x):
    try:
        return int(x)
    except Exception:
        return 0


def videos_details(youtube, video_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetch snippet, statistics, contentDetails for a list of video IDs."""
    results = []
    for batch in chunked(video_ids, 50):
        resp = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(batch)
        ).execute()
        results.extend(resp.get("items", []))
        time.sleep(0.1)
    return results


def search_videos(youtube, query: str, max_results: int = 25, order: str = "relevance") -> pd.DataFrame:
    """Search videos by query and return a DataFrame with rich stats."""
    video_ids = []
    meta_rows = []
    page_token = None

    while len(video_ids) < max_results:
        try:
            resp = youtube.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=min(50, max_results - len(video_ids)),
                order=order,
                pageToken=page_token
            ).execute()
        except HttpError as e:
            print("HTTPError during search:", e)
            break

        for item in resp.get("items", []):
            vid = item["id"]["videoId"]
            video_ids.append(vid)
            meta_rows.append({
                "video_id": vid,
                "title": item["snippet"].get("title"),
                "channel_title": item["snippet"].get("channelTitle"),
                "channel_id": item["snippet"].get("channelId"),
                "published_at": item["snippet"].get("publishedAt"),
            })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    # Fetch details
    details = videos_details(youtube, video_ids)
    details_map = {d["id"]: d for d in details}

    rows = []
    for m in meta_rows:
        d = details_map.get(m["video_id"], {})
        snip = d.get("snippet", {})
        stats = d.get("statistics", {})
        cont = d.get("contentDetails", {})

        tags = snip.get("tags", [])
        published_at = snip.get("publishedAt", m.get("published_at"))
        dur_seconds = parse_iso_duration(cont.get("duration", ""))
        views = safe_int(stats.get("viewCount"))
        likes = safe_int(stats.get("likeCount"))
        comments = safe_int(stats.get("commentCount"))

        # Calculate age (days)
        age_days = None
        if published_at:
            try:
                dt = dateparser.parse(published_at)
                if not dt.tzinfo:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_days = (datetime.now(timezone.utc) - dt).days
            except Exception:
                age_days = None

        rows.append({
            "video_id": m["video_id"],
            "title": m["title"],
            "channel_title": m["channel_title"],
            "channel_id": m["channel_id"],
            "published_at": published_at,
            "age_days": age_days,
            "duration_sec": dur_seconds,
            "views": views,
            "likes": likes,
            "comments": comments,
            "tags": ", ".join(tags) if isinstance(tags, list) else ""
        })

    df = pd.DataFrame(rows)
    # Engagement proxy: likes + comments per 1k views
    if not df.empty:
        df["engagement_per_k"] = (df["likes"] + df["comments"]) / df["views"].replace(0, pd.NA) * 1000
    return df


def trending_videos(youtube, region: str = "US", category_id: Optional[str] = None, max_results: int = 50) -> pd.DataFrame:
    """Fetch most popular videos by region and optional category."""
    video_ids = []
    page_token = None

    while len(video_ids) < max_results:
        params = dict(
            part="id",
            chart="mostPopular",
            regionCode=region,
            maxResults=min(50, max_results - len(video_ids)),
        )
        if category_id:
            params["videoCategoryId"] = category_id

        try:
            resp = youtube.videos().list(**params).execute()
        except HttpError as e:
            print("HTTPError during trending:", e)
            break

        for item in resp.get("items", []):
            video_ids.append(item["id"])

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    details = videos_details(youtube, video_ids)
    rows = []
    for d in details:
        vid = d.get("id")
        snip = d.get("snippet", {})
        stats = d.get("statistics", {})
        cont = d.get("contentDetails", {})
        tags = snip.get("tags", [])
        published_at = snip.get("publishedAt")
        dur_seconds = parse_iso_duration(cont.get("duration", ""))

        views = safe_int(stats.get("viewCount"))
        likes = safe_int(stats.get("likeCount"))
        comments = safe_int(stats.get("commentCount"))

        rows.append({
            "video_id": vid,
            "title": snip.get("title"),
            "channel_title": snip.get("channelTitle"),
            "channel_id": snip.get("channelId"),
            "published_at": published_at,
            "duration_sec": dur_seconds,
            "views": views,
            "likes": likes,
            "comments": comments,
            "tags": ", ".join(tags) if isinstance(tags, list) else ""
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["engagement_per_k"] = (df["likes"] + df["comments"]) / df["views"].replace(0, pd.NA) * 1000
    return df


def channel_uploads_playlist_id(youtube, channel_id: str) -> Optional[str]:
    """Return the uploads playlist ID for a channel."""
    try:
        resp = youtube.channels().list(
            part="contentDetails,snippet,statistics",
            id=channel_id
        ).execute()
    except HttpError as e:
        print("HTTPError during channel lookup:", e)
        return None

    items = resp.get("items", [])
    if not items:
        return None
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def playlist_items_video_ids(youtube, playlist_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Return list of dicts with videoId and publishedAt from an uploads playlist."""
    results = []
    page_token = None
    while len(results) < max_results:
        try:
            resp = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=min(50, max_results - len(results)),
                pageToken=page_token
            ).execute()
        except HttpError as e:
            print("HTTPError during playlist fetch:", e)
            break

        for it in resp.get("items", []):
            sn = it.get("snippet", {})
            cd = it.get("contentDetails", {})
            vid = cd.get("videoId")
            if vid:
                results.append({
                    "video_id": vid,
                    "published_at": sn.get("publishedAt") or cd.get("videoPublishedAt")
                })
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results


def competitor_analysis(youtube, channel_id: str, max_results: int = 50) -> pd.DataFrame:
    """Fetch recent uploads from a channel with performance stats."""
    uploads = channel_uploads_playlist_id(youtube, channel_id)
    if not uploads:
        return pd.DataFrame()

    vids = playlist_items_video_ids(youtube, uploads, max_results=max_results)
    details = videos_details(youtube, [v["video_id"] for v in vids])
    detail_map = {d["id"]: d for d in details}

    rows = []
    for v in vids:
        d = detail_map.get(v["video_id"], {})
        snip = d.get("snippet", {})
        stats = d.get("statistics", {})
        cont = d.get("contentDetails", {})
        tags = snip.get("tags", [])
        dur_seconds = parse_iso_duration(cont.get("duration", ""))
        views = safe_int(stats.get("viewCount"))
        likes = safe_int(stats.get("likeCount"))
        comments = safe_int(stats.get("commentCount"))

        rows.append({
            "video_id": v["video_id"],
            "title": snip.get("title"),
            "published_at": snip.get("publishedAt") or v.get("published_at"),
            "duration_sec": dur_seconds,
            "views": views,
            "likes": likes,
            "comments": comments,
            "tags": ", ".join(tags) if isinstance(tags, list) else ""
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["engagement_per_k"] = (df["likes"] + df["comments"]) / df["views"].replace(0, pd.NA) * 1000
    return df


def dataframe_to_csv(df: pd.DataFrame, out_path: Optional[str]) -> Optional[str]:
    if out_path:
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        return out_path
    return None


def main():
    parser = argparse.ArgumentParser(description="YouTube Content Research Tool")
    parser.add_argument("--api-key", required=True, help="YouTube Data API v3 key")
    sub = parser.add_subparsers(dest="mode", required=True)

    # Search
    p_search = sub.add_parser("search", help="Keyword-based research")
    p_search.add_argument("--q", required=True, help="Search query/keyword")
    p_search.add_argument("--max", type=int, default=25, help="Max results (default 25)")
    p_search.add_argument("--order", default="viewCount", choices=["date", "rating", "relevance", "title", "viewCount", "videoCount"], help="Search order")
    p_search.add_argument("--out", help="CSV output path")

    # Trending
    p_tr = sub.add_parser("trending", help="Trending/most popular by region/category")
    p_tr.add_argument("--region", default="US", help="Region code, e.g., US, PK, IN, GB")
    p_tr.add_argument("--category", help="Optional videoCategoryId, e.g., 10 (Music), 20 (Gaming)")
    p_tr.add_argument("--max", type=int, default=50, help="Max results (default 50)")
    p_tr.add_argument("--out", help="CSV output path")

    # Competitor
    p_comp = sub.add_parser("competitor", help="Competitor analysis by channel ID")
    p_comp.add_argument("--channel-id", required=True, help="Channel ID like UC_x5XG1OV2P6uZZ5FSM9Ttw")
    p_comp.add_argument("--max", type=int, default=50, help="Max recent uploads to analyze")
    p_comp.add_argument("--out", help="CSV output path")

    args = parser.parse_args()
    yt = build_youtube(args.api_key)

    if args.mode == "search":
        df = search_videos(yt, args.q, args.max, args.order)
        path = dataframe_to_csv(df, args.out)
        print(df.head(10).to_string(index=False))
        if path:
            print(f"\nSaved to: {path}")

    elif args.mode == "trending":
        df = trending_videos(yt, args.region, args.category, args.max)
        path = dataframe_to_csv(df, args.out)
        print(df.head(10).to_string(index=False))
        if path:
            print(f"\nSaved to: {path}")

    elif args.mode == "competitor":
        df = competitor_analysis(yt, args.channel_id, args.max)
        path = dataframe_to_csv(df, args.out)
        print(df.head(10).to_string(index=False))
        if path:
            print(f"\nSaved to: {path}")


if __name__ == "__main__":
    main()
