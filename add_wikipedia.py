import wikipediaapi

def get_wiki_summary(keywords):
    """Get Wikipedia summary"""
    wiki = wikipediaapi.Wikipedia(
        user_agent='CuriosityApp/1.0',
        language='en'
    )
    
    # Get main topic
    topic = keywords.split(',')[0].strip()
    page = wiki.page(topic)
    
    if page.exists():
        # Get first 2 sentences
        summary = '. '.join(page.summary.split('.')[:2]) + '.'
        return {
            'type': 'wikipedia',
            'title': page.title,
            'summary': summary,
            'url': page.fullurl
        }
    return None

if __name__ == "__main__":
    result = get_wiki_summary("Samoyed, dog breed")
    if result:
        print(f"\n📚 {result['title']}")
        print(f"{result['summary']}")
        print(f"→ {result['url']}\n")
