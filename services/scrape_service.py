from .base_langchain import BaseLangChainService
import logging
from typing import Dict, List, Any, Optional, Union
import random
from langchain.schema import HumanMessage
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class ScrapeService(BaseLangChainService):
    def __init__(self):
        super().__init__(model_name="models/gemini-2.0-flash")
        logger.info("ScrapeService initialized")
        
        self.download_dir = Path("downloads/cultural_images")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.provinces = [
            "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Kepulauan Riau",
            "Jambi", "Sumatera Selatan", "Kepulauan Bangka Belitung", "Bengkulu", "Lampung",
            "DKI Jakarta", "Jawa Barat", "Banten", "Jawa Tengah", "DI Yogyakarta",
            "Jawa Timur", "Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur",
            "Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Selatan", "Kalimantan Timur",
            "Kalimantan Utara", "Sulawesi Utara", "Gorontalo", "Sulawesi Tengah",
            "Sulawesi Selatan", "Sulawesi Barat", "Sulawesi Tenggara", "Maluku",
            "Maluku Utara", "Papua"
        ]
        
        self.cultural_categories = [
            "traditional dance", "traditional music", "traditional clothing",
            "traditional ceremony", "traditional food", "traditional house",
            "traditional art", "traditional crafts", "cultural festival",
            "wayang puppet", "batik pattern",
            "traditional musical instrument",
        ]
        self.video_cultural_categories = [
            "traditional dance", "traditional music", "wayang puppet",
            "cultural festival", "traditional ceremony"
        ]
        
        self.media_probabilities = {
            "image": 0.6,
            "video": 0.4
        }

    def generate_cultural_query(self, province: str, cultural_category: str) -> str:
        
        prompt = f"""Generate a specific search query for finding {cultural_category} from {province} province in Indonesia.
        
        The query should be:
        - Concise (2-4 words)
        - Include specific cultural element names when possible
        - Use Indonesian terms when appropriate
        - Focus on authentic traditional content
        
        Examples:
        - For "traditional dance" from "Jawa Barat": "tari jaipong"
        - For "traditional music" from "Jawa Tengah": "gamelan jawa"
        - For "traditional clothing" from "Bali": "pakaian adat bali"
        
        Return ONLY the search query, nothing else."""
        
        try:
            response = self.text_llm.invoke([HumanMessage(content=prompt)])
            query = response.content.strip().replace('"', '').replace("'", "")
            logger.info(f"Generated query for {province} {cultural_category}: {query}")
            return query
        except Exception as e:
            logger.error(f"Error generating query: {e}")
            return f"{cultural_category} {province}".replace("traditional ", "")

    def choose_media_type(self) -> str:
        rand_val = random.random()
        if rand_val < self.media_probabilities["image"]:
            return "image"
        else:
            return "video"

    def search_youtube_videos(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
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

    def validate_video_cultural_accuracy(self, video_data: Dict[str, Any], province: str, cultural_category: str, query: str) -> float:
        try:
            validation_prompt = f"""Analyze this video information to determine if it accurately represents {cultural_category} from {province} province in Indonesia.

                Video details:
                - Title: {video_data['title']}
                - Description: {video_data['description'][:500]}...
                - Channel: {video_data['channel_title']}

                Search query used: "{query}"
                Target province: {province}
                Cultural category: {cultural_category}

                Please evaluate:
                1. Does the video appear to show authentic Indonesian cultural content?
                2. Is it specifically related to {province} province?
                3. Does it match the cultural category "{cultural_category}"?
                4. Is the content quality and authenticity appropriate?

                Return ONLY a confidence score between 0.0 and 1.0 as a number (e.g., 0.85)."""
            
            response = self.text_llm.invoke([HumanMessage(content=validation_prompt)])
            response_text = response.content.strip()
            
            import re
            score_match = re.search(r'(\d+\.?\d*)', response_text)
            if score_match:
                confidence_score = float(score_match.group(1))
                if confidence_score > 1.0:
                    confidence_score = 0
                confidence_score = max(0.0, min(1.0, confidence_score))
            else:
                logger.warning(f"Could not extract confidence score from: {response_text}")
                confidence_score = 0.0
            
            logger.info(f"AI validation confidence for video {video_data['title']}: {confidence_score}")
            return confidence_score
                    
        except Exception as e:
            logger.error(f"Error in video cultural validation: {e}")
            title_desc = f"{video_data.get('title', '')} {video_data.get('description', '')}".lower()
            specific_terms = ['tari', 'dance', 'musik', 'music', 'pakaian', 'clothing', 'rumah', 'house', 'batik', 'wayang', 'indonesia', 'budaya', 'culture']
            matches = sum(1 for term in specific_terms if term in title_desc)
            confidence_score = min(0.9, max(0.3, matches * 0.15))
            logger.info(f"Fallback video validation confidence: {confidence_score}")
            return confidence_score

    def search_wikimedia_commons(self, query: str, max_results: int = 5) -> List[str]:
        
        try:
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://commons.wikimedia.org/w/index.php?search={encoded_query}"
            
            logger.info(f"Searching Wikimedia Commons: {search_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            file_urls = []
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            
            search_results = soup.find('div', class_='searchresults') or soup.find('ul', class_='mw-search-results') or soup
            
            for link in search_results.find_all('a', href=True):
                href = link['href']
                
                if '/wiki/File:' in href and href.startswith('/wiki/File:'):
                    filename = href.lower()
                    if any(ext in filename for ext in image_extensions):
                        full_url = f"https://commons.wikimedia.org{href}"
                        if full_url not in file_urls:
                            logger.info(f"Found image file: {href}")
                            file_urls.append(full_url)
                            if len(file_urls) >= max_results:
                                break
            
            if len(file_urls) < max_results:
                for element in soup.find_all(['span', 'div', 'a'], string=lambda text: text and 'File:' in text):
                    text = element.get_text() if hasattr(element, 'get_text') else str(element)
                    if 'File:' in text:
                        import re
                        file_matches = re.findall(r'File:[^,\s\]]+\.(?:jpg|jpeg|png|webp|gif)', text, re.IGNORECASE)
                        for match in file_matches:
                            file_url = f"https://commons.wikimedia.org/wiki/{match.replace(' ', '_')}"
                            if file_url not in file_urls:
                                logger.info(f"Found image file from text: {match}")
                                file_urls.append(file_url)
                                if len(file_urls) >= max_results:
                                    break
                        if len(file_urls) >= max_results:
                            break
            
            logger.info(f"Found {len(file_urls)} image file URLs for query: {query}")
            return file_urls
            
        except Exception as e:
            logger.error(f"Error searching Wikimedia Commons: {e}")
            return []

    def extract_image_from_file_page(self, file_page_url: str) -> Optional[str]:
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(file_page_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            
            logger.info(f"Extracting image from file page: {file_page_url}")
            
            file_page_img = soup.find('div', class_='fullImageLink')
            if file_page_img:
                link = file_page_img.find('a', href=True)
                if link:
                    href = link['href']
                    if any(ext in href.lower() for ext in image_extensions):
                        logger.info(f"Found main file image: {href}")
                        return href
            
            for link in soup.find_all('a', href=True):
                link_text = link.get_text().strip().lower()
                if ('original file' in link_text or 'full resolution' in link_text or 
                    'original' in link_text):
                    href = link['href']
                    if any(ext in href.lower() for ext in image_extensions):
                        logger.info(f"Found original file link: {href}")
                        return href
            
            largest_thumb = None
            largest_size = 0
            
            for img in soup.find_all('img', src=True):
                src = img['src']
                if ('upload.wikimedia.org' in src and 
                    '/thumb/' in src and
                    any(ext in src.lower() for ext in image_extensions)):
                    
                    import re
                    size_match = re.search(r'(\d+)px-', src)
                    if size_match:
                        size = int(size_match.group(1))
                        if size > largest_size:
                            largest_size = size
                            largest_thumb = src
            
            if largest_thumb:
                parts = largest_thumb.split('/thumb/')
                if len(parts) == 2:
                    after_thumb = parts[1]
                    path_parts = after_thumb.split('/')
                    if len(path_parts) >= 3:
                        original_path = '/'.join(path_parts[:-1])
                        original_url = f"https://upload.wikimedia.org/wikipedia/commons/{original_path}"
                        logger.info(f"Converted largest thumbnail to original: {original_url}")
                        return original_url
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if ('upload.wikimedia.org' in href and 
                    any(ext in href.lower() for ext in image_extensions) and
                    '/thumb/' not in href):
                    logger.info(f"Found direct upload link: {href}")
                    return href
            
            logger.warning(f"Could not find image URL in {file_page_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting image from {file_page_url}: {e}")
            return None

    def download_image(self, image_url: str, province: str, query: str) -> Optional[str]:
        
        try:
            province_dir = self.download_dir / province.replace(" ", "_")
            province_dir.mkdir(exist_ok=True)
   
            parsed_url = urllib.parse.urlparse(image_url)
            file_name = os.path.basename(parsed_url.path)
            
            if '.' not in file_name:
                file_name = f"{query.replace(' ', '_')}_{int(time.time())}.jpg"
            
            counter = 1
            base_name, ext = os.path.splitext(file_name)
            while (province_dir / file_name).exists():
                file_name = f"{base_name}_{counter}{ext}"
                counter += 1
            
            local_path = province_dir / file_name
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not point to an image: {image_url}")
                return None
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded image: {local_path}")
            return str(local_path)
            
        except Exception as e:
            logger.error(f"Error downloading image from {image_url}: {e}")
            return None

    def cleanup_local_file(self, local_path: str) -> bool:
        try:
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
                logger.info(f"Cleaned up local file: {local_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up file {local_path}: {e}")
            return False

    def extract_cultural_context_from_video(self, video_data: Dict[str, Any], query: str) -> str:
        try:
            title = video_data.get('title', '')
            description = video_data.get('description', '')[:500] 
            
            extraction_prompt = f"""Extract the most specific cultural element name from this video information.

                        Video Title: {title}
                        Video Description: {description}
                        Search Query: {query}

                        Please identify and return ONLY the most specific cultural element name (e.g., "Tari Kecak", "Gamelan Jawa", "Batik Jogja", "Wayang Kulit").

                        Rules:
                        1. Return the cultural element in its traditional Indonesian name if possible
                        2. Include the specific type/style if mentioned (e.g., "Tari Kecak" not just "dance")
                        3. If multiple elements are mentioned, choose the most prominent one
                        4. If no specific element can be identified, return the search query
                        5. Return ONLY the cultural element name, nothing else

                        Examples:
                        - "Traditional Balinese Kecak Dance Performance" → "Tari Kecak"
                        - "Javanese Gamelan Music Concert" → "Gamelan Jawa"
                        - "Wayang Kulit Shadow Puppet Show" → "Wayang Kulit"
                        """
            
            response = self.text_llm.invoke([HumanMessage(content=extraction_prompt)])
            cultural_context = response.content.strip().replace('"', '').replace("'", "")
            
            logger.info(f"Extracted cultural context from video: {cultural_context}")
            return cultural_context if cultural_context else query
            
        except Exception as e:
            logger.error(f"Error extracting cultural context from video: {e}")
            return query

    def extract_cultural_context_from_image(self, file_page_url: str, query: str) -> str:
        try:
            import re
            filename_match = re.search(r'/wiki/File:([^/]+)', file_page_url)
            filename = filename_match.group(1) if filename_match else ""
            
            filename = urllib.parse.unquote(filename)
            filename = filename.replace('_', ' ').replace('-', ' ')
            
            extraction_prompt = f"""Extract the most specific cultural element name from this Wikimedia Commons filename.

                    Filename: {filename}
                    Search Query: {query}

                    Please identify and return ONLY the most specific cultural element name (e.g., "Tari Kecak", "Gamelan Jawa", "Batik Jogja", "Rumah Gadang").

                    Rules:
                    1. Return the cultural element in its traditional Indonesian name if possible
                    2. Include the specific type/style if mentioned
                    3. Remove file extensions and technical terms
                    4. If filename doesn't contain specific cultural info, return the search query
                    5. Return ONLY the cultural element name, nothing else

                    Examples:
                    - "Tari_Kecak_performance.jpg" → "Tari Kecak"
                    - "Batik_Jogja_traditional_pattern.png" → "Batik Jogja"
                    - "Rumah_Gadang_Minangkabau.jpg" → "Rumah Gadang"
                    """
            
            response = self.text_llm.invoke([HumanMessage(content=extraction_prompt)])
            cultural_context = response.content.strip().replace('"', '').replace("'", "")
            
            logger.info(f"Extracted cultural context from image filename: {cultural_context}")
            return cultural_context if cultural_context else query
            
        except Exception as e:
            logger.error(f"Error extracting cultural context from image: {e}")
            return query

    def validate_cultural_accuracy(self, province: str, cultural_category: str, query: str) -> float:
        
        try:
            validation_prompt = f"""Analyze this image to determine if it accurately represents {cultural_category} from {province} province in Indonesia.

                    Search query used: "{query}"
                    Target province: {province}
                    Cultural category: {cultural_category}

                    Please evaluate:
                    1. Does the image show authentic Indonesian cultural content?
                    2. Is it specifically related to {province} province?
                    3. Does it match the cultural category "{cultural_category}"?

                    Return ONLY a confidence score between 0.0 and 1.0 as a number (e.g., 0.85)."""
            
            response = self.text_llm.invoke([HumanMessage(content=validation_prompt)])
            response_text = response.content.strip()
            
            import re
            score_match = re.search(r'(\d+\.?\d*)', response_text)
            if score_match:
                confidence_score = float(score_match.group(1))
                if confidence_score > 1.0:
                    confidence_score = confidence_score / 100.0
                confidence_score = max(0.0, min(1.0, confidence_score))
            else:
                logger.warning(f"Could not extract confidence score from: {response_text}")
                confidence_score = 0.0
            
            logger.info(f"AI validation confidence for {province}: {confidence_score}")
            return confidence_score
                    
        except Exception as e:
            logger.error(f"Error in cultural validation: {e}")
            specific_terms = ['tari', 'dance', 'musik', 'music', 'pakaian', 'clothing', 'rumah', 'house', 'batik', 'wayang']
            is_specific = any(term in query.lower() for term in specific_terms)
            confidence_score = 0.85 if is_specific else 0.4
            logger.info(f"Fallback validation confidence for {province}: {confidence_score}")
            return confidence_score

    def scrape_validated_cultural_media(self) -> Dict[str, Any]:
        province = random.choice(self.provinces)
        media_type = self.choose_media_type()
        
        if media_type == "video":
            cultural_category = random.choice(self.video_cultural_categories)
        else: 
            cultural_category = random.choice(self.cultural_categories)
        
        logger.info(f"Starting pipeline for {cultural_category} from {province} (media type: {media_type})")
        
        try:
            query = self.generate_cultural_query(province, cultural_category)
            
            if media_type == "image":
                return self._scrape_image_media(province, cultural_category, query)
            else:  
                return self._scrape_video_media(province, cultural_category, query)
            
        except Exception as e:
            logger.error(f"Error in scraping pipeline: {e}")
            return {
                "province": province,
                "cultural_category": cultural_category,
                "media_type": media_type,
                "query": query if 'query' in locals() else None,
                "status": "error",
                "error": str(e),
                "media_url": None,
                "local_path": None,
                "confidence_score": 0.0
            }

    def _scrape_image_media(self, province: str, cultural_category: str, query: str) -> Dict[str, Any]:
        file_urls = self.search_wikimedia_commons(query, max_results=3)
        
        if not file_urls:
            logger.warning(f"No image files found for query: {query}")
            return {
                "province": province,
                "cultural_category": cultural_category,
                "media_type": "image",
                "query": query,
                "status": "no_results",
                "media_url": None,
                "local_path": None,
                "confidence_score": 0.0
            }
        
        for file_url in file_urls:
            logger.info(f"Processing image file: {file_url}")
            
            image_url = self.extract_image_from_file_page(file_url)
            if not image_url:
                continue
            
            local_path = self.download_image(image_url, province, query)
            if not local_path:
                continue
            
            confidence_score = self.validate_cultural_accuracy(province, cultural_category, query)
            cultural_context = self.extract_cultural_context_from_image(file_url, query)
            
            result = {
                "province": province,
                "cultural_category": cultural_category,
                "media_type": "image",
                "query": query,
                "status": "success",
                "file_page_url": file_url,
                "media_url": image_url,
                "local_path": local_path,
                "confidence_score": confidence_score,
                "cultural_context": cultural_context,
            }
            
            logger.info(f"Image pipeline completed for {province}: confidence {confidence_score}, context: {cultural_context}")
            return result
        
        return {
            "province": province,
            "cultural_category": cultural_category,
            "media_type": "image",
            "query": query,
            "status": "processing_failed",
            "media_url": None,
            "local_path": None,
            "confidence_score": 0.0
        }

    def _scrape_video_media(self, province: str, cultural_category: str, query: str) -> Dict[str, Any]:
        videos = self.search_youtube_videos(query, max_results=3)
        
        if not videos:
            logger.warning(f"No videos found for query: {query}")
            return {
                "province": province,
                "cultural_category": cultural_category,
                "media_type": "video",
                "query": query,
                "status": "no_results",
                "media_url": None,
                "local_path": None,
                "confidence_score": 0.0
            }
        
        for video in videos:
            logger.info(f"Processing video: {video['title']}")
            
            confidence_score = self.validate_video_cultural_accuracy(video, province, cultural_category, query)
            cultural_context = self.extract_cultural_context_from_video(video, query)
            
            result = {
                "province": province,
                "cultural_category": cultural_category,
                "media_type": "video",
                "query": query,
                "status": "success",
                "video_id": video['video_id'],
                "media_url": video['video_url'],
                "title": video['title'],
                "description": video['description'],
                "channel_title": video['channel_title'],
                "thumbnail_url": video['thumbnail_url'],
                "published_at": video['published_at'],
                "local_path": None,
                "confidence_score": confidence_score,
                "cultural_context": cultural_context,
            }
            
            logger.info(f"Video pipeline completed for {province}: confidence {confidence_score}, context: {cultural_context}")
            return result
        
        return {
            "province": province,
            "cultural_category": cultural_category,
            "media_type": "video",
            "query": query,
            "status": "processing_failed",
            "media_url": None,
            "local_path": None,
            "confidence_score": 0.0
        }

    def scrape_until_valid(self, max_attempts: int = 10) -> Dict[str, Union[str, float]]:
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Scraping attempt {attempt}/{max_attempts}")
            
            try:
                result = self.scrape_validated_cultural_media()
                
                confidence_score = result.get("confidence_score", 0.0)
                has_media = result.get("media_url") is not None
                media_type = result.get("media_type", "unknown")
                is_valid = confidence_score >= 0.85
                
                if is_valid and has_media:
                    logger.info(f"Found valid {media_type} on attempt {attempt}: {result['province']} (confidence: {confidence_score})")
                    
                    if result.get("local_path"):
                        self.cleanup_local_file(result["local_path"])
                    
                    return_data = {
                        "province": result["province"],
                        "media_type": media_type,
                        "media_url": result["media_url"],
                        "cultural_category": result["cultural_category"],
                        "query": result["query"],
                        "cultural_context": result.get("cultural_context", result["query"])
                    }
                    
                    return return_data
                else:
                    logger.warning(f"Attempt {attempt} failed - Confidence: {confidence_score} (need ≥0.85), Has media: {has_media}, Media type: {media_type}")
                    if result.get("local_path"):
                        self.cleanup_local_file(result["local_path"])
                    
                    time.sleep(1)
                    continue
                    
            except Exception as e:
                logger.error(f"Error on attempt {attempt}: {e}")
                time.sleep(1)
                continue
        
        logger.error(f"Failed to get valid media after {max_attempts} attempts")
        raise Exception(f"Could not find valid cultural media after {max_attempts} attempts")

