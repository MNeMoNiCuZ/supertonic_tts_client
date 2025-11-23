
import base64
import requests
import os
import sys
import tempfile
from typing import Optional, List, Literal, Union, Dict, Any
from pathlib import Path
from pydantic import Field
from tools.mcp_instance import mcp
import time
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment

# Module-level configuration constants
BASE_URL = 'http://localhost:8765'
TIMEOUT = 30
DEFAULT_VOICE = 'M1'
DEFAULT_QUALITY = 5
DEFAULT_SPEED = 1.05
DEFAULT_FORMAT = 'wav'
OUTPUT_DIR = 'output/supertonic_tts'

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Helper Functions ---

def _play_audio(audio_path: str) -> str:
    """Plays an audio file using the sounddevice library in a non-blocking manner."""
    try:
        data, samplerate = sf.read(audio_path)
        sd.play(data, samplerate)
        return f"Playback of audio message started and sent to the user: {os.path.basename(audio_path)}."
    except Exception as e:
        return f"Playback error: {e}"

def _normalize_voice_style(voice: Optional[str]) -> Optional[str]:
    """Adds .json extension to voice style name if missing."""
    if voice is None:
        return None
    return f"{voice}.json" if not voice.endswith('.json') else voice

def _convert_audio_format(wav_data: bytes, output_path: str) -> str:
    """Converts WAV audio data to the format specified by the output_path extension."""
    output_path_obj = Path(output_path)
    extension = output_path_obj.suffix.lower()

    if extension == '.wav':
        output_path_obj.write_bytes(wav_data)
        return f"Saved WAV audio to {output_path}"

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
        temp_wav.write(wav_data)
        temp_wav_path = temp_wav.name

    try:
        audio = AudioSegment.from_wav(temp_wav_path)
        format_name = extension[1:]
        
        if format_name == 'mp3':
            audio.export(str(output_path_obj), format='mp3', bitrate='192k')
        else:
            audio.export(str(output_path_obj), format=format_name)
        
        return f"Saved {format_name.upper()} audio to {output_path}"
    finally:
        os.unlink(temp_wav_path)

@mcp.tool()
async def supertonic_text_to_speech(
    mode: Literal['health', 'synthesize', 'batch_synthesize'] = Field(
        description="The operation to perform."
    ),
    text: Optional[str] = Field(
        None,
        description="The text to synthesize. Required for 'synthesize' mode."
    ),
    texts: Optional[List[str]] = Field(
        None,
        description="A list of texts to synthesize. Required for 'batch_synthesize' mode."
    ),
    voice_style: Optional[str] = Field(
        None,
        description="Voice style to use. Common options: 'M1' (deep, authoritative male), 'M2' (lighter, conversational male), 'F1' (professional, clear female), 'F2' (warm, expressive female)."
    ),
    voice_styles: Optional[List[str]] = Field(
        None,
        description="A list of voice styles for batch synthesis. Must be the same length as `texts`."
    ),
    quality: Optional[int] = Field(
        None,
        description="Synthesis quality (1-20). Higher is better."
    ),
    speed: Optional[float] = Field(
        None,
        description="Speech speed factor (0.5-2.0). Higher is faster."
    ),
    save_path: Optional[str] = Field(
        None,
        description="Full path to save the output audio file. If not provided for synthesis and playback is false, audio data is returned as base64."
    ),
    save_dir: Optional[str] = Field(
        None,
        description="Directory to save output files for 'batch_synthesize' mode."
    ),
    playback: bool = Field(
        False,
        description=(
            "If true, synthesizes and plays the audio directly. "
            "IMPORTANT: Playback is non-blocking and takes time. "
            "Sending another playback request will interrupt the current audio. "
            "To ensure a smooth experience, consolidate all speech into a single, longer `text` parameter in one tool call."
            "If asked to chat and respond in voice, it is a good idea to end your turn after the tool use and do not finish your turn by outputting any other text"
            "If asked to exclusively respond by voice ONLY use one tool call, do not output any text before or after the tool call"
        )
    ),
    server_url: str = Field(
        BASE_URL,
        description="The base URL of the Supertonic TTS server."
    ),
    request_timeout: int = Field(
        TIMEOUT,
        description="Timeout for API requests in seconds."
    )
) -> Dict[str, Any]:
    """
    Interfaces with the Supertonic TTS server to perform text-to-speech synthesis.

    Modes:
    - health: Checks the status of the TTS server.
    - synthesize: Converts a single piece of text into speech. Can save to a file, play back directly, or return as base64 data.
    - batch_synthesize: Converts multiple pieces of text into speech.
    """
    current_base_url = server_url.rstrip('/')
    
    try:
        with requests.Session() as session:
            session.timeout = request_timeout

            # --- HEALTH MODE ---
            if mode == 'health':
                response = session.get(f"{current_base_url}/health")
                response.raise_for_status()
                return response.json()

            # --- SYNTHESIZE MODE ---
            elif mode == 'synthesize':
                if not text:
                    raise ValueError("The 'text' parameter is required for 'synthesize' mode.")
                
                payload = {
                    "text": text,
                    "total_step": quality if quality is not None else DEFAULT_QUALITY,
                    "speed": speed if speed is not None else DEFAULT_SPEED,
                    "voice_style": _normalize_voice_style(voice_style or DEFAULT_VOICE)
                }

                response = session.post(f"{current_base_url}/synthesize", json=payload)
                response.raise_for_status()
                result = response.json()
                audio_bytes = base64.b64decode(result["audio_base64"])

                # Handle playback
                if playback:
                    temp_fd, temp_path = tempfile.mkstemp(suffix=f'.{DEFAULT_FORMAT}', dir=OUTPUT_DIR)
                    os.close(temp_fd)
                    
                    try:
                        _convert_audio_format(audio_bytes, temp_path)
                        playback_message = _play_audio(temp_path)
                        return {
                            "status": "success",
                            "message": f"Synthesis successful. {playback_message}",
                            "next_action": "The audio message has been sent to the user. Await the user's next input."
                        }
                    finally:
                        try:
                            os.unlink(temp_path)
                        except OSError:
                            pass # Ignore if file is already gone
                
                # Handle saving without playback
                if save_path:
                    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                    message = _convert_audio_format(audio_bytes, save_path)
                    return {"status": "success", "message": message, "file_path": save_path}
                
                # Default: return base64
                return {"status": "success", "audio_base64": result["audio_base64"]}

            # --- BATCH SYNTHESIZE MODE ---
            elif mode == 'batch_synthesize':
                if not texts:
                    raise ValueError("The 'texts' parameter is required for 'batch_synthesize' mode.")

                if voice_styles and len(texts) != len(voice_styles):
                    raise ValueError("Length of 'texts' and 'voice_styles' must match.")

                final_voices = voice_styles or ([voice_style or DEFAULT_VOICE] * len(texts))

                requests_list = [
                    {
                        "text": t,
                        "total_step": quality if quality is not None else DEFAULT_QUALITY,
                        "speed": speed if speed is not None else DEFAULT_SPEED,
                        "voice_style": _normalize_voice_style(v)
                    } for t, v in zip(texts, final_voices)
                ]

                payload = {"requests": requests_list}
                response = session.post(f"{current_base_url}/batch", json=payload)
                response.raise_for_status()
                results = response.json()["results"]

                if save_dir:
                    saved_files = []
                    Path(save_dir).mkdir(parents=True, exist_ok=True)
                    for i, item in enumerate(results):
                        audio_bytes = base64.b64decode(item["audio_base64"])
                        file_extension = f".{DEFAULT_FORMAT}"
                        output_file = Path(save_dir) / f"output_{i+1}{file_extension}"
                        _convert_audio_format(audio_bytes, str(output_file))
                        saved_files.append(str(output_file))
                    return {"status": "success", "message": f"Batch synthesis complete. Saved {len(saved_files)} files.", "file_paths": saved_files}
                else:
                    audio_list = [item["audio_base64"] for item in results]
                    return {"status": "success", "audio_base64_list": audio_list}

            else:
                raise ValueError(f"Invalid mode '{mode}'. Must be one of 'health', 'synthesize', 'batch_synthesize'.")

    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": f"Connection failed. Could not connect to the Supertonic server at {current_base_url}."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"An API request failed: {str(e)}"}
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
