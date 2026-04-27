#!/usr/bin/env python3
"""
Test script for YouTube API key
Tests the API key: AIzaSyCaRgEDBFWVHRDaNCM6wEX__2NR_wGcyNk
"""

import requests
import sys

# Test YouTube API key
API_KEY = "AIzaSyCaRgEDBFWVHRDaNCM6wEX__2NR_wGcyNk"
BASE_URL = "https://www.googleapis.com/youtube/v3"

def test_search():
    """Test YouTube Data API v3 - Search endpoint"""
    print("=" * 60)
    print("Testing YouTube Data API v3 - Search")
    print("=" * 60)
    
    params = {
        'part': 'snippet',
        'q': 'Tum Hi Ho Arijit Singh',
        'type': 'video',
        'maxResults': 3,
        'key': API_KEY
    }
    
    try:
        response = requests.get(f"{BASE_URL}/search", params=params, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS! API key is working!")
            print(f"\nSearch Results:")
            
            for i, item in enumerate(data.get('items', []), 1):
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                channel = item['snippet']['channelTitle']
                print(f"\n{i}. {title}")
                print(f"   Channel: {channel}")
                print(f"   Video ID: {video_id}")
                print(f"   URL: https://www.youtube.com/watch?v={video_id}")
            
            return True
        else:
            print(f"\n❌ FAILED! Status: {response.status_code}")
            print(f"Error Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def test_video_details():
    """Test YouTube Data API v3 - Video Details endpoint"""
    print("\n" + "=" * 60)
    print("Testing YouTube Data API v3 - Video Details")
    print("=" * 60)
    
    # Test with a known video ID
    video_id = "A_ZMnD36h8g"  # Tum Hi Ho
    
    params = {
        'part': 'snippet,contentDetails,statistics',
        'id': video_id,
        'key': API_KEY
    }
    
    try:
        response = requests.get(f"{BASE_URL}/videos", params=params, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                video = data['items'][0]
                stats = video.get('statistics', {})
                print(f"\n✅ SUCCESS! Video details retrieved!")
                print(f"\nTitle: {video['snippet']['title']}")
                print(f"Views: {stats.get('viewCount', 'N/A')}")
                print(f"Likes: {stats.get('likeCount', 'N/A')}")
                print(f"Duration: {video['contentDetails']['duration']}")
                return True
            else:
                print(f"\n❌ No video found")
                return False
        else:
            print(f"\n❌ FAILED! Status: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

def check_quota():
    """Check API quota usage"""
    print("\n" + "=" * 60)
    print("Checking API Quota Information")
    print("=" * 60)
    print("\nYouTube Data API v3 Daily Quota: 10,000 units (free tier)")
    print("Search request cost: ~100 units")
    "Videos.list request cost: ~1 unit"
    print("\nEstimated requests per day:")
    print("- Search: ~100 requests")
    print("- Video details: ~10,000 requests")

if __name__ == "__main__":
    print("\n🔍 YouTube API Key Test")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-5:]}")
    print()
    
    # Run tests
    search_ok = test_search()
    
    if search_ok:
        video_ok = test_video_details()
        check_quota()
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Search API: {'✅ PASS' if search_ok else '❌ FAIL'}")
        print(f"Video Details API: {'✅ PASS' if video_ok else '❌ FAIL'}")
        print(f"\n{'✅ API Key is working!' if search_ok and video_ok else '❌ API Key has issues'}")
    else:
        print("\n❌ Search API failed. Video details test skipped.")
        sys.exit(1)
