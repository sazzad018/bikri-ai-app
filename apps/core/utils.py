from django.http import Http404
import logging, json, textwrap
from django.contrib import messages
import mimetypes, threading
from django.utils.safestring import mark_safe
from django.utils.html import escape
from google import genai
import markdown
from bs4 import BeautifulSoup
import re
import dirtyjson
from django import db


logger = logging.getLogger(__name__)

def try_except(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(str(e), exc_info=True)
            return str(e)
    return wrapper
      
def guess_file_type(url):
    options = ['image', 'video', 'audio', 'file']
    guessed = mimetypes.guess_type(url)[0]
    if guessed:
        for option in options:
            if option in guessed:
                return option
    return 'file'

def run_in_thread(func, *args, **kwargs):
    def wrapper(*w_args, **w_kwargs):
        try:
            func(*w_args, **w_kwargs)
        finally:
            db.connections.close_all()

    thread = threading.Thread(target=wrapper, args=args, kwargs=kwargs)
    thread.start()
    return thread


def parse_ai_response(response: str):
    response_json = {}
    text = response.strip()

    try:
        parsed = dirtyjson.loads(text, search_for_first_object=True)
        response_json = dict(parsed)

        match = re.search(r'[{\[]', text)
        if match:
            preamble = text[:match.start()].strip()
            if preamble.endswith("```json"):
                preamble = preamble[:-7].strip()
            elif preamble.endswith("```"):
                preamble = preamble[:-3].strip()
            text = preamble
        else:
            text = ""

    except dirtyjson.Error:
        response_json = {}

    return text, response_json

def image_html(url, alt=None, size=28):
    if not url:
        url = f"https://placehold.co/{size}/f0f0f0/666?text={alt or 'No+Image'}"
    return mark_safe(f'<img src="{url}" class="rounded-default aspect-square" alt="{alt or ""}" width="{size}" height="{size}">')

def profile_html(image_url, name, size=28, href=None):
    if not image_url:
        image_url = f"https://placehold.co/{size}/f0f0f0/666?text={name[0].upper()}"
    name = textwrap.shorten(escape(name), width=32, placeholder="...")
    content_html = mark_safe(f'<div class="flex gap-2 items-center p-2"><img src="{image_url}" width="{size}" height="{size}" class="rounded-default" /> <span class="font-medium whitespace-nowrap">{name}</span></div>')
    if href:
        content_html = mark_safe(f'<a href="{href}">{content_html}</a>')
    return content_html

def clean_markdown(md_text):
    """
    Converts Markdown to plain text, text-based lists.
    """
    # 1. Convert to HTML to handle nested markdown properly
    html = markdown.markdown(md_text, extensions=['extra', 'sane_lists'])
    soup = BeautifulSoup(html, 'html.parser')
    
    # 2. Transform headers into bold text
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        tag.name = 'strong'

    # 3. Handle Lists: Convert HTML lists to plain text hyphens
    for li in soup.find_all('li'):
        li.insert(0, "- ") # Prepend text hyphen
        li.unwrap()        # Remove <li> tag
    for list_tag in soup.find_all(['ul', 'ol']):
        list_tag.unwrap()  # Remove <ul> / <ol> tags

    # 4. Handle Paragraphs: Add line breaks, remove <p> tags
    for p in soup.find_all('p'):
        p.insert_after('\n')
        p.unwrap()

    # 5. Strip all remaining HTML tags except formatting targets
    for tag in soup.find_all(True):
        if tag.name not in ['strong', 'em', 'u']:
            tag.unwrap()

    # 6. Decode back to string
    text = soup.decode_contents()
    
    # 7. Regex mapping to your specific single-character rules
    text = re.sub(r'<strong>(.*?)</strong>', r'\1', text) # Bold to text
    text = re.sub(r'<em>(.*?)</em>', r'\1', text)         # Italic to text
    text = re.sub(r'<u>(.*?)</u>', r'\1', text)           # Underline to text
    
    # Clean up excessive newlines caused by unwrapping
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


from functools import lru_cache

@lru_cache(maxsize=1)
def _get_genai_client():
    return genai.Client()

def count_tokens(text: str) -> int:
    try:
        client = _get_genai_client()
        r = client.models.count_tokens(model="gemini-3.1-flash-lite-preview", contents=text)
        return r.total_tokens
    except Exception as e:
        logger.error(f"Failed to count tokens: {e}", exc_info=True)
        # Return estimated token count as fallback: roughly 4 chars per token
        return len(text) // 4
