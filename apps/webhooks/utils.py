import requests
import base64
import mimetypes
import logging

logger = logging.getLogger(__name__)

def url_to_data_url(url):
    """
    Fetches an image from a URL and converts it to a base64 Data URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status() 
        mime_type = response.headers.get('content-type', 'image/png')
        encoded_string = base64.b64encode(response.content).decode('utf-8')
        data_url = f"data:{mime_type};base64,{encoded_string}"
        return data_url
    except Exception as e:
        logger.exception(f"Error fetching image from URL: {url}")
        return None
