# Supertonic TTS Client

Python client for connecting to a Supertonic TTS server. This client allows you to synthesize text into speech using various voices and settings, and save the output to different audio formats.

## Features

- **Synthesize Text to Speech**: Convert text into high-quality speech.
- **Multiple Voices**: Choose from a variety of male and female voices.
- **Customizable Quality and Speed**: Adjust the quality and speed of the generated speech.
- **Multiple Audio Formats**: Save the audio in WAV, MP3, and other formats.
- **Command-Line and Python API**: Use the client from the command line or integrate it into your Python applications.
- **Batch Synthesis**: Synthesize multiple texts in a single request.
- **Health Check**: Check the status of the Supertonic TTS server.

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/MNeMoNiCuZ/supertonic_tts_client.git
cd supertonic_tts_client
```

### 2. Create a Virtual Environment

You can use the included `venv_create.bat` script to create a virtual environment automatically.

**Windows:**
```bash
venv_create.bat
```

Alternatively, you can create it manually:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install the required packages from `requirements.txt`.

```bash
pip install -r requirements.txt
```

**For MP3 support, you also need to install ffmpeg:**

- **Windows:** `choco install ffmpeg`
- **Linux:** `sudo apt-get install ffmpeg`
- **macOS:** `brew install ffmpeg`

## Configuration

The client can be configured using a `.env` file.

### 1. Create the .env File

Copy the `.env.example` file to a new file named `.env`.

```bash
copy .env.example .env
```

### 2. Configure Environment Variables

Open the `.env` file and customize the following variables:

- **`BASE_URL`**: The URL of the Supertonic TTS server (e.g., `http://localhost:8765`). If you are running the server in a Docker container, this will be the URL of the Docker host.
- **`TIMEOUT`**: The timeout in seconds for requests to the server.
- **`DEFAULT_VOICE`**: The default voice to use for synthesis (e.g., `M1`, `F1`).
- **`DEFAULT_QUALITY`**: The default quality of the synthesized speech (1-20).
- **`DEFAULT_SPEED`**: The default speed of the synthesized speech (0.5-2.0).
- **`DEFAULT_FORMAT`**: The default audio format for output files (e.g., `wav`, `mp3`).
- **`TEMP_DIR`**: The directory to use for temporary files.
- **`OUTPUT_DIR`**: The directory to save output files to.

## Usage

### Command-Line Interface

The `inference.py` script provides a command-line interface for the client.

**Basic Usage:**

```bash
python inference.py "Hello world" -o output.wav
```

**MP3 Output:**

```bash
python inference.py "Hello world" -o output.mp3
```

**Play Immediately:**

```bash
python inference.py "Hello world" -p
```

**Custom Settings:**

```bash
python inference.py "Hello" -v F1 -q 10 -s 1.2 -o test.wav
```

**Remote Server:**

```bash
python inference.py "Hello" -u http://server-ip:8765 -o out.wav
```

**Check Server Health:**

```bash
python inference.py --health
```

### Python API

The `inference.py` script also provides a Python API for the client.

**Basic Usage:**

```python
from inference import SupertonicClient

with SupertonicClient() as client:
    client.synthesize(
        text="Hello from Python",
        voice_style="M1",
        save_path="output.wav"
    )
```

**MP3 Output:**

```python
from inference import SupertonicClient

with SupertonicClient() as client:
    client.synthesize(
        text="MP3 example",
        voice_style="F1",
        save_path="output.mp3"
    )
```

**Batch Synthesis:**

```python
from inference import SupertonicClient

with SupertonicClient() as client:
    texts = ["First", "Second", "Third"]
    voices = ["M1", "F1", "M2"]

    client.batch_synthesize(
        texts=texts,
        voice_styles=voices,
        save_dir="batch_output"
    )
```

**Check Server Health:**

```python
from inference import SupertonicClient

with SupertonicClient() as client:
    health = client.health()
    print(health)
```

### All Supported Functions

The following functions are available in the `SupertonicClient` class:

- **`health()`**: Checks the health of the Supertonic TTS server.
  - **Returns**: A dictionary containing the server status.

- **`synthesize(text, voice_style=None, total_step=None, speed=None, save_path=None)`**: Synthesizes speech from text.
  - **`text`** (str): The text to synthesize.
  - **`voice_style`** (str, optional): The voice style to use (e.g., "M1", "F2"). Defaults to `DEFAULT_VOICE` from `.env`.
  - **`total_step`** (int, optional): The number of denoising steps (1-20). Higher is better quality. Defaults to `DEFAULT_QUALITY` from `.env`.
  - **`speed`** (float, optional): The speech speed (0.5-2.0). Higher is faster. Defaults to `DEFAULT_SPEED` from `.env`.
  - **`save_path`** (str, optional): The path to save the audio file. The format is determined by the file extension.

- **`batch_synthesize(texts, voice_styles=None, total_step=None, speed=None, save_dir=None)`**: Synthesizes multiple texts in a single request.
  - **`texts`** (list): A list of texts to synthesize.
  - **`voice_styles`** (list, optional): A list of voice styles corresponding to the texts.
  - **`total_step`** (int, optional): The number of denoising steps.
  - **`speed`** (float, optional): The speech speed.
  - **`save_dir`** (str, optional): The directory to save the output files.

- **`close()`**: Closes the client session.

The following convenience functions are also available:

- **`synthesize_text(text, save_path, base_url=None, **kwargs)`**: A convenience function to synthesize text and save it to a file.
- **`play_audio(audio_path)`**: Plays an audio file.

For more detailed examples, see `inference-examples.py`.
