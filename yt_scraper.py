import os
import re
import json
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

# --- API MODELS ---
class ScrapeRequest(BaseModel):
    video_ids: List[str]
    clean_mode: bool = True

# --- DX ERROR PAYLOADS ---
def get_dx_error_response(video_id, error_type="TRANSCRIPT_DISABLED"):
    """
    Returns a 'Bridge, not Dead End' error payload with deep-links to documentation.
    Linked to: https://github.com/david-fred/python-yt-scraper#error-reference
    """
    error_map = {
        "TRANSCRIPT_DISABLED": {
            "status": 404,
            "error_code": "YT_TRANSCRIPT_UNAVAILABLE",
            "message": f"The creator of video '{video_id}' has disabled closed captioning.",
            "dx_deep_link": "https://github.com/david-fred/python-yt-scraper#transcript-unavailable"
        },
        "INVALID_ID": {
            "status": 400,
            "error_code": "YT_INVALID_ID",
            "message": f"The provided YouTube ID '{video_id}' appears to be malformed or non-existent.",
            "dx_deep_link": "https://github.com/david-fred/python-yt-scraper#invalid-id"
        }
    }
    return error_map.get(error_type, {"status": 500, "error": "Internal Processing Error"})

# --- CORE LOGIC ---
def clean_transcript_text(text: str) -> str:
    """Removes common verbal fillers, bracketed text, and cleans up stray punctuation."""
    if not text: return ""

    # 1. Remove bracketed text like [Music] or [Applause]
    text = re.sub(r'\[.*?\]', '', text)
    
    # 2. Match filler words AND any optional commas/spaces immediately following them
    # \b ensures we match whole words only. [,?\s]* catches trailing punctuation.
    fillers = ['um', 'uh', 'like', 'basically', 'right', 'so', 'applause']
    for word in fillers:
        pattern = rf'\b{word}\b[,?\s]*'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # 3. Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text)
    
    # 4. Clean up "stray" punctuation (e.g., "word , word" or "word ,.")
    text = re.sub(r'\s+([,.!?])', r'\1', text) # move punctuation next to words
    text = re.sub(r',+([,.!?])', r'\1', text) # remove commas before other punctuation
    
    return text.strip()

def fetch_single_transcript(video_id: str):
    """Explicitly instantiates the API and handles object-based transcript snippets."""
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        
        # Grab English or first available
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            transcript = list(transcript_list)[0]
            
        raw_data = transcript.fetch()
        
        # Handle 'FetchedTranscriptSnippet' objects OR standard dicts
        text_parts = []
        for entry in raw_data:
            if hasattr(entry, 'text'):
                text_parts.append(entry.text)
            elif isinstance(entry, dict) and 'text' in entry:
                text_parts.append(entry['text'])
            else:
                text_parts.append(str(entry))

        full_text = " ".join(text_parts)
        cleaned_text = clean_transcript_text(full_text)
        return {"success": True, "id": video_id, "data": cleaned_text}
    
    except TranscriptsDisabled:
        return {"success": False, "id": video_id, "error_data": get_dx_error_response(video_id, "TRANSCRIPT_DISABLED")}
    
    except Exception as e:
        print(f"DEBUG: Error for {video_id}: {str(e)}")
        return {
            "success": False, # Fixed casing from 'false' to 'False'
            "id": video_id,
            "error_data": {
                "status": 500,
                "message": f"Extraction Error: {str(e)}",
                "dx_deep_link": "https://github.com/david-fred/python-yt-scraper#error-reference"
            }
        }

# --- FASTAPI APP ---
app = FastAPI(title="Python-YT-Scraper API")

@app.post("/api/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    """
    POST endpoint for Postman interaction.
    Accepts video_ids list and returns JSON results.
    """
    results = []
    for vid in request.video_ids:
        res = fetch_single_transcript(vid)
        results.append(res)
    return {"status": "completed", "results": results}

# --- CLI COMPATIBILITY ---
def main(ids: list, output_filename="clean_transcripts.md"):
    """Main execution logic for batch processing to file."""
    if not ids: return
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("# Consolidated Project Transcripts\n\n")
        for i, vid in enumerate(ids):
            print(f"[{i+1}/{len(ids)}] Processing {vid}")
            result = fetch_single_transcript(vid)
            f.write(f"## Video {i+1}: https://youtu.be/{vid}\n")
            if result["success"]:
                f.write(f"{result['data']}\n\n---\n\n")
            else:
                f.write(f"> [!WARNING]\n> {result['error_data']['message']}\n")
                f.write(f"> See DX Link: {result['error_data']['dx_deep_link']}\n\n```json\n")
                f.write(json.dumps(result["error_data"], indent=2))
                f.write("\n```\n\n---\n\n")
    print(f"\nSaved to {output_filename}")

if __name__ == "__main__":
    # Run FastAPI server if executed directly
    print("Starting API Server on http://localhost:5000")
    uvicorn.run(app, host="0.0.0.0", port=8000)