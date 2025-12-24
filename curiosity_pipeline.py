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
    """Step 1: Understand what the user is curious about - IMPROVED CONTEXT"""
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
                    "text": """Look at this image carefully. What is the PRIMARY subject or activity that someone would want to learn about?

IMPORTANT: Focus on the main activity/concept, not just visible objects.
- If you see soccer shoes and a ball → "soccer sport, football tactics" (not just "soccer cleats")
- If you see guitar strings → "guitar playing, music" (not just "guitar strings")
- If you see cooking tools → "cooking techniques, recipes" (not just "kitchen utensils")

Be specific and add educational context:
- "iPhone smartphone, iOS features, mobile technology" 
- "soccer sport, football tactics, athletic training"
- "burger recipe, American cuisine, grilling techniques"

Return 3-5 educational keywords with context, comma separated.
Focus on what someone would want to LEARN, not just identify.

Just the keywords, nothing else."""
                }
            ]
        }],
        max_tokens=150
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
