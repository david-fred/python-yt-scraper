import os
import re
from youtube_transcript_api import YouTubeTranscriptApi

# PASTE YOUR IDs HERE
VIDEO_IDS = ["ID1", "ID2", "ID3"] 

def clean_text(text):
    """Removes common verbal fillers and extra whitespace to save tokens."""
    fillers = [
        r'\buh\b', r'\bum\b', r'\blike\b', r'\bso\b', r'\bactually\b', 
        r'\bbasically\b', r'\bright\b', r'\byou know\b'
    ]
    # Case-insensitive removal of fillers
    for filler in fillers:
        text = re.sub(filler, '', text, flags=re.IGNORECASE)
    # Remove bracketed sounds like [Music] or [Applause]
    text = re.sub(r'\[.*?\]', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def run_scraper(ids, output_file="clean_transcripts.md"):
    if not ids or ids[0] == "ID1":
        print("Error: Please update the VIDEO_IDS list with actual IDs.")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Project Transcripts\n\n")
        
        for i, vid in enumerate(ids):
            try:
                print(f"[{i+1}/{len(ids)}] Fetching: {vid}")
                raw_data = YouTubeTranscriptApi.get_transcript(vid)
                
                # Combine and clean
                raw_text = " ".join([entry['text'] for entry in raw_data])
                processed_text = clean_text(raw_text)
                
                f.write(f"## Video {i+1}: https://youtu.be/{vid}\n")
                f.write(f"{processed_text}\n\n---\n\n")
            except Exception as e:
                print(f"Failed {vid}: {e}")
                f.write(f"## Video {i+1}: {vid}\n[TRANSCRIPT UNAVAILABLE]\n\n")

    print(f"\nSuccess! File saved as: {output_file}")

if __name__ == "__main__":
    run_scraper(VIDEO_IDS)