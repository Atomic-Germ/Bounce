#!/usr/bin/env python3
"""
Beat Detection Script
Detects beats in an audio file and outputs timestamps to a text file.
"""

import sys
import librosa
import numpy as np


def detect_beats(audio_file, output_file="beats.txt"):
    """
    Detect beats in an audio file and save timestamps to a text file.
    
    Args:
        audio_file: Path to audio file (MP3, WAV, etc.)
        output_file: Path to output text file for beat timestamps
    
    Returns:
        Array of beat times in seconds
    """
    print(f"Loading audio file: {audio_file}")
    
    # Load the audio file
    y, sr = librosa.load(audio_file)
    
    print(f"✓ Audio loaded: {len(y) / sr:.2f} seconds, sample rate: {sr} Hz")
    
    # Detect beats
    print("Detecting beats...")
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    
    # Convert beat frames to time in seconds
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    # Handle tempo (can be array or scalar)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0]) if len(tempo) > 0 else 0.0
    else:
        tempo = float(tempo)
    
    print(f"✓ Detected {len(beat_times)} beats")
    print(f"✓ Estimated tempo: {tempo:.1f} BPM")
    
    # Calculate average beat interval
    if len(beat_times) > 1:
        intervals = np.diff(beat_times)
        avg_interval = np.mean(intervals)
        calculated_bpm = 60.0 / avg_interval
        print(f"✓ Calculated BPM from intervals: {calculated_bpm:.1f}")
    
    # Save beat times to text file
    print(f"\nSaving beat timestamps to: {output_file}")
    with open(output_file, 'w') as f:
        f.write(f"# Beat timestamps for: {audio_file}\n")
        f.write(f"# Detected {len(beat_times)} beats at {tempo:.1f} BPM\n")
        f.write(f"# Format: beat_number, timestamp_seconds\n")
        f.write("#\n")
        
        for i, beat_time in enumerate(beat_times, 1):
            f.write(f"{i}, {beat_time:.6f}\n")
    
    print(f"✓ Saved {len(beat_times)} beat timestamps")
    
    # Print first 10 beats
    print("\nFirst 10 beats:")
    for i, beat_time in enumerate(beat_times[:10], 1):
        print(f"  Beat {i:3d}: {beat_time:7.3f}s")
    
    if len(beat_times) > 10:
        print(f"  ... and {len(beat_times) - 10} more beats")
    
    return beat_times


def main():
    if len(sys.argv) < 2:
        print("Usage: python detect_beats.py <audio_file> [output_file]")
        print("\nExample:")
        print("  python detect_beats.py example/mp3/Example.mp3")
        print("  python detect_beats.py example/mp3/Example.mp3 my_beats.txt")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "beats.txt"
    
    try:
        beat_times = detect_beats(audio_file, output_file)
        print(f"\n✅ Success! Beat detection complete.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
