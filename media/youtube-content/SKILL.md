---
name: youtube-content
description: "YouTube transcripts to summaries, threads, blogs, and video uploads."
platforms: [linux, macos, windows]
---

# YouTube Content Tool

## When to use

Use when the user:
- Shares a YouTube URL or video link.
- Asks to summarize a video, requests a transcript, or wants to extract and reformat content.
- Needs to **upload a video** to YouTube (with metadata, thumbnails, and privacy settings).
- Wants to **list accessible YouTube channels** or verify upload permissions.
- Encounters **YouTube API errors** (transcript disabled, quota limits, permission issues).

## Key Features
- **Transcript extraction** from any YouTube video (with timestamps, language fallback).
- **Content reformatting** into summaries, threads, blog posts, or chapters.
- **Video upload automation** with metadata, thumbnails, and privacy control.
- **Channel access verification** to debug permission issues.
- **Error handling** for common API limitations (quotas, disabled transcripts, unsupported media types).
- Needs to **upload a video** to YouTube (with metadata, thumbnails, and privacy settings).
- Wants to manage YouTube channels (list accessible channels, verify permissions).

Transforms transcripts into structured content (chapters, summaries, threads, blog posts) and handles video uploads via YouTube API.

## Key Features
- Transcript extraction and reformatting.
- Video upload automation with metadata.
- Channel access verification and management.
- Error handling for API limitations and permission issues.

## Setup

```bash
pip install youtube-transcript-api google-api-python-client google-auth-oauthlib
```

## Helper Scripts

### Transcript Extraction
`SKILL_DIR` is the directory containing this SKILL.md file. The script accepts any standard YouTube URL format, short links (youtu.be), shorts, embeds, live links, or a raw 11-character video ID.

```bash
# JSON output with metadata
python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping into further processing)
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

### Channel Management
```bash
# List accessible YouTube channels
python3 SKILL_DIR/scripts/list_channels.py --token youtube-token-chaine2.json
```

### Video Upload
```bash
# Upload a video with metadata
python3 SKILL_DIR/scripts/upload_video.py \
  --token youtube-token-chaine2.json \
  --file video.mp4 \
  --title "Your Video Title" \
  --description "Detailed description with links." \
  --tags "tag1,tag2,tag3" \
  --category 27 \
  --privacy unlisted \
  --thumbnail thumbnail.png

# Note: Tokens in /home/ubuntu/.hermes/google/youtube-token-*.json are now complete with client_id, client_secret, and token_uri
# Token naming convention: youtube-token-{channel-name}.json (e.g., youtube-token-contesenchantes.json, youtube-token-corporatemavericks.json)
```

## Output Formats

After fetching the transcript, format it based on what the user asks for:

- **Chapters**: Group by topic shifts, output timestamped chapter list
- **Summary**: Concise 5-10 sentence overview of the entire video
- **Chapter summaries**: Chapters with a short paragraph summary for each
- **Thread**: Twitter/X thread format — numbered posts, each under 280 chars
- **Blog post**: Full article with title, sections, and key takeaways
- **Quotes**: Notable quotes with timestamps

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Workflow

### For Transcripts
1. **Fetch** the transcript using the helper script with `--text-only --timestamps`.
2. **Validate**: confirm the output is non-empty and in the expected language. If empty, retry without `--language` to get any available transcript. If still empty, tell the user the video likely has transcripts disabled.
3. **Chunk if needed**: if the transcript exceeds ~50K characters, split into overlapping chunks (~40K with 2K overlap) and summarize each chunk before merging.
4. **Transform** into the requested output format. If the user did not specify a format, default to a summary.
5. **Verify**: re-read the transformed output to check for coherence, correct timestamps, and completeness before presenting.

### For Video Uploads
1. **Verify channel access** using `scripts/list_channels.py` to confirm the token has upload permissions.
2. **Prepare metadata**: title, description, tags, category, and privacy status.
3. **Convert audio to video** if needed (e.g., `ffmpeg -loop 1 -i image.png -i audio.mp3 -c:v libx264 output.mp4`).
4. **Upload** using `scripts/upload_video.py` with the prepared metadata.
5. **Validate**: check the upload status in YouTube Studio and confirm the video is processing correctly.
6. **Clean up local files**: After successful upload, delete the local video file to save space (especially important for large karaoke videos).

Example cleanup:
```python
# After successful upload
if result.returncode == 0:
    os.remove(video_path)
    # Also clean up temporary files in the working directory
    for temp_file in ['index.html', 'composition.js', 'audio.mp3', 'vignette.webp']:
        if os.path.exists(temp_file):
            os.remove(temp_file)
```

## Error Handling

- **Transcript disabled**: tell the user; suggest they check if subtitles are available on the video page.
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user.
- **Dependency missing**: run `pip install youtube-transcript-api google-api-python-client google-auth-oauthlib` and retry.
- **Insufficient permissions**: guide the user to re-authenticate with the correct scopes (`youtube.upload`).
- **Media type not supported**: convert the file to a supported format (e.g., audio to video).

## Common Pitfalls

- **Token expiration**: Always check token validity before uploading. Use `scripts/list_channels.py` to test access.
- **Quota limits**: Monitor API usage in the Google Cloud Console.
- **Audio-only uploads**: YouTube API requires video files. Convert audio to video using `ffmpeg`.
- **Thumbnail requirements**: Must be 1280x720, <2MB, in JPG/PNG/GIF format.
- **Privacy settings**: Test with `unlisted` first to avoid public mistakes.
- **Token format incompatibility**: Tokens in ~/.hermes/google/youtube-token-*.json may lack required fields (client_id, client_secret). The bundled scripts expect full OAuth2 tokens. Check if token contains: access_token, refresh_token, token_uri, client_id, client_secret.
- **Simulated uploads in cron jobs**: Cron jobs may create upload_result JSON files with fake URLs. Always verify actual upload by checking the channel or using real API calls, not trusting local JSON results.
