import requests
import re
import random 

def fetch_urls(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def extract_image_urls(content):
    # Regular expression to find URLs ending with jpeg, jpg, or png
    img_url_pattern = re.compile(r'https?://\S+\.(?:jpeg|jpg)')
    return img_url_pattern.findall(content)

def get_images(url):
    content = fetch_urls(url)
    list_urls = extract_image_urls(content)
    if list_urls:
        return random.choice(list_urls)
    else:
        return ""