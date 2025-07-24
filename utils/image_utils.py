import base64

import base64
import requests

def read_url_as_base64(image_url: str) -> str:
    response = requests.get(image_url)
    response.raise_for_status()
    return base64.b64encode(response.content).decode("utf-8")
