---
name: voxtral-tts
description: "Voxtral TTS: Mistral voice cloning and text-to-speech via API."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tts, voice, clone, mistral, voxtral, audio, speech]
    related_skills: [heartmula, songwriting-and-ai-music]
---

# Voxtral TTS — Mistral Voice Cloning & Text-to-Speech

## Overview
Voxtral is Mistral's TTS API that supports both stock voices and custom voice clones. Voice clones are created via the Mistral console and accessed via the API using voice IDs.

## When to Use
- User wants to generate speech audio with a custom or stock voice
- User wants to send voice messages (combine with WbizTool or other messaging)
- User wants to add voiceover to video content (combine with HyperFrames)
- User asks about Voxtral, Mistral TTS, or voice cloning

## API Reference

### Endpoint
```
POST https://api.mistral.ai/v1/audio/speech
Authorization: Bearer $MISTRAL_API_KEY
Content-Type: application/json
```

### Model Name
The correct model name is `voxtral-mini-tts-latest` (NOT `mistral-tts-latest`).

To discover available models:
```bash
curl -s "https://api.mistral.ai/v1/models" \
  -H "Authorization: Bearer $MISTRAL_API_KEY" | \
  python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin).get('data',[]) if 'tts' in m['id'].lower() or 'vox' in m['id'].lower()]"
```

### Request Body
```json
{
  "model": "voxtral-mini-tts-latest",
  "input": "Text to speak.",
  "voice_id": "<voice-uuid>",
  "response_format": "mp3"
}
```

Supported response_format values: `mp3`, `wav`, `flac`, `opus`.

### Listing Voice Clones
```bash
curl -s "https://api.mistral.ai/v1/audio/voices" \
  -H "Authorization: Bearer $MISTRAL_API_KEY" | python3 -m json.tool
```

Returns paginated list with `items[]`, each containing `id`, `name`, `slug`, `languages`, `gender`, `age`, `tags`. Custom clones have a non-null `user_id`.

### Example (Python — recommended over curl)

**CRITICAL**: The API returns JSON with base64-encoded audio data, NOT raw binary. You must decode it.

```python
import json, urllib.request, base64

data = json.dumps({
    "model": "voxtral-mini-tts-latest",
    "input": "Bonjour, comment allez-vous ?",
    "voice_id": "<voice-uuid>",
    "response_format": "mp3"
}).encode()

req = urllib.request.Request(
    "https://api.mistral.ai/v1/audio/speech",
    data=data,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
)

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode())
    audio_bytes = base64.b64decode(result["audio_data"])
    with open("output.mp3", "wb") as f:
        f.write(audio_bytes)
```

If you save the response directly to a file (e.g., via `curl --output`), you get a JSON file, not audio. The file will be detected as `JSON data` by the `file` command and will fail to play.

### Example with Emotion and Speed (custom voice clone)
For a custom voice clone, use these parameters for dynamic content:

```python
data = json.dumps({
    "model": "voxtral-mini-tts-latest",
    "input": "Bonjour ! Voici un exemple de texte pour tester la voix personnalisée.",
    "voice_id": "YOUR_VOICE_CLONE_ID",  # Custom voice clone ID
    "emotion": 0.7,              # 0.7 for provocative/engaging tone (videos)
    "speed": 1.1,                # 1.1 for dynamic rhythm (videos)
    "response_format": "mp3"
}).encode()
```

**Note**: The `emotion` and `speed` parameters are supported for custom voice clones like `YOUR_VOICE_CLONE_ID` but may be ignored for stock voices. Check your voice clone documentation for full parameters.

### WhatsApp Sharing Workflow
When the user needs to share a Voxtral-generated audio file via WhatsApp:

1. **Generate the MP3** using the API (as shown above).
2. **Host the file** on a temporary HTTP server:
   ```bash
   python3 -m http.server 8000 --directory /path/to/audio/ &
   ```
3. **Send the direct download link** to the user:
   ```
   http://<server-ip>:8000/<filename>.mp3
   ```
4. **Instruct the user** to:
   - Click the link on their phone.
   - Share the downloaded file via WhatsApp (as a document or voice message).

**Pitfall**: WhatsApp Business API (WbizTool) cannot send generated audio directly due to platform restrictions. Always use a download link for user-mediated sharing.

**Alternative**: Use your VPS (`YOUR_VPS_IP`) to host files temporarily:
```bash
cp /path/to/audio.mp3 /home/ubuntu/public/
python3 -m http.server 8000 --directory /home/ubuntu/public/ &
```
Then share:
```
http://YOUR_VPS_IP:8000/audio.mp3
```

## Pitfalls

1. **Model name changed**: The model is `voxtral-mini-tts-latest`, NOT `mistral-tts-latest`. The latter returns `Invalid model` error (code 1500).

2. **Response is JSON with base64, NOT raw audio**: The API returns `{"audio_data": "<base64>"}`. You MUST decode with `base64.b64decode(result["audio_data"])` before saving. Saving the raw response produces a JSON file that won't play. This is the #1 cause of "audio not available" errors when sending to users.

3. **Voice ID must be complete UUID**: Truncated IDs return 404 (`Voice not found`, code 1902). Always retrieve the full UUID from `/v1/audio/voices` before generating.

4. **Voice clone retention**: Custom voice clones may disappear but often reappear. Always check `/v1/audio/voices` first to get current UUIDs. Don't cache voice IDs long-term.

5. **Security redaction breaks env export**: In production, API keys in `.env` get redacted (`MISTRAL_API_KEY=Ue42...MyCm`). Bash export/source fails. **SOLUTION**: Read `.env` directly in Python:
   ```python
   with open('/home/ubuntu/.hermes/.env', 'r') as f:
       for line in f:
           if line.startswith('MISTRAL_API_KEY=*** and '...' not in line:
               key = line.split('=', 1)[1]
               # Use key directly with urllib.request
   ```

6. **Curl with redacted keys fails**: Use Python `urllib.request` instead of curl for reliable API access when keys are redacted.

7. **Voice UUIDs**: Retrieve current UUIDs from `GET /v1/audio/voices` — don't hardcode them, they can change.

8. **Output size**: A short sentence (~5 words) produces ~20KB MP3. A 20-second clip is ~100KB. A 40-second clip is ~270KB (decoded from ~360KB base64 JSON).

9. **Emotion/speed parameters NOT SUPPORTED**: The API documentation shows `emotion` and `speed` parameters, but these return HTTP 422 "Unprocessable Entity" errors as of June 2026. DO NOT use these parameters in requests. Custom voice clones are already trained with their intended emotional tone. Focus on script quality and word choice rather than API parameters for voice improvement.

10. **HyperFrames audio integration pitfall**: When using Voxtral-generated audio in HyperFrames videos, audio may not be captured during rendering. Use these proven methods:
    - Method 1: `<audio id="audio" src="filename.mp3" preload="auto"></audio>` (simple, usually works)
    - Method 2: Explicit audio start in JavaScript:
      ```javascript
      document.addEventListener('DOMContentLoaded', () => {
          const audio = document.getElementById('audio');
          if (audio) {
              audio.currentTime = 0;
              audio.play().catch(e => console.log('Audio:', e));
          }
      });
      ```
    - Method 3: If audio still missing from final video, check ffprobe output for audio streams. Re-render with `--quality standard` and verify audio file is in the same directory as index.html.

## Voice Management

Voice clones are created in the Mistral console (https://console.mistral.ai), not via the API. The API is read-only for voices (list + use).

Stock voices follow the pattern: `en_paul_happy`, `en_paul_sad`, `en_paul_neutral`, etc. — with name, emotion, and language variants.

## Integration Patterns

### Send as WhatsApp voice message
1. Generate MP3 with Voxtral
2. Upload to WbizTool media API
3. Send via WbizTool send_msg with file_url

### Add to video (HyperFrames)
1. Generate MP3 with Voxtral
2. Use as audio track in HyperFrames project
3. Render with FFmpeg

### YouTube Automation Workflow
1. Generate script
2. Create audio with Voxtral (custom or stock voice)
3. Build HyperFrames video composition
4. Upload to YouTube with proper authentication

**Important**: YouTube OAuth tokens expire frequently. See `references/youtube-token-workflow.md` for token renewal process.
