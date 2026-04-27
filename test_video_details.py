#!/usr/bin/env python3
"""
Test YouTube Video Details API
Tests fetching video information using YouTube Data API v3
"""

import requests

API_KEY = "AIzaSyCaRgEDBFWVHRDaNCM6wEX__2NR_wGcyNk"

# Test with different video IDs
TEST_VIDEOS = [
    ("A_ZMnD36h8g", "Tum Hi Ho - Aashiqui 2"),
    ("kJQP7kiw5Fk", "Despacito - Luis Fonsi"),
    ("JGwWNGJdvx8", "Shape of You - Ed Sheeran"),
]

def test_video_details(video_id, description):
    """Test getting video details from YouTube API"""
    print("=" * 70)
    print(f"Testing: {description}")
    print(f"Video ID: {video_id}")
    print("=" * 70)
    
    url = "https://www.googleapis.com/youtube/v3/videos"
    
    params = {
        "part": "snippet,contentDetails,statistics",
        "id": video_id,
        "key": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200 and data.get("items"):
            video = data["items"][0]
            
            title = video["snippet"]["title"]
            channel = video["snippet"]["channelTitle"]
            published = video["snippet"]["publishedAt"]
            views = video["statistics"]["viewCount"]
            likes = video["statistics"].get("likeCount", "N/A")
            duration = video["contentDetails"]["duration"]
            thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
            
            print("\n✅ SUCCESS! Video details retrieved:")
            print("-" * 70)
            print(f"Title:     {title}")
            print(f"Channel:   {channel}")
            print(f"Published: {published}")
            print(f"Views:     {int(views):,}")
            print(f"Likes:     {int(likes):,}" if likes != "N/A" else f"Likes:     {likes}")
            print(f"Duration:  {duration}")
            print(f"Thumbnail: {thumbnail}")
            print("-" * 70)
            return True
            
        else:
            print(f"\n❌ FAILED!")
            print(f"Error Response: {data}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def test_invalid_video():
    """Test with invalid video ID to see error handling"""
    print("\n" + "=" * 70)
    print("Testing: Invalid Video ID")
    print("=" * 70)
    
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,contentDetails,statistics",
        "id": "INVALID123",
        "key": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {data}")
        
        if not data.get("items"):
            print("\n✅ Correctly handled invalid video ID (no items returned)")
            return True
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("\n🎬 YouTube Video Details API Test")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-5:]}")
    print()
    
    results = []
    
    # Test valid videos
    for video_id, description in TEST_VIDEOS:
        success = test_video_details(video_id, description)
        results.append((description, success))
        print()
    
    # Test invalid video
    invalid_ok = test_invalid_video()
    results.append(("Invalid Video Handling", invalid_ok))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {description}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! API key is working perfectly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
