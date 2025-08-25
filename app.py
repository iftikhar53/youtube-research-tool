import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from dateutil import parser as dateparser
from datetime import datetime, timezone

# Function: Build YouTube API client
def build_youtube(api_key):
    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)

# Helper: Safe int
def safe_int(x):
    try:
        return int(x)
    except:
        return 0

# Fetch videos by keyword
def search_videos(youtube, query, max_results=10):
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        order="viewCount",
        maxResults=max_results
    )
    response = request.execute()

    video_data = []
    for item in response["items"]:
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]

        stats_req = youtube.videos().list(part="statistics", id=video_id)
        stats_res = stats_req.execute()
        stats = stats_res["items"][0]["statistics"]

        views = safe_int(stats.get("viewCount"))
        likes = safe_int(stats.get("likeCount"))
        comments = safe_int(stats.get("commentCount"))

        video_data.append({
            "Video ID": video_id,
            "Title": title,
            "Channel": channel,
            "Views": views,
            "Likes": likes,
            "Comments": comments,
            "URL": f"https://www.youtube.com/watch?v={video_id}"
        })

    return pd.DataFrame(video_data)

# ----------------- Streamlit UI -------------------
st.title("📊 YouTube Content Research Tool")

api_key = st.text_input("Enter your YouTube API Key", type="password")

menu = st.sidebar.radio("Choose Option", ["Keyword Research", "Trending (Region)", "Competitor Analysis"])

if api_key:
    youtube = build_youtube(api_key)

    if menu == "Keyword Research":
        query = st.text_input("Enter a keyword", "toyota supra")
        max_results = st.slider("Max Results", 5, 50, 10)
        if st.button("Search"):
            df = search_videos(youtube, query, max_results)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "results.csv", "text/csv")
