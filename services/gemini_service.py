import base64
import os
import google.generativeai as genai
from utils.image_utils import read_image_as_base64

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))