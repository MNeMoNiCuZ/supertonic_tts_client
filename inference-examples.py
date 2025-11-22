"""
Supertonic TTS Inference Examples
Demonstrates various synthesis scenarios with updated features:
- Simplified voice names (M1 instead of M1.json)
- MP3 output support
- Different quality levels and speeds
- Configuration-driven defaults
"""

from inference import SupertonicClient, synthesize_text, OUTPUT_DIR
from pathlib import Path


def main():
    # Initialize client (uses .env BASE_URL by default)
    client = SupertonicClient()
    
    # Create output directory (use config default)
    output_dir = Path(OUTPUT_DIR) / "inference_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=== Supertonic TTS Inference Examples ===\n")
    
    # Example 1: Check service health
    print("1. Checking service health...")
    try:
        health = client.health()
        print(f"   Status: {health['status']}")
        print(f"   Model loaded: {health['model_loaded']}")
        print(f"   Available voices: {', '.join(health['available_voices'])}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure the Docker container is running!")
        return
    
    # Example 2: WAV output - Professional narration (M1)
    print("2. Professional narration → WAV (M1 - Deep, authoritative)...")
    try:
        text1 = "Welcome to this comprehensive guide on artificial intelligence. In this series, we explore fundamental concepts that power modern AI systems."
        client.synthesize(
            text=text1,
            voice_style="M1",  # Simplified - no .json needed
            total_step=5,
            speed=1.05,
            save_path=output_dir / "narration_professional.wav"
        )
        print("   ✓ Saved: narration_professional.wav")
        print("   → Voice: M1 (male, authoritative) | Quality: 5 | Speed: 1.05x\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Example 3: MP3 output - News announcement (F1)
    print("3. News announcement → MP3 (F1 - Professional, clear)...")
    try:
        text2 = "Breaking news from the technology sector. Scientists have announced a major breakthrough in quantum computing with unprecedented stability."
        client.synthesize(
            text=text2,
            voice_style="F1",  # Female professional
            total_step=10,     # High quality
            speed=1.0,
            save_path=output_dir / "news_announcement.mp3"  # MP3 format
        )
        print("   ✓ Saved: news_announcement.mp3")
        print("   → Voice: F1 (female, professional) | Quality: 10 | Format: MP3\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Example 4: Fast notification (F1)
    print("4. Quick notification → WAV (F1 - Fast, draft quality)...")
    try:
        text3 = "System maintenance will begin in fifteen minutes. Please save your work and log out."
        client.synthesize(
            text=text3,
            voice_style="F1",
            total_step=2,   # Draft quality for speed
            speed=1.4,      # Faster speech
            save_path=output_dir / "notification_fast.wav"
        )
        print("   ✓ Saved: notification_fast.wav")
        print("   → Voice: F1 | Quality: 2 (draft) | Speed: 1.4x (fast)\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Example 5: Educational content (F2)
    print("5. Educational content → WAV (F2 - Warm, slow and clear)...")
    try:
        text4 = "Let me explain photosynthesis. Plants convert sunlight into chemical energy by absorbing carbon dioxide and water, producing glucose and releasing oxygen."
        client.synthesize(
            text=text4,
            voice_style="F2",  # Warm, expressive
            total_step=8,      # High quality
            speed=0.85,        # Slower for comprehension
            save_path=output_dir / "education_slow.wav"
        )
        print("   ✓ Saved: education_slow.wav")
        print("   → Voice: F2 (female, warm) | Quality: 8 | Speed: 0.85x (slow)\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Example 6: Casual tutorial (M2)
    print("6. Casual tutorial → MP3 (M2 - Lighter male, conversational)...")
    try:
        text5 = "Hey everyone! Today we're going to learn how to build a simple web application. Don't worry if you're new to this, I'll walk you through each step."
        client.synthesize(
            text=text5,
            voice_style="M2",  # Casual male
            total_step=5,
            speed=1.15,        # Slightly faster
            save_path=output_dir / "tutorial_casual.mp3"
        )
        print("   ✓ Saved: tutorial_casual.mp3")
        print("   → Voice: M2 (male, casual) | Quality: 5 | Speed: 1.15x\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Example 7: Batch synthesis - Multi-voice dialogue
    print("7. Batch synthesis → Multiple voices (Dialogue scene)...")
    try:
        texts = [
            "In a small village, there lived a wise storyteller who captivated audiences every evening.",
            "The storyteller began: Once upon a time, in a land far beyond the horizon, magic and reality intertwined.",
            "A young listener asked eagerly: What happened next? Did the hero find the legendary treasure?"
        ]
        voices = [
            "M1",  # Narrator - authoritative
            "M2",  # Storyteller - casual
            "F2"   # Young listener - warm
        ]
        
        client.batch_synthesize(
            texts=texts,
            voice_styles=voices,
            total_step=5,
            speed=1.05,
            save_dir=output_dir / "dialogue_batch"
        )
        print("   ✓ Saved batch outputs to: dialogue_batch/")
        print("   → 3 voices: M1 (narrator), M2 (storyteller), F2 (listener)\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Example 8: Audiobook - Long-form content
    print("8. Audiobook → WAV (M1 - Extended narration)...")
    try:
        long_text = "Supertonic represents a significant advancement in text-to-speech technology. Unlike traditional cloud-based systems, it operates entirely on your local device, ensuring complete data privacy and eliminating network latency. The system achieves remarkable speed through ONNX Runtime, generating speech up to one hundred sixty-seven times faster than real-time. With only sixty-six million parameters, it maintains minimal computational footprint while delivering natural-sounding speech across multiple voice styles."
        client.synthesize(
            text=long_text,
            voice_style="M1",
            total_step=5,
            speed=1.05,
            save_path=output_dir / "audiobook_chapter.wav"
        )
        print("   ✓ Saved: audiobook_chapter.wav")
        print("   → Voice: M1 | Quality: 5 | Long-form content\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Example 9: High-quality production (F1 → MP3)
    print("9. High-quality production → MP3 (F1 - Studio quality)...")
    try:
        text6 = "This premium audio content has been synthesized at maximum quality settings for professional distribution and archival purposes."
        client.synthesize(
            text=text6,
            voice_style="F1",
            total_step=20,  # Maximum quality
            speed=1.0,
            save_path=output_dir / "production_hq.mp3"
        )
        print("   ✓ Saved: production_hq.mp3")
        print("   → Voice: F1 | Quality: 20 (maximum) | Format: MP3\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Close the client
    client.close()
    
    print("=== All examples completed! ===")
    print(f"\nOutput directory: {output_dir.absolute()}")
    print("\nExamples created:")
    print("  1. Health check - Server status")
    print("  2. Professional narration (M1) → WAV")
    print("  3. News announcement (F1) → MP3")
    print("  4. Fast notification (F1, draft quality)")
    print("  5. Educational content (F2, slow speech)")
    print("  6. Casual tutorial (M2) → MP3")
    print("  7. Batch dialogue (M1, M2, F2)")
    print("  8. Audiobook chapter (M1, long-form)")
    print("  9. High-quality production (F1, quality 20) → MP3")
    print("\n💡 Tips:")
    print("  • Use quality 2-5 for fast iteration")
    print("  • Use quality 10-20 for final production")
    print("  • MP3 format requires: pip install audioop-lts")
    print("  • Voice names work with or without .json extension")


if __name__ == "__main__":
    main()
