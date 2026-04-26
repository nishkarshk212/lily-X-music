# Copyright (c) 2025 ShreyamousX1025
# Licensed under the MIT License.
# This file is part of ShreyaMusic


import os
import re
import asyncio
import aiohttp
from pathlib import Path

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

        # Use NexGen API only (No fallback to yt-dlp)
        api_type = "video" if video else "song"
        api_url = f"{config.API_URL}/{api_type}/{video_id}?api={config.API_KEY}"
        
        async with aiohttp.ClientSession() as session:
            try:
                logger.info(f"Trying NexGen API for {video_id} ({api_type})")
                for attempt in range(5):
                    async with session.get(api_url) as response:
                        logger.info(f"NexGen API response status: {response.status}")
                        if response.status != 200:
                            logger.error(f"NexGen API returned status {response.status}")
                            break
                        
                        data = await response.json()
                        status = data.get("status", "").lower()
                        logger.info(f"NexGen API status for {video_id}: {status}")

                        if status == "done":
                            download_url = data.get("link")
                            logger.info(f"NexGen API download link: {download_url}")
                            if download_url:
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
                        elif status == "downloading":
                            logger.info(f"Still downloading... waiting 5 seconds")
                            await asyncio.sleep(5)
                        else:
                            logger.error(f"Unexpected NexGen status: {status}, response: {data}")
                            break
                logger.error(f"NexGen API failed after 5 attempts for {video_id}")
            except Exception as e:
                logger.error(f"NexGen API failed for {video_id}: {e}", exc_info=True)
        
        return None
