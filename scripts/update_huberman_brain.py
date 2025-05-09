import os
import json
import csv
import re
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from openai import OpenAI
import chromadb
from chromadb import PersistentClient

# Get API key from environment variable
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("Please set OPENAI_API_KEY environment variable")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# Directory setup
os.makedirs("../data/transcripts", exist_ok=True)
os.makedirs("../HubermanBotDB", exist_ok=True)

db_path = "../HubermanBotDB"
progress_file = "../data/processing_progress.json"

# Initialize ChromaDB
chroma_client = PersistentClient(path=db_path)
collection = chroma_client.get_or_create_collection(name="hubermanbot_chunks")

def load_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {'processed_videos': []}

def save_progress(video_id):
    progress = load_progress()
    if video_id not in progress['processed_videos']:
        progress['processed_videos'].append(video_id)
        with open(progress_file, 'w') as f:
            json.dump(progress, f)

def sanitize_filename(text):
    text = text.lower()
    text = re.sub(r'\s+', '_', text)  # spaces to underscores
    text = re.sub(r'[^\w\-]', '', text)  # remove non-word chars
    return text[:50]  # limit filename length if needed

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([item['text'] for item in transcript])
        return full_text
    except TranscriptsDisabled:
        print(f"❌ Transcript disabled for video: {video_id}")
        return None
    except Exception as e:
        print(f"❌ Failed to fetch transcript: {video_id}, error: {e}")
        return None

def chunk_text(text, max_tokens=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunk = " ".join(words[i:i + max_tokens])
        chunks.append(chunk)
    return chunks

def get_embedding(text):
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

def process_videos():
    new_links_path = "../data/new_links.csv"
    if not os.path.exists(new_links_path):
        print("❌ No new_links.csv found. Please add your cleaned links file to /data/.")
        return

    # Load progress
    bad_videos = []
    progress = load_progress()
    processed_videos = progress['processed_videos']

    with open(new_links_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        videos = list(reader)

    for idx, video in enumerate(videos):
        title = video['name']
        link = video['link']
        video_id_match = re.search(r"(?:v=|be/)([\w\-]{11})", link)
        if not video_id_match:
            print(f"❌ Invalid video link: {link}")
            continue

        video_id = video_id_match.group(1)

        # Skip if already processed
        if video_id in processed_videos:
            print(f"⏭️ Skipping already processed video {idx+1}/{len(videos)}: {title}")
            continue

        print(f"\n🔎 Processing video {idx+1}/{len(videos)}: {title}")

        full_transcript = get_transcript(video_id)
        if not full_transcript:
            bad_videos.append(title)
            continue

        try:
            # Save full transcript
            sanitized_title = sanitize_filename(title)
            transcript_path = f"../data/transcripts/hubermanlab_{sanitized_title}.txt"
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(full_transcript)

            # Chunk and embed
            chunks = chunk_text(full_transcript)
            for chunk_idx, chunk in enumerate(chunks):
                embedding = get_embedding(chunk)
                collection.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[{
                        "title": title,
                        "summary": f"Auto-generated chunk {chunk_idx+1}",
                        "category": "Auto-generated"
                    }],
                    ids=[f"{video_id}_chunk_{chunk_idx}"]
                )

            # Save progress after each successful video processing
            save_progress(video_id)
            print(f"✅ Successfully processed and saved video {idx+1}")

        except Exception as e:
            print(f"❌ Error processing video {title}: {str(e)}")
            # Continue with next video even if one fails
            continue
  
    progress = load_progress()
    processed_videos = progress['processed_videos']
    successful_videos = len(processed_videos)
    failed_videos = len(bad_videos)
    total_videos = successful_videos + failed_videos

    print("\n====== Final Report ======")
    print(f"✅ Successfully processed {successful_videos}/{total_videos} videos.")
    print(f"❌ Failed to process {failed_videos}/{total_videos} videos.\n")

    if failed_videos > 0:
        print("Failed videos:")
        for idx, title in enumerate(bad_videos, 1):
            print(f"{idx}. {title}")

    # Always cleanup after all videos are attempted
    os.remove(new_links_path)
    if os.path.exists(progress_file):
        os.remove(progress_file)

    if failed_videos > 0:
        print("\n⚠️ Some videos failed, but brain update is complete for available videos!")
    else:
        print("\n✅ Brain update complete. All new knowledge embedded and full transcripts saved!")


if __name__ == "__main__":
    process_videos()
