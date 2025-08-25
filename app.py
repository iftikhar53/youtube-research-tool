import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# Streamlit App Title
st.set_page_config(page_title="YouTube Research Tool", layout="wide")
st.title("📊 YouTube Research Tool")

# Sidebar for API Key and Mode Selection
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("🔑 Enter YouTube API Key", type="password")
mode = st.sidebar.selectbox("Select Mode", ["Search", "Trending", "Competitor Analysis"])

# Helper function to connect with YouTube API
def get_youtube(api_key):
    return build("youtube", "v3", developerKey=api_key)

# Search Function
def search_videos(youtube, query, max_results=10):
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results
    )
    response = request.execute()
    results = []
    for item in response.get("items", []):
        results.append({
            "Title": item["snippet"]["title"],
            "Channel": item["snippet"]["channelTitle"],
            "Published At": item["snippet"]["publishedAt"],
            "Video ID": item["id"]["videoId"],
            "Video Link": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        })
    return pd.DataFrame(results)

# Competitor Function
def competitor_analysis(youtube, channel_id, max_results=10):
    request = youtube.search().list(
        channelId=channel_id,
        part="snippet",
        order="date",
        type="video",
        maxResults=max_results
    )
    response = request.execute()
    results = []
    for item in response.get("items", []):
        results.append({
            "Title": item["snippet"]["title"],
            "Published At": item["snippet"]["publishedAt"],
            "Video ID": item["id"]["videoId"],
            "Video Link": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        })
    return pd.DataFrame(results)

# Main App Logic
if api_key:
    youtube = get_youtube(api_key)

    if mode == "Search":
        query = st.text_input("🔍 Enter a search query")
        if st.button("Search") and query:
            df = search_videos(youtube, query)
            st.dataframe(df, use_container_width=True)

    elif mode == "Trending":
        st.info("⚡ Trending videos feature will be added soon (region-based).")

    elif mode == "Competitor Analysis":
        channel_id = st.text_input("🏆 Enter Competitor Channel ID")
        if st.button("Analyze") and channel_id:
            df = competitor_analysis(youtube, channel_id)
            st.dataframe(df, use_container_width=True)

else:
    st.warning("Please enter your YouTube API key in the sidebar to continue.")
