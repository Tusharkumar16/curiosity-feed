from googleapiclient.discovery import build

# Put your YouTube API key here
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_curiosity_feed(keywords):
    """Get short, relevant YouTube videos"""
    
    print(f"🔎 Searching YouTube for: {keywords}\n")
    
    request = youtube.search().list(
        part="snippet",
        q=keywords,
        type="video",
        videoDuration="short",  # under 4 minutes
        maxResults=5,
        order="relevance",
        relevanceLanguage="en"
    )
    
    response = request.execute()
    
    videos = []
    for item in response['items']:
        videos.append({
            'title': item['snippet']['title'],
            'channel': item['snippet']['channelTitle'],
            'url': f"https://youtube.com/watch?v={item['id']['videoId']}"
        })
    
    return videos

if __name__ == "__main__":
    # Use the keywords GPT found
    keywords = "Egyptian mummy, ancient Egypt, mummification"
    videos = get_curiosity_feed(keywords)
    
    print("🎯 Your Curiosity Feed:\n")
    for i, v in enumerate(videos, 1):
        print(f"{i}. {v['title']}")
        print(f"   by {v['channel']}")
        print(f"   → {v['url']}\n")
