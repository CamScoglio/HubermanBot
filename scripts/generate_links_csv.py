import os
import subprocess
import json
import csv
import re
from datetime import datetime

# Create data folder if doesn't exist
os.makedirs("../data/", exist_ok=True)

def extract_video_info(channel_url):
    print("\nScraping video info... (this might take a few seconds)")
    command = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        channel_url
    ]
    result = subprocess.run(command, capture_output=True, text=True)

    videos = []
    for line in result.stdout.splitlines():
        try:
            data = json.loads(line)
            video_id = data.get('id')
            title = data.get('title')
            if video_id and title:
                videos.append({
                    "name": title,
                    "link": f"https://www.youtube.com/watch?v={video_id}"
                })
        except Exception as e:
            print(f"Error parsing a line: {e}")
            continue

    return videos

def save_videos_to_csv(videos, channel_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../data/{channel_name}_links_{timestamp}.csv"
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["name", "link"])
        writer.writeheader()
        for video in videos:
            writer.writerow(video)
    return filename

def main():
    print("🔥 Welcome to YouTube Channel Scraper 🔥")
    channel_url = input("\nPaste the full YouTube Channel URL: ").strip()
    channel_name = input("\nType a simple name for this channel (ex: hubermanlab): ").strip().lower()

    if not channel_url or not channel_name:
        print("❌ Error: You must provide both a channel URL and a channel name.")
        return

    videos = extract_video_info(channel_url)

    if not videos:
        print("❌ No videos found or failed to scrape. Check the URL or channel privacy settings.")
        return

    saved_file = save_videos_to_csv(videos, channel_name)
    print(f"\n✅ Done! Video links saved to {saved_file}\n")
    print("👉 Now open it, clean it manually, and save it as /data/new_links.csv before running update_huberman_brain.py!")

if __name__ == "__main__":
    main()
