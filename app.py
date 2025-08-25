import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# ===============================
# YouTube API Helper Functions
# ===============================
def youtube_search(api_key, query, max_results=20):
    youtube = build("youtube", "v3", developerKey=api_key)
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        videos.append({
            "Video Title": item["snippet"]["title"],
            "Channel": item["snippet"]["channelTitle"],
            "Published At": item["snippet"]["publishedAt"],
            "Video ID": item["id"]["videoId"],
            "Video URL": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        })
    return pd.DataFrame(videos)


def youtube_trending(api_key, region="US", max_results=20):
    youtube = build("youtube", "v3", developerKey=api_key)
    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=region,
        maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        videos.append({
            "Video Title": item["snippet"]["title"],
            "Channel": item["snippet"]["channelTitle"],
            "Published At": item["snippet"]["publishedAt"],
            "Views": item["statistics"].get("viewCount", "N/A"),
            "Likes": item["statistics"].get("likeCount", "N/A"),
            "Video URL": f"https://www.youtube.com/watch?v={item['id']}"
        })
    return pd.DataFrame(videos)


def youtube_competitor(api_key, channel_id, max_results=20):
    youtube = build("youtube", "v3", developerKey=api_key)
    request = youtube.search().list(
        channelId=channel_id,
        part="snippet",
        order="date",
        type="video",
        maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        videos.append({
            "Video Title": item["snippet"]["title"],
            "Published At": item["snippet"]["publishedAt"],
            "Video ID": item["id"]["videoId"],
            "Video URL": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        })
    return pd.DataFrame(videos)


# ===============================
# Streamlit UI
# ===============================
st.set_page_config(page_title="YouTube Research Tool", layout="wide")
st.title("📊 YouTube Automation Research Tool")

# API Key input
api_key = st.text_input("🔑 Enter your YouTube API Key:", type="password")

# Mode selection
mode = st.selectbox("Select Mode:", ["Keyword Research", "Trending", "Competitor Analysis"])

if api_key:
    if mode == "Keyword Research":
        query = st.text_input("Enter a search keyword:")
        if st.button("Search"):
            df = youtube_search(api_key, query)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, "keyword_research.csv", "text/csv")

    elif mode == "Trending":
        region = st.text_input("Enter region code (default US):", value="US")
        if st.button("Get Trending"):
            df = youtube_trending(api_key, region)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, "trending_videos.csv", "text/csv")

    elif mode == "Competitor Analysis":
        channel_id = st.text_input("Enter Competitor Channel ID:")
        if st.button("Analyze"):
            df = youtube_competitor(api_key, channel_id)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, "competitor_analysis.csv", "text/csv")
else:
    st.warning("⚠️ Please enter your API key to continue.")
