#!/usr/bin/env python3
"""
Test YouTube Download using YouTube Data API v3 + yt-dlp
Search for songs using YouTube API, then download using yt-dlp
"""

import os
import sys
import asyncio
import yt_dlp
import requests
from pathlib import Path

# YouTube API Configuration
YOUTUBE_API_KEY = "AIzaSyCaRgEDBFWVHRDaNCM6wEX__2NR_wGcyNk"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"

# Test songs to search and download
TEST_SONGS = [
    "Tum Hi Ho Aashiqui 2",
    "Kal Ho Naa Ho Title Song",
    "Chaiyya Chaiyya Dil Se",
    "Jeene Laga Hoon Ramaiya Vastavaiya",
    "Senorita Zindagi Na Milegi Dobara",
    "Kabira Yeh Jawaani Teri",
    "Ilahi Yeh Jawaani Hai",
    "Gerua Dilwale",
    "Tum Se Hi Jab We Met",
    "Pehla Nasha Jo Jeeta Wohi Sikandar",
]

def search_youtube_video(query: str) -> dict:
    """Search for a video using YouTube Data API v3"""
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': 1,
        'key': YOUTUBE_API_KEY,
        'videoEmbeddable': 'true',
    }
    
    try:
        response = requests.get(f"{YOUTUBE_API_URL}/search", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if items:
                item = items[0]
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                channel = item['snippet']['channelTitle']
                
                return {
                    'id': video_id,
                    'title': title,
                    'channel': channel,
                    'url': f"https://www.youtube.com/watch?v={video_id}"
                }
        
        return None
        
    except Exception as e:
        print(f"   ❌ Search error: {e}")
        return None

def download_audio(video_url: str, video_id: str, output_dir: str = "test_downloads") -> bool:
    """Download audio from YouTube using yt-dlp"""
    
    Path(output_dir).mkdir(exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_dir}/{video_id}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            
            # Check if file was created
            filename = f"{output_dir}/{video_id}.mp3"
            if Path(filename).exists():
                file_size = Path(filename).stat().st_size / (1024 * 1024)  # MB
                duration = info.get('duration', 0)
                
                return {
                    'success': True,
                    'filename': filename,
                    'size_mb': round(file_size, 2),
                    'duration_sec': duration
                }
            
            return {'success': False, 'error': 'File not created'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    print("=" * 80)
    print("🎵 YouTube Download Test: YouTube Data API v3 + yt-dlp")
    print("=" * 80)
    print(f"\n📋 Testing {len(TEST_SONGS)} songs")
    print(f"🔑 API Key: {YOUTUBE_API_KEY[:10]}...{YOUTUBE_API_KEY[-5:]}")
    print()
    
    results = []
    
    for i, song_query in enumerate(TEST_SONGS, 1):
        print(f"\n{'='*80}")
        print(f"🎵 Test {i}/{len(TEST_SONGS)}: {song_query}")
        print(f"{'='*80}")
        
        # Step 1: Search using YouTube API
        print("\n[1/2] 🔍 Searching YouTube API...")
        video_info = search_youtube_video(song_query)
        
        if not video_info:
            print(f"   ❌ FAILED: Video not found")
            results.append({
                'query': song_query,
                'search': False,
                'download': False,
                'error': 'Video not found'
            })
            continue
        
        print(f"   ✅ Found: {video_info['title']}")
        print(f"   📺 Channel: {video_info['channel']}")
        print(f"   🔗 URL: {video_info['url']}")
        print(f"   🆔 Video ID: {video_info['id']}")
        
        # Step 2: Download using yt-dlp
        print(f"\n[2/2] ⬇️  Downloading with yt-dlp...")
        download_result = download_audio(
            video_info['url'],
            video_info['id']
        )
        
        if download_result.get('success'):
            print(f"   ✅ Downloaded successfully!")
            print(f"   📁 File: {download_result['filename']}")
            print(f"   💾 Size: {download_result['size_mb']} MB")
            print(f"   ⏱️  Duration: {download_result['duration_sec']}s")
            
            results.append({
                'query': song_query,
                'video_id': video_info['id'],
                'title': video_info['title'],
                'search': True,
                'download': True,
                'size_mb': download_result['size_mb'],
                'duration_sec': download_result['duration_sec']
            })
        else:
            print(f"   ❌ Download failed: {download_result.get('error', 'Unknown error')}")
            results.append({
                'query': song_query,
                'video_id': video_info.get('id'),
                'search': True,
                'download': False,
                'error': download_result.get('error')
            })
    
    # Print Summary
    print("\n\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    search_success = sum(1 for r in results if r['search'])
    download_success = sum(1 for r in results if r['download'])
    total = len(results)
    
    print(f"\n✅ YouTube API Search: {search_success}/{total} ({search_success/total*100:.1f}%)")
    print(f"✅ yt-dlp Download: {download_success}/{total} ({download_success/total*100:.1f}%)")
    
    print(f"\n{'='*80}")
    print(f"{'Song':<45} {'Search':<10} {'Download':<10}")
    print(f"{'='*80}")
    
    for r in results:
        query = r['query'][:43] + '..' if len(r['query']) > 45 else r['query']
        search_status = "✅" if r['search'] else "❌"
        download_status = "✅" if r['download'] else "❌"
        print(f"{query:<45} {search_status:<10} {download_status:<10}")
    
    print(f"{'='*80}")
    
    # Show downloaded files
    downloaded = [r for r in results if r['download']]
    if downloaded:
        print(f"\n📁 Downloaded Files ({len(downloaded)}):")
        print("-" * 80)
        for r in downloaded:
            print(f"  • {r.get('title', 'Unknown')}")
            print(f"    File: {r['video_id']}.mp3")
            print(f"    Size: {r.get('size_mb', 'N/A')} MB | Duration: {r.get('duration_sec', 'N/A')}s")
    
    # Final verdict
    print(f"\n{'='*80}")
    if download_success >= 8:
        print(f"🎉 EXCELLENT! {download_success}/{total} songs downloaded successfully!")
        print("✅ System is ready for production use!")
    elif download_success >= 5:
        print(f"👍 GOOD! {download_success}/{total} songs downloaded successfully!")
        print("⚠️  Some issues detected, review errors above")
    else:
        print(f"⚠️  ISSUES DETECTED! Only {download_success}/{total} downloads succeeded")
        print("❌ Review errors and fix before production use")
    print(f"{'='*80}\n")
    
    return download_success == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
