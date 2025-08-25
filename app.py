import streamlit as st
from googleapiclient.discovery import build

# --- YouTube API Call Helper ---
def get_youtube(api_key):
    return build("youtube", "v3", developerKey=api_key)


# --- Search Function ---
def search_videos(youtube, query, max_results=10):
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results
    )
    response = request.execute()
    return response.get("items", [])


# --- Competitor Channel Analysis ---
def get_channel_stats(youtube, channel_id):
    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )
    response = request.execute()
    return response.get("items", [])


# --- Trending Videos ---
def get_trending_videos(youtube, region="US", max_results=10):
    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=region,
        maxResults=max_results
    )
    response = request.execute()
    return response.get("items", [])


# --- Streamlit App ---
def main():
    st.title("📊 YouTube Research Tool")

    st.sidebar.header("⚙️ Settings")
    api_key = st.sidebar.text_input("Enter YouTube API Key", type="password")

    if not api_key:
        st.warning("⚠️ Pehle apna YouTube API Key enter karo")
        return

    youtube = get_youtube(api_key)

    mode = st.sidebar.radio("Select Mode", ["Search", "Trending", "Competitor Analysis"])

    if mode == "Search":
        st.subheader("🔍 YouTube Video Search")
        query = st.text_input("Search Term")
        if st.button("Search"):
            results = search_videos(youtube, query)
            for video in results:
                title = video["snippet"]["title"]
                channel = video["snippet"]["channelTitle"]
                video_id = video["id"]["videoId"]
                url = f"https://youtube.com/watch?v={video_id}"
                st.write(f"**{title}** by *{channel}*")
                st.video(url)

    elif mode == "Trending":
        st.subheader("🔥 Trending Videos")
        region = st.text_input("Enter Region Code (default = US)", value="US")
        if st.button("Get Trending"):
            results = get_trending_videos(youtube, region)
            for video in results:
                title = video["snippet"]["title"]
                channel = video["snippet"]["channelTitle"]
                video_id = video["id"]
                url = f"https://youtube.com/watch?v={video_id}"
                st.write(f"**{title}** by *{channel}*")
                st.video(url)

    elif mode == "Competitor Analysis":
        st.subheader("🏆 Competitor Channel Analysis")
        channel_id = st.text_input("Enter Channel ID")
        if st.button("Analyze"):
            results = get_channel_stats(youtube, channel_id)
            if results:
                data = results[0]
                title = data["snippet"]["title"]
                subs = data["statistics"].get("subscriberCount", "N/A")
                views = data["statistics"].get("viewCount", "N/A")
                videos = data["statistics"].get("videoCount", "N/A")
                st.write(f"📺 **{title}**")
                st.write(f"👥 Subscribers: {subs}")
                st.write(f"👀 Views: {views}")
                st.write(f"🎬 Total Videos: {videos}")
            else:
                st.error("Channel not found!")


if __name__ == "__main__":
    main()
