import base64
import requests
import argparse
import sys
import tempfile
import os
import time
from typing import Optional, List, Tuple
from pathlib import Path

# Try to import audio playback libraries
try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_BACKEND = 'sounddevice'
except ImportError:
    try:
        import winsound
        AUDIO_BACKEND = 'winsound'
    except ImportError:
        AUDIO_BACKEND = None

# Try to import pydub for audio format conversion
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
    PYDUB_IMPORT_ERROR = None
except ImportError as e:
    PYDUB_AVAILABLE = False
    PYDUB_IMPORT_ERROR = str(e)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - Load from .env file
# ═══════════════════════════════════════════════════════════════════════════════

def _load_env():
    """Load .env file if it exists"""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        # Manually parse .env if python-dotenv not installed
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key, value = key.strip(), value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    if key not in os.environ:
                        os.environ[key] = value

# Load environment variables
_load_env()

# Get configuration values with defaults
def _get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default)

def _get_env_int(key: str, default: int) -> int:
    value = os.getenv(key)
    return int(value) if value and value != "" else default

def _get_env_float(key: str, default: float) -> float:
    value = os.getenv(key)
    return float(value) if value and value != "" else default

# Configuration constants
BASE_URL = _get_env('BASE_URL', 'http://localhost:8765')
TIMEOUT = _get_env_int('TIMEOUT', 30)
DEFAULT_VOICE = _get_env('DEFAULT_VOICE', 'M1')
DEFAULT_QUALITY = _get_env_int('DEFAULT_QUALITY', 5)
DEFAULT_SPEED = _get_env_float('DEFAULT_SPEED', 1.05)
DEFAULT_FORMAT = _get_env('DEFAULT_FORMAT', 'wav')
TEMP_DIR = _get_env('TEMP_DIR', '') or None
OUTPUT_DIR = _get_env('OUTPUT_DIR', 'output')

# Create directories if specified
if TEMP_DIR:
    os.makedirs(TEMP_DIR, exist_ok=True)
if OUTPUT_DIR:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def normalize_voice_style(voice: Optional[str]) -> Optional[str]:
    """
    Normalize voice style name by adding .json extension if missing
    
    Args:
        voice: Voice style name (e.g., "M1", "M1.json", "F1", etc.)
        
    Returns:
        Normalized voice style with .json extension, or None if input is None
    """
    if voice is None:
        return None
    
    # Add .json extension if not present
    if not voice.endswith('.json'):
        return f"{voice}.json"
    
    return voice


def convert_audio_format(wav_data: bytes, output_path: str) -> None:
    """
    Convert WAV audio data to the format specified by output_path extension
    
    Args:
        wav_data: WAV audio data as bytes
        output_path: Output file path (extension determines format)
        
    Raises:
        ImportError: If pydub is not installed for non-WAV formats
    """
    output_path = Path(output_path)
    extension = output_path.suffix.lower()
    
    # If WAV, just write directly
    if extension == '.wav':
        output_path.write_bytes(wav_data)
        return
    
    # For other formats, need pydub
    if not PYDUB_AVAILABLE:
        error_msg = f"Converting to {extension} format requires pydub. Install with:\n  pip install pydub\n"
        if PYDUB_IMPORT_ERROR:
            error_msg += f"\nActual import error: {PYDUB_IMPORT_ERROR}\n"
        error_msg += (
            "For MP3 support, you also need ffmpeg:\n"
            "  Windows: choco install ffmpeg  OR  download from https://ffmpeg.org/\n"
            "  Linux: sudo apt-get install ffmpeg\n"
            "  Mac: brew install ffmpeg"
        )
        raise ImportError(error_msg)
    
    # Create temp WAV file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
        temp_wav.write(wav_data)
        temp_wav_path = temp_wav.name
    
    try:
        # Load WAV and convert to target format
        audio = AudioSegment.from_wav(temp_wav_path)
        
        # Export based on extension
        format_name = extension[1:]  # Remove the dot
        
        # MP3-specific settings for better quality
        if format_name == 'mp3':
            audio.export(str(output_path), format='mp3', bitrate='192k')
        else:
            audio.export(str(output_path), format=format_name)
    
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_wav_path)
        except:
            pass


class SupertonicClient:
    """Client for Supertonic TTS API"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the TTS service (default: from .env BASE_URL)
        """
        self.base_url = (base_url or BASE_URL).rstrip('/')
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
    
    def health(self) -> dict:
        """
        Check service health
        
        Returns:
            dict: Health status information
        """
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def synthesize(
        self,
        text: str,
        voice_style: Optional[str] = None,
        total_step: Optional[int] = None,
        speed: Optional[float] = None,
        save_path: Optional[str] = None
    ) -> bytes:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            voice_style: Voice style filename (e.g., "M1", "F2") (default: from config)
            total_step: Number of denoising steps (1-20, higher = better quality) (default: from config)
            speed: Speech speed factor (0.5-2.0, higher = faster) (default: from config)
            save_path: Optional path to save audio file (.wav, .mp3, etc.)
                      Format is auto-detected from file extension
        
        Returns:
            bytes: WAV audio data
        """
        # Apply config defaults
        if voice_style is None:
            voice_style = DEFAULT_VOICE
        if total_step is None:
            total_step = DEFAULT_QUALITY
        if speed is None:
            speed = DEFAULT_SPEED
        payload = {
            "text": text,
            "total_step": total_step,
            "speed": speed
        }
        
        if voice_style:
            payload["voice_style"] = normalize_voice_style(voice_style)
        
        response = self.session.post(
            f"{self.base_url}/synthesize",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        audio_bytes = base64.b64decode(result["audio_base64"])
        
        if save_path:
            convert_audio_format(audio_bytes, save_path)
            print(f"Saved audio to: {save_path}")
        
        return audio_bytes
    
    def batch_synthesize(
        self,
        texts: List[str],
        voice_styles: Optional[List[Optional[str]]] = None,
        total_step: Optional[int] = None,
        speed: Optional[float] = None,
        save_dir: Optional[str] = None
    ) -> List[bytes]:
        """
        Batch synthesize multiple texts
        
        Args:
            texts: List of texts to synthesize
            voice_styles: Optional list of voice style filenames (must match length of texts)
            total_step: Number of denoising steps (1-20, higher = better quality) (default: from config)
            speed: Speech speed factor (0.5-2.0, higher = faster) (default: from config)
            save_dir: Optional directory to save WAV files
        
        Returns:
            List[bytes]: List of WAV audio data
        """
        # Apply config defaults
        if total_step is None:
            total_step = DEFAULT_QUALITY
        if speed is None:
            speed = DEFAULT_SPEED
        if voice_styles is None:
            voice_styles = [None] * len(texts)
        
        if len(texts) != len(voice_styles):
            raise ValueError("Length of texts and voice_styles must match")
        
        requests_list = []
        for text, voice_style in zip(texts, voice_styles):
            req = {
                "text": text,
                "total_step": total_step,
                "speed": speed
            }
            if voice_style:
                req["voice_style"] = normalize_voice_style(voice_style)
            requests_list.append(req)
        
        payload = {"requests": requests_list}
        
        response = self.session.post(
            f"{self.base_url}/batch",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        audio_list = []
        
        for i, item in enumerate(result["results"]):
            audio_bytes = base64.b64decode(item["audio_base64"])
            audio_list.append(audio_bytes)
            
            if save_dir:
                save_path = Path(save_dir) / f"output_{i+1}.wav"
                save_path.parent.mkdir(parents=True, exist_ok=True)
                convert_audio_format(audio_bytes, str(save_path))
                print(f"Saved audio {i+1} to: {save_path}")
        
        return audio_list
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function
def synthesize_text(
    text: str,
    save_path: str,
    base_url: Optional[str] = None,
    **kwargs
) -> bytes:
    """
    Convenience function to synthesize text and save to file
    
    Args:
        text: Text to synthesize
        save_path: Path to save the WAV file
        base_url: Base URL of the TTS service (default: from .env)
        **kwargs: Additional arguments passed to synthesize()
    
    Returns:
        bytes: WAV audio data
    """
    with SupertonicClient(base_url) as client:
        return client.synthesize(text, save_path=save_path, **kwargs)


def play_audio(audio_path: str) -> bool:
    """
    Play audio file using available backend
    
    Args:
        audio_path: Path to WAV file
        
    Returns:
        bool: True if playback succeeded, False otherwise
    """
    if AUDIO_BACKEND == 'sounddevice':
        try:
            data, samplerate = sf.read(audio_path)
            sd.play(data, samplerate)
            sd.wait()  # Wait until playback is finished
            return True
        except Exception as e:
            print(f"Playback error (sounddevice): {e}", file=sys.stderr)
            return False
    
    elif AUDIO_BACKEND == 'winsound':
        try:
            import winsound
            winsound.PlaySound(audio_path, winsound.SND_FILENAME)
            return True
        except Exception as e:
            print(f"Playback error (winsound): {e}", file=sys.stderr)
            return False
    
    else:
        print("Audio playback not available. Install sounddevice and soundfile:", file=sys.stderr)
        print("  pip install sounddevice soundfile", file=sys.stderr)
        return False


def main():
    """Command-line interface for Supertonic TTS client"""
    parser = argparse.ArgumentParser(
        description="Supertonic TTS Client - Synthesize speech from text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Hello world" -o hello.wav
  %(prog)s "Hello world" -o hello.mp3
  %(prog)s "Test" -v F1 -q 10 -s 1.2 -o test.wav
  %(prog)s "Listen to this" -p
  %(prog)s "Listen to this" --play
  %(prog)s --health
  %(prog)s "Remote" -u http://192.168.1.100:8765 -o out.mp3
        """
    )
    
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to synthesize"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output WAV file path (optional if --play is used)"
    )
    
    parser.add_argument(
        "-v", "--voice",
        default=DEFAULT_VOICE,
        help=f"Voice style: M1, M2, F1, F2 (.json extension optional) (default: {DEFAULT_VOICE})"
    )
    
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        help=f"Quality: denoising steps 1-20, higher=better (default: {DEFAULT_QUALITY})"
    )
    
    parser.add_argument(
        "-s", "--speed",
        type=float,
        default=DEFAULT_SPEED,
        help=f"Speech speed 0.5-2.0, higher=faster (default: {DEFAULT_SPEED})"
    )
    
    parser.add_argument(
        "-u", "--url",
        default=BASE_URL,
        help=f"Server URL (default: {BASE_URL})"
    )
    
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check server health and exit (no short form, -h is reserved for help)"
    )
    
    parser.add_argument(
        "-p", "--play",
        action="store_true",
        help="Play audio immediately after generation (saves to temp file if no -o specified)"
    )
    
    args = parser.parse_args()
    
    # Initialize client
    client = SupertonicClient(base_url=args.url)
    
    try:
        # Health check mode
        if args.health:
            print("Checking server health...")
            health = client.health()
            print(f"Status: {health['status']}")
            print(f"Model loaded: {health['model_loaded']}")
            print(f"Default voice: {health['default_voice']}")
            print(f"Available voices: {', '.join(health['available_voices'])}")
            return 0
        
        # Synthesis mode
        if not args.text:
            parser.error("text is required unless --health is specified")
                
        # Determine output path
        use_temp = False
        if args.output:
            output_path = args.output
        elif args.play:
            suffix = f".{DEFAULT_FORMAT.lower()}"
            temp_fd, output_path = tempfile.mkstemp(
                suffix=suffix,
                prefix='supertonic_',
                dir=TEMP_DIR
            )
            os.close(temp_fd)
            use_temp = True
        else:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            import time
            timestamp = int(time.time() * 1000)
            output_path = os.path.join(OUTPUT_DIR, f"supertonic_{timestamp}.{DEFAULT_FORMAT.lower()}")

        
        # Validate parameters
        if args.quality < 1 or args.quality > 20:
            parser.error("quality must be between 1 and 20")
        
        if args.speed < 0.5 or args.speed > 2.0:
            parser.error("speed must be between 0.5 and 2.0")
        
        print(f"Synthesizing: '{args.text[:50]}{'...' if len(args.text) > 50 else ''}'")
        print(f"Voice: {args.voice or 'M1.json (default)'}")
        print(f"Quality: {args.quality} steps")
        print(f"Speed: {args.speed}x")
        
        # Synthesize
        client.synthesize(
            text=args.text,
            voice_style=normalize_voice_style(args.voice),
            total_step=args.quality,
            speed=args.speed,
            save_path=output_path
        )
        
        if not use_temp:
            print(f"✓ Saved to: {output_path}")
        
        # Play audio if requested
        if args.play:
            print("▶ Playing audio...")
            if play_audio(output_path):
                print("✓ Playback complete")
            else:
                print("✗ Playback failed", file=sys.stderr)
            
            # Clean up temp file
            if use_temp:
                try:
                    os.unlink(output_path)
                except:
                    pass
        
        return 0
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to server at {args.url}", file=sys.stderr)
        print("Make sure the Docker container is running:", file=sys.stderr)
        print("  docker-compose up -d", file=sys.stderr)
        return 1
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
