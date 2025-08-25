import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# Streamlit app
st.set_page_config(page_title="YouTube Research Tool", layout="wide")

st.title("📊 YouTube Research Tool")

# Sidebar inputs
api_key = st.sidebar.text_input("🔑 Enter YouTube API Key", type="password")
mode = st.sidebar.selectbox("Select Mode", ["search", "trending", "competitor"])

query = None
channel_id = None
if mode == "search":
    query = st.sidebar.text_input("Enter Search Keyword")
elif mode == "competitor":
    channel_id = st.sidebar.text_input("Enter Competitor Channel ID")

# Function to connect YouTube API
def get_youtube_service(api_key):
    return build("youtube", "v3", developerKey=api_key)

# Run logic
if st.sidebar.button("Run Tool"):
    if not api_key:
        st.error("Please enter your YouTube API Key")
    else:
        youtube = get_youtube_service(api_key)

        if mode == "search" and query:
            request = youtube.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=10
            )
            response = request.execute()
            results = []
            for item in response["items"]:
                results.append({
                    "Title": item["snippet"]["title"],
                    "Channel": item["snippet"]["channelTitle"],
                    "Published": item["snippet"]["publishedAt"],
                    "Video ID": item["id"]["videoId"]
                })
            df = pd.DataFrame(results)
            st.dataframe(df)

        elif mode == "competitor" and channel_id:
            request = youtube.search().list(
                channelId=channel_id,
                part="snippet",
                type="video",
                order="date",
                maxResults=10
            )
            response = request.execute()
            results = []
            for item in response["items"]:
                results.append({
                    "Title": item["snippet"]["title"],
                    "Published": item["snippet"]["publishedAt"],
                    "Video ID": item["id"]["videoId"]
                })
            df = pd.DataFrame(results)
            st.dataframe(df)

        elif mode == "trending":
            st.info("⚡ Trending API ka direct access nahi hai free YouTube API me. Iske liye custom logic banana padega.")

        else:
            st.warning("Please provide required inputs.")
