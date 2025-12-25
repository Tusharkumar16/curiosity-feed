import os
import openai
import base64
from googleapiclient.discovery import build
import wikipediaapi
import time
import sys

# Your API keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY') 

# Initialize clients
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
wiki = wikipediaapi.Wikipedia(user_agent='CuriosityApp/1.0', language='en')

# Known problematic Wikipedia disambiguations
WIKI_SKIP_PATTERNS = {
    'soccer': ['wishbone', 'actor', 'dog', 'terrier'],
    'python': ['monty python', 'comedy'],
    'java': ['island', 'coffee'],
    'apple': ['fruit', 'tree'],
}

# Content safety keywords - block these
UNSAFE_KEYWORDS = [
    'jailbreak', 'crack', 'pirate', 'torrent', 'hack',
    'exploit', 'bypass', 'unlock', 'free download', 'keygen',
    'serial key', 'activation', 'nulled', 'leaked'
]

def is_safe_content(title, description=""):
    """Check if content is safe and appropriate"""
    text = (title + " " + description).lower()
    
    # Block unsafe keywords
    for keyword in UNSAFE_KEYWORDS:
        if keyword in text:
            return False
    
    return True

def analyze_image(image_path):
    """Step 1: Understand EVERYTHING the user might be curious about"""
    print("🔍 Analyzing image...", end=" ", flush=True)
    
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                },
                {
                    "type": "text",
                    "text": """Analyze EVERYTHING in this image and identify multiple distinct topics someone might be curious about:

1. Main Subject: What/who is the primary focus?
2. Setting/Location: Where might this be? Any recognizable places?
3. Context: What might this be from? (movie, TV show, music video, event, advertisement, etc.)
4. People: Any recognizable people, celebrities, or characters?
5. Text/Logos: Any visible text, brand names, or logos?
6. Style/Aesthetic: Notable visual characteristics, art style, or cinematography?
7. Objects/Details: Other interesting elements worth exploring?

Return 5-8 specific, searchable keywords covering DIFFERENT aspects of the image, comma separated.

IMPORTANT: 
- Focus on proper nouns (names, places, titles, brands) when identifiable
- Include context clues (e.g., "movie scene", "concert footage", "music video")
- Be specific, not generic (e.g., "Times Square New York" not just "city")
- If you see multiple interesting elements, include them all

Examples:
- Movie scene → "Actor Name, Movie Title, filming location, director name, cinematography style"
- Music video → "Artist name, song title, music video, dance choreography, visual effects"
- Food → "Dish name, cuisine type, restaurant name, plating technique, culinary style"
- Architecture → "Building name, architectural style, architect name, city location, historical period"

Just the keywords, comma separated, nothing else."""
                }
            ]
        }],
        max_tokens=200
    )
    
    keywords = response.choices[0].message.content.strip()
    print("Done! ✓")
    return keywords

def get_wikipedia_content(keywords):
    """Get Wikipedia summary - SMART SEARCH with context awareness"""
    print("📚 Getting Wikipedia...", end=" ", flush=True)
    
    # Split keywords
    keyword_list = [k.strip() for k in keywords.split(',')]
    main_topic = keyword_list[0]
    first_word = main_topic.split()[0]
    
    # Build smart search variations based on likely categories
    variations = [
        main_topic,  # Try exact match first
        first_word + " (sport)",
        first_word + " sport",
        first_word + " (game)",
        first_word + " (association football)",
        first_word + " (dog)",
        first_word + " (breed)",
        first_word + " dog",
        first_word + " (car)",
        first_word + " (automobile)",
        first_word + " (technology)",
        first_word + " (company)",
        first_word,  # Last resort: just the word
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    variations = [x for x in variations if not (x in seen or seen.add(x))]
    
    for variation in variations:
        page = wiki.page(variation)
        
        if not page.exists():
            continue
            
        summary_lower = page.summary.lower()
        
        # Skip disambiguation pages
        if 'may refer to' in summary_lower or 'disambiguation' in summary_lower:
            continue

        # Check for known problematic patterns (this handles all edge cases)
        if first_word.lower() in WIKI_SKIP_PATTERNS:
            skip_words = WIKI_SKIP_PATTERNS[first_word.lower()]
            if any(skip_word in summary_lower for skip_word in skip_words):
                continue
        
        # Get summary
        summary = '. '.join(page.summary.split('.')[:3]) + '.'
        if len(summary) > 400:
            summary = summary[:400] + '...'
        
        print("Done! ✓")
        return {
            'title': page.title,
            'summary': summary,
            'url': page.fullurl
        }
    
    print("Not found")
    return None

def get_youtube_videos(keywords):
    """Get YouTube videos - FILTERED FOR SAFETY"""
    print("🎥 Finding videos...", end=" ", flush=True)
    
    request = youtube.search().list(
        part="snippet",
        q=keywords,
        type="video",
        videoDuration="short",
        maxResults=10,  # Get more, then filter
        order="relevance",
        relevanceLanguage="en",
        safeSearch="strict"  # YouTube's built-in safety
    )
    
    response = request.execute()
    
    videos = []
    for item in response['items']:
        title = item['snippet']['title']
        channel = item['snippet']['channelTitle']
        
        # Filter out unsafe content
        if is_safe_content(title, item['snippet']['description']):
            videos.append({
                'title': title,
                'channel': channel,
                'url': f"https://youtube.com/watch?v={item['id']['videoId']}"
            })
        
        # Stop once we have 5 safe videos
        if len(videos) >= 5:
            break
    
    print("Done! ✓")
    return videos

def curiosity_flow(image_path):
    """The complete magic: Image → Understanding → Multi-source Content"""
    
    print("\n" + "="*70)
    print("                  ✨ CURIOSITY FEED ✨")
    print("="*70 + "\n")
    
    start_time = time.time()
    
    # Step 1: Understand the image
    keywords = analyze_image(image_path)
    print(f"   💡 You're curious about: {keywords}\n")
    
    # Step 2: Get Wikipedia
    wiki_content = get_wikipedia_content(keywords)
    
    # Step 3: Get YouTube videos
    videos = get_youtube_videos(keywords)
    
    print("\n" + "="*70)
    
    # Step 4: Display the feed
    if wiki_content:
        print("\n📚 QUICK FACTS\n")
        print(f"   {wiki_content['title']}")
        print(f"   {wiki_content['summary']}")
        print(f"   → {wiki_content['url']}\n")
        print("-"*70)
    
    print("\n🎥 WATCH & LEARN\n")
    for i, v in enumerate(videos, 1):
        print(f"   {i}. {v['title']}")
        print(f"      by {v['channel']}")
        print(f"      → {v['url']}\n")
    
    print("="*70)
    elapsed = time.time() - start_time
    print(f"⚡ Loaded in {elapsed:.2f} seconds")
    print("="*70 + "\n")

if __name__ == "__main__":
    import sys
    image_file = sys.argv[1] if len(sys.argv) > 1 else "Dog.jpg"
    curiosity_flow(image_file)
