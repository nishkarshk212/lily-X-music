# Copyright (c) 2025 ShreyamousX1025
# Licensed under the MIT License.
# This file is part of ShreyaMusic


import os
import re
import asyncio
import aiohttp
from pathlib import Path

import yt_dlp
from py_yt import Playlist, VideosSearch

from lily import logger
from lily.helpers import Track, utils


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )



    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
        except Exception:
            return None
        if results and results["result"]:
            data = results["result"][0]
            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=data.get("title")[:25],
                thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
            )
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception:
            pass
        return tracks

    async def download(self, video_id: str, video: bool = False) -> str | None:
        from lily import config
        url = self.base + video_id
        ext = "mp4" if video else "mp3"
        filename = f"downloads/{video_id}.{ext}"

        if Path(filename).exists():
            return filename

        # Use NexGen API with proper timeout and retry logic
        api_type = "video" if video else "song"
        api_url = f"{config.API_URL}/{api_type}/{video_id}?api={config.API_KEY}"
        
        # Configure timeout for the session
        timeout = aiohttp.ClientTimeout(total=60, connect=30, sock_connect=30, sock_read=60)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                logger.info(f"Trying NexGen API for {video_id} ({api_type})")
                max_attempts = 5
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        logger.info(f"NexGen API attempt {attempt}/{max_attempts} for {video_id}")
                        
                        async with session.get(api_url) as response:
                            logger.info(f"NexGen API response status: {response.status}")
                            if response.status != 200:
                                logger.error(f"NexGen API returned status {response.status}")
                                if attempt < max_attempts:
                                    wait_time = min(attempt * 3, 10)  # Exponential backoff: 3s, 6s, 9s, 10s, 10s
                                    logger.info(f"Waiting {wait_time}s before retry...")
                                    await asyncio.sleep(wait_time)
                                continue
                            
                            data = await response.json()
                            status = data.get("status", "").lower()
                            logger.info(f"NexGen API status for {video_id}: {status}")

                            if status == "done":
                                download_url = data.get("link")
                                logger.info(f"NexGen API download link received")
                                if download_url:
                                    # Download the actual file
                                    async with session.get(download_url) as file_response:
                                        if file_response.status == 200:
                                            os.makedirs("downloads", exist_ok=True)
                                            with open(filename, 'wb') as f:
                                                while True:
                                                    chunk = await file_response.content.read(8192)
                                                    if not chunk:
                                                        break
                                                    f.write(chunk)
                                            logger.info(f"Successfully downloaded via NexGen: {filename}")
                                            return filename
                                        else:
                                            logger.error(f"Failed to download file: {file_response.status}")
                                            break
                                else:
                                    logger.error(f"No download link in response")
                                    break
                            elif status == "downloading":
                                logger.info(f"Still processing... waiting 5 seconds (attempt {attempt})")
                                await asyncio.sleep(5)
                                # Don't count "downloading" status as a failed attempt
                                continue
                            else:
                                logger.error(f"Unexpected NexGen status: {status}, response: {data}")
                                break
                                
                    except asyncio.TimeoutError:
                        logger.warning(f"NexGen API timeout on attempt {attempt}/{max_attempts}")
                        if attempt < max_attempts:
                            wait_time = min(attempt * 5, 15)  # Longer wait for timeouts
                            logger.info(f"Waiting {wait_time}s before retry after timeout...")
                            await asyncio.sleep(wait_time)
                        continue
                    except aiohttp.ClientError as e:
                        logger.warning(f"NexGen API client error on attempt {attempt}: {e}")
                        if attempt < max_attempts:
                            wait_time = min(attempt * 3, 10)
                            await asyncio.sleep(wait_time)
                        continue
                        
                logger.error(f"NexGen API failed after {max_attempts} attempts for {video_id}")
                
                # Fallback to NubCoder API if NexGen fails
                logger.info(f"Trying fallback NubCoder API for {video_id}")
                nubcoder_url = f"{config.API_BASE_URL}/download/{video_id}?token={config.API_TOKEN}"
                
                try:
                    async with session.get(nubcoder_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            download_url = data.get("download_url") or data.get("link") or data.get("url")
                            
                            if download_url:
                                logger.info(f"NubCoder API download link received for {video_id}")
                                async with session.get(download_url) as file_response:
                                    if file_response.status == 200:
                                        os.makedirs("downloads", exist_ok=True)
                                        with open(filename, 'wb') as f:
                                            while True:
                                                chunk = await file_response.content.read(8192)
                                                if not chunk:
                                                    break
                                                f.write(chunk)
                                        logger.info(f"Successfully downloaded via NubCoder: {filename}")
                                        return filename
                                    else:
                                        logger.error(f"NubCoder file download failed: {file_response.status}")
                            else:
                                logger.error(f"No download link in NubCoder response")
                        else:
                            logger.error(f"NubCoder API returned status {response.status}")
                except Exception as e:
                    logger.error(f"NubCoder API fallback failed: {e}", exc_info=True)
                
                # Second fallback: Use yt-dlp to download directly from YouTube
                logger.info(f"Trying second fallback yt-dlp for {video_id}")
                try:
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                    logger.info(f"Downloading via yt-dlp: {youtube_url}")
                    
                    os.makedirs("downloads", exist_ok=True)
                    
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3' if not video else 'mp4',
                            'preferredquality': '192',
                        }],
                        'outtmpl': f'downloads/{video_id}.%(ext)s',
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': False,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([youtube_url])
                        
                        # Check if file was created
                        expected_file = f"downloads/{video_id}.mp3" if not video else f"downloads/{video_id}.mp4"
                        if Path(expected_file).exists():
                            logger.info(f"Successfully downloaded via yt-dlp: {expected_file}")
                            return expected_file
                        else:
                            logger.error(f"yt-dlp download completed but file not found: {expected_file}")
                            
                except Exception as e:
                    logger.error(f"yt-dlp fallback failed for {video_id}: {e}", exc_info=True)
                    
            except Exception as e:
                logger.error(f"NexGen API failed for {video_id}: {e}", exc_info=True)
        
        return None
