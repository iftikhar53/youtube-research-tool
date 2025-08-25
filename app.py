import streamlit as st
st.warning("Channel not found. Please provide a valid channel URL/ID/handle.")
return pd.DataFrame()
# Get uploads playlist
ch = youtube.channels().list(part="contentDetails,snippet,statistics", id=ch_id).execute()
items = ch.get("items", [])
if not items:
st.warning("Channel not found.")
return pd.DataFrame()
uploads = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


# Collect videos from uploads playlist
vids: List[str] = []
page_token = None
while len(vids) < max_results:
pl = youtube.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=min(50, max_results - len(vids)), pageToken=page_token).execute()
for it in pl.get("items", []):
vid = it.get("contentDetails", {}).get("videoId")
if vid:
vids.append(vid)
page_token = pl.get("nextPageToken")
if not page_token:
break


details = fetch_video_details(youtube, vids)
return df_from_details(details)




# ---------- UI ----------
st.title("📊 YouTube Content Research Tool")
st.caption("Keyword research • Trending by region/category • Competitor analysis • CSV export")


with st.sidebar:
st.header("Settings")
api_key = st.text_input("YouTube API Key", type="password")
mode = st.radio("Mode", ["Keyword Research", "Trending (Region/Category)", "Competitor Analysis"], index=0)


if not api_key:
st.info("Enter your YouTube API key in the sidebar to begin.")
st.stop()


try:
yt = build_youtube(api_key)
except Exception as e:
st.error(f"Failed to initialize YouTube API: {e}")
st.stop()


try:
if mode == "Keyword Research":
col1, col2, col3 = st.columns([3,1,1])
with col1:
q = st.text_input("Keyword / search query", "toyota supra")
with col2:
max_r = st.slider("Max results", 5, 100, 25, step=5)
with col3:
order = st.selectbox("Order", ["viewCount", "relevance", "date", "rating", "title", "videoCount"], index=0)


if st.button("Search", type="primary"):
df = search_videos(yt, q, max_r, order)
if df.empty:
st.warning("No results.")
else:
st.success(f"Found {len(df)} videos")
st.dataframe(df, use_container_width=True, hide_index=True)
st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8-sig"), file_name="keyword_results.csv", mime="text/csv")


elif mode == "Trending (Region/Category)":
col1, col2, col3 = st.columns([1,1,1])
with col1:
region = st.text_input("Region code (e.g., PK, IN, US, GB)", "PK")
with col2:
category_name = st.selectbox("Category", list(CATEGORY_MAP.keys()), index=0)
category_id = CATEGORY_MAP[category_name]
with col3:
max_r = st.slider("Max results", 10, 100, 50, step=10)


if st.button("Fetch Trending", type="primary"):
df = trending_videos(yt, region, category_id, max_r)
if df.empty:
st.warning("No results.")
else:
st.success(f"Fetched {len(df)} trending videos")
st.dataframe(df, use_container_width=True, hide_index=True)
st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8-sig"), file_name="trending_results.csv", mime="text/csv")
