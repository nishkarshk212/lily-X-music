# Copyright (c) 2025 Lilyx1025
# Licensed under the MIT License.
# This file is part of LilyMusic

"""
YouTube Data API v3 Integration
Uses official YouTube API for search and video details
"""

import aiohttp
from typing import Optional, List, Dict
from lily import config, logger


class YouTubeAPI:
    """Official YouTube Data API v3 client"""
    
    def __init__(self):
        self.api_key = config.YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search for videos using YouTube Data API v3
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-50)
            
        Returns:
            List of video dictionaries with id, title, channel, etc.
        """
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': min(max_results, 50),
            'key': self.api_key,
            'videoEmbeddable': 'true',
            'videoSyndicated': 'true'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/search", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        
                        results = []
                        for item in items:
                            video_id = item['id']['videoId']
                            snippet = item['snippet']
                            
                            results.append({
                                'id': video_id,
                                'title': snippet['title'],
                                'channel': snippet['channelTitle'],
                                'description': snippet.get('description', ''),
                                'thumbnail': snippet['thumbnails']['high']['url'],
                                'url': f"https://www.youtube.com/watch?v={video_id}"
                            })
                        
                        logger.info(f"YouTube API search returned {len(results)} results for: {query}")
                        return results
                    else:
                        error_text = await response.text()
                        logger.error(f"YouTube API search failed: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"YouTube API search error: {e}", exc_info=True)
            return []
    
    async def get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        Get video details using YouTube Data API v3
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with video details or None
        """
        params = {
            'part': 'snippet,contentDetails,statistics',
            'id': video_id,
            'key': self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/videos", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        
                        if items:
                            video = items[0]
                            snippet = video['snippet']
                            content_details = video.get('contentDetails', {})
                            statistics = video.get('statistics', {})
                            
                            return {
                                'id': video_id,
                                'title': snippet['title'],
                                'channel': snippet['channelTitle'],
                                'description': snippet.get('description', ''),
                                'thumbnail': snippet['thumbnails']['high']['url'],
                                'duration': content_details.get('duration', ''),
                                'view_count': statistics.get('viewCount', '0'),
                                'like_count': statistics.get('likeCount', '0'),
                                'url': f"https://www.youtube.com/watch?v={video_id}"
                            }
                        
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"YouTube API video details failed: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"YouTube API video details error: {e}", exc_info=True)
            return None
    
    async def is_quota_exceeded(self) -> bool:
        """
        Check if API quota is likely exceeded by making a test request
        
        Returns:
            True if quota is exceeded, False otherwise
        """
        params = {
            'part': 'snippet',
            'q': 'test',
            'type': 'video',
            'maxResults': 1,
            'key': self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/search", params=params) as response:
                    if response.status == 403:
                        data = await response.json()
                        error = data.get('error', {})
                        if 'quota' in error.get('message', '').lower():
                            logger.warning("YouTube API quota exceeded!")
                            return True
                    return False
        except Exception:
            return False


# Create singleton instance
yt_api = YouTubeAPI()
