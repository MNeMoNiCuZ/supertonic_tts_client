# Supertonic TTS Client

Python client for connecting to a Supertonic TTS server.

## Installation

```bash
pip install -r requirements-client.txt
```

**For Python 3.13+:**
```bash
pip install audioop-lts
```

**For MP3 support, install ffmpeg:**
- Windows: `choco install ffmpeg`
- Linux: `sudo apt-get install ffmpeg`
- macOS: `brew install ffmpeg`

## Quick Start

### Command Line

```bash
# Basic usage
python client.py "Hello world" -o output.wav

# MP3 output
python client.py "Hello world" -o output.mp3

# Play immediately
python client.py "Hello world" -p

# Custom settings
python client.py "Hello" -v F1 -q 10 -s 1.2 -o test.wav

# Remote server
python client.py "Hello" -u http://server-ip:8765 -o out.wav
```

### Python API

```python
from client import SupertonicClient

# Connect to server
client = SupertonicClient(base_url="http://localhost:8765")

# Synthesize
client.synthesize(
    text="Hello from Python",
    voice_style="M1",
    total_step=5,
    speed=1.05,
    save_path="output.wav"
)

client.close()
```

## Command-Line Arguments

| Short | Long | Description | Default |
|-------|------|-------------|---------|
| | `text` | Text to synthesize | Required |
| `-o` | `--output` | Output file (.wav, .mp3, etc.) | Required unless `-p` |
| `-v` | `--voice` | Voice: M1, M2, F1, F2 | M1 |
| `-q` | `--quality` | Quality 1-20 (higher=better) | 5 |
| `-s` | `--speed` | Speed 0.5-2.0 (higher=faster) | 1.05 |
| `-u` | `--url` | Server URL | http://localhost:8765 |
| `-p` | `--play` | Play immediately | false |
| | `--health` | Check server health | false |

## Voices

| Voice | Gender | Style | Best For |
|-------|--------|-------|----------|
| M1 | Male | Deep, authoritative | Narration, audiobooks |
| M2 | Male | Lighter, casual | Tutorials, conversation |
| F1 | Female | Clear, professional | News, education |
| F2 | Female | Warm, expressive | Storytelling |

## Quality Guide

| Quality | Speed | Use Case |
|---------|-------|----------|
| 1-2 | Fastest | Draft, testing |
| 3-5 | Fast | **Production** |
| 6-10 | Moderate | High quality |
| 11-20 | Slow | Studio quality |

## Audio Formats

- **WAV** (.wav) - Default, no extra dependencies
- **MP3** (.mp3) - Requires `pydub` + `ffmpeg`
- **OGG** (.ogg) - Requires `pydub` + `ffmpeg`
- **FLAC** (.flac) - Requires `pydub` + `ffmpeg`

## Python API Examples

### Context Manager

```python
from client import SupertonicClient

with SupertonicClient(base_url="http://localhost:8765") as client:
    client.synthesize(
        text="Using context manager",
        voice_style="F2",
        save_path="output.wav"
    )
```

### Batch Synthesis

```python
client = SupertonicClient()

texts = ["First", "Second", "Third"]
voices = ["M1", "F1", "M2"]

client.batch_synthesize(
    texts=texts,
    voice_styles=voices,
    save_dir="batch_output"
)
```

### MP3 Output

```python
client.synthesize(
    text="MP3 example",
    voice_style="F1",
    save_path="output.mp3"  # Auto-converts to MP3
)
```

## Configuration

Create a `.env` file in the same directory as `inference.py` to customize default settings:

```bash
# Server Settings
BASE_URL=http://localhost:8765
TIMEOUT=30

# Default Synthesis Settings
DEFAULT_VOICE=M1
DEFAULT_QUALITY=5
DEFAULT_SPEED=1.05
DEFAULT_FORMAT=wav

# Path Settings
TEMP_DIR=
OUTPUT_DIR=output
```

**Example `.env` configurations:**

```bash
# Remote server
BASE_URL=http://192.168.1.100:8765

# Custom temp directory for playback
TEMP_DIR=C:/Temp/TTS

# Higher quality defaults
DEFAULT_QUALITY=10
DEFAULT_VOICE=F1
```

Copy `.env.example` to `.env` and customize as needed. The `.env` file is optional - if not present, hardcoded defaults will be used

## Troubleshooting

### Connection Error
- Verify server is running: `curl http://localhost:8765/health`
- Check firewall settings
- Verify correct URL and port

### MP3 Error
```bash
pip install audioop-lts pydub
# Install ffmpeg (see installation section)
```

### Import Error (Python 3.13+)
```bash
pip install audioop-lts
```

## Server Setup

See `README-Docker.md` for server deployment instructions.
