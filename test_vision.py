import openai
import base64
import os

# Put your OpenAI API key here
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def test_image_recognition(image_path):
    """Test if GPT can understand what's in an image"""
    
    # Read and encode the image
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
    
    # Determine image type
    extension = image_path.split('.')[-1].lower()
    mime_type = f"image/{extension}" if extension in ['jpeg', 'jpg', 'png', 'gif', 'webp'] else "image/jpeg"
    
    # Ask GPT what it sees
    response = client.chat.completions.create(
        model="gpt-4o",  # GPT-4 with vision
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": """Look at this image. What would someone be curious about here?
                        
                        Return ONLY 3-5 keywords that capture the main topic, separated by commas.
                        
                        Examples:
                        - "egyptian mummy, ancient egypt, mummification"
                        - "golden retriever, dog training, puppy"
                        - "guitar technique, fingerpicking, acoustic"
                        
                        Just the keywords, nothing else."""
                    }
                ]
            }
        ],
        max_tokens=100
    )
    
    # Extract the keywords
    keywords = response.choices[0].message.content.strip()
    
    print(f"🔍 Detected topics: {keywords}")
    return keywords

if __name__ == "__main__":
    # Test with an image
    test_image_recognition("test.jpg")
