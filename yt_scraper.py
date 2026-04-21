import os
import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

# --- DX Error Payloads (Implementing the post's philosophy) ---
def get_dx_error_response(video_id, error_type="TRANSCRIPT_DISABLED"):
    """
    Returns a 'Bridge, not Dead End' error payload with deep-links to documentation.
    Derived from: https://github.com/yourusername/python-yt-scraper/wiki/Errors
    """
    error_map = {
        "TRANSCRIPT_DISABLED": {
            "status": 404,
            "error_code": "YT_TRANSCRIPT_UNAVAILABLE",
            "message": f"The creator of video '{video_id}' has disabled closed captioning.",
            "dx_deep_link": "https://github.com/yourusername/python-yt-scraper/wiki/Errors#transcript-unavailable"
        },
        "INVALID_ID": {
            "status": 400,
            "error_code": "YT_INVALID_ID",
            "message": f"The provided YouTube ID '{video_id}' appears to be malformed or non-existent.",
            "dx_deep_link": "https://github.com/yourusername/python-yt-scraper/wiki/Errors#invalid-id"
        }
    }
    return error_map.get(error_type, {"status": 500, "error": "Internal Processing Error"})


# --- CORE REFACTOR (Making it Testable) ---

def clean_transcript_text(text: str) -> str:
    """Removes common verbal fillers (uh, um, like) and collapse whitespace."""
    if not text: return ""
    fillers = [r'\buh\b', r'\bum\b', r'\blike\b', r'\bbasically\b', r'\bright\b', r'\bso\b']
    for filler in fillers:
        text = re.sub(filler, '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[.*?\]', '', text) # Remove [Music], [Applause]
    return re.sub(r'\s+', ' ', text).strip()


def fetch_single_transcript(video_id: str):
    """Fetches, cleans, and returns the transcript for ONE video ID."""
    try:
        raw_data = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([entry['text'] for entry in raw_data])
        cleaned_text = clean_transcript_text(full_text)
        return {"success": True, "id": video_id, "data": cleaned_text}
    
    except TranscriptsDisabled:
        # Implement the professional DX error handler here
        dx_payload = get_dx_error_response(video_id, "TRANSCRIPT_DISABLED")
        return {"success": False, "id": video_id, "error_data": dx_payload}
    
    except Exception as e:
        # Generic fallback, but you should expand get_dx_error_response for more edge cases
        return {"success": False, "id": video_id, "error": str(e)}


def main(ids: list, output_filename="clean_transcripts.md"):
    """Linear execution logic (formerly your entire script)."""
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
                # If it failed, dump the professional JSON error payload directly into the MD
                # This helps you know exactly why the video failed and gives you the DX link.
                import json
                f.write(f"> [!WARNING]\n> {result['error_data']['message']}\n> See DX Link: {result['error_data']['dx_deep_link']}\n\n```json\n")
                f.write(json.dumps(result["error_data"], indent=2))
                f.write("\n```\n\n---\n\n")

    print(f"\nSaved to {output_filename}")


if __name__ == "__main__":
    # Add your real IDs here from image_0.png workflow
    MY_IDS = ["dQw4w9WgXcQ", "INVALID_ID_TEST"] 
    main(MY_IDS)