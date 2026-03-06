import os
import requests
import json
import time

BASE_URL = "http://localhost:8000"
PROJECT_ID = "01c247540cc741cb" # Using an existing project ID from previous logs

def test_video_pipeline():
    print(f"--- Testing Video Pipeline for Project: {PROJECT_ID} ---")
    
    # 1. Generate Scene Clips
    print("\n1. Generating Scene Clips...")
    res = requests.post(f"{BASE_URL}/projects/{PROJECT_ID}/generate-scene-clips")
    print(f"Status: {res.status_code}")
    print(res.json())
    
    if res.status_code != 200:
        print("Scene clip generation failed!")
        return

    # 2. Render Final Video
    print("\n2. Rendering Final Video...")
    res = requests.post(f"{BASE_URL}/projects/{PROJECT_ID}/render-final-video")
    print(f"Status: {res.status_code}")
    data = res.json()
    print(data)
    
    if res.status_code == 200:
        print(f"\nSUCCESS! Project rendered to: {data.get('final_video_path')}")
        
        # 3. Check video endpoint
        print("\n3. Verifying video download endpoint...")
        res = requests.get(f"{BASE_URL}/projects/{PROJECT_ID}/video", stream=True)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print("Video endpoint is active and serving content.")
    else:
        print("Final render failed!")

if __name__ == "__main__":
    test_video_pipeline()
