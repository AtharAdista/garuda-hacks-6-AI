import base64
import requests

def read_url_as_base64(image_url: str) -> str:
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    response = requests.get(image_url, headers=headers)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")
