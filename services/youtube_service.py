import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from typing import Dict, List, Any
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("Google API key not found in environment variables")
            raise ValueError("Google API key is required for YouTube service")

        try:
            self.youtube_client = build('youtube', 'v3', developerKey=api_key)
            logger.info("YouTube API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API client: {e}")
            self.youtube_client = None
            raise

    def search_videos(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        try:
            if not self.youtube_client:
                logger.error("YouTube client not initialized")
                return []
                
            logger.info(f"Searching YouTube for videos: {query}")
            
            search_response = self.youtube_client.search().list(
                q=query,
                part='id,snippet',
                type='video',
                maxResults=max_results,
                order='relevance',
                regionCode='ID', 
                relevanceLanguage='id' 
            ).execute()
            
            videos = []
            for search_result in search_response.get('items', []):
                video_data = {
                    'video_id': search_result['id']['videoId'],
                    'title': search_result['snippet']['title'],
                    'description': search_result['snippet']['description'],
                    'channel_title': search_result['snippet']['channelTitle'],
                    'published_at': search_result['snippet']['publishedAt'],
                    'thumbnail_url': search_result['snippet']['thumbnails']['high']['url'],
                    'video_url': f"https://www.youtube.com/watch?v={search_result['id']['videoId']}"
                }
                videos.append(video_data)
                logger.info(f"Found video: {video_data['title']}")
            
            logger.info(f"Found {len(videos)} videos for query: {query}")
            return videos
            
        except Exception as e:
            logger.error(f"Error searching YouTube videos: {e}")
            return []

    def is_client_available(self) -> bool:
        return self.youtube_client is not None