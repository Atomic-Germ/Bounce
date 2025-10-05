#!/usr/bin/env python3
"""
Assemble Final Video
Trims scenes according to the alignment plan and combines with music.
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path


def load_scene_plan(plan_file):
    """
    Load the scene alignment plan.
    
    Returns:
        List of dicts with scene information
    """
    scenes = []
    
    with open(plan_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse CSV format
            try:
                parts = [p.strip() for p in line.split(',')]
                
                # Handle both old format (6 fields) and new format (9 fields)
                if len(parts) >= 9:
                    # New format with splitting support
                    scene_info = {
                        'file': parts[0],
                        'part': int(parts[1]),
                        'total_parts': int(parts[2]),
                        'start_offset': float(parts[3]),
                        'original_duration': float(parts[4]),
                        'trim_to': float(parts[5]),
                        'measure_number': int(parts[6]),
                        'measure_time': float(parts[7]),
                        'time_lost': float(parts[8])
                    }
                elif len(parts) >= 6:
                    # Old format (backward compatibility)
                    scene_info = {
                        'file': parts[0],
                        'part': 1,
                        'total_parts': 1,
                        'start_offset': 0.0,
                        'original_duration': float(parts[1]),
                        'trim_to': float(parts[2]),
                        'measure_number': int(parts[3]),
                        'measure_time': float(parts[4]),
                        'time_lost': float(parts[5])
                    }
                else:
                    continue
                    
                scenes.append(scene_info)
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse line: {line}")
                continue
    
    return scenes


def trim_scene(scene_path, duration, output_path, start_offset=0.0):
    """
    Trim a scene to the specified duration, optionally starting from an offset.
    
    Args:
        scene_path: Path to input scene file
        duration: Duration to trim to in seconds
        output_path: Path for trimmed output
        start_offset: Start time offset in seconds (for splitting long scenes)
    """
    cmd = [
        "ffmpeg",
        "-i", scene_path,
        "-ss", str(start_offset),  # Start from offset
        "-t", str(duration),        # Duration
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-an",  # Keep it silent
        "-y",
        output_path
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)


def concatenate_videos(video_files, output_path):
    """
    Concatenate multiple video files.
    
    Args:
        video_files: List of video file paths
        output_path: Path for concatenated output
    """
    # Create concat file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        concat_file = f.name
        for video in video_files:
            abs_path = os.path.abspath(video)
            # Escape single quotes for FFmpeg
            escaped_path = abs_path.replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    
    try:
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-an",  # No audio yet
            "-y",
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
    finally:
        os.unlink(concat_file)


def add_audio(video_path, audio_path, output_path):
    """
    Add audio track to video.
    
    Trims video to match audio duration if needed.
    
    Args:
        video_path: Path to silent video
        audio_path: Path to audio file
        output_path: Path for final output
    """
    # Get audio duration
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    audio_duration = float(result.stdout.strip())
    
    # Get video duration
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    video_duration = float(result.stdout.strip())
    
    # If video is longer than audio, we need to trim it during encoding
    if video_duration > audio_duration + 0.1:
        print(f"  Trimming video from {video_duration:.2f}s to {audio_duration:.2f}s")
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v:0",  # Video from first input
            "-map", "1:a:0",  # Audio from second input
            "-t", str(audio_duration),  # Trim to audio duration
            "-c:v", "libx264",  # Must re-encode to trim
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",    # Encode audio as AAC for MP4
            "-b:a", "192k",   # Audio bitrate
            "-y",
            output_path
        ]
    else:
        # Video is equal or shorter, can use copy
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v:0",  # Video from first input
            "-map", "1:a:0",  # Audio from second input
            "-c:v", "copy",   # Copy video
            "-c:a", "aac",    # Encode audio as AAC for MP4
            "-b:a", "192k",   # Audio bitrate
            "-shortest",      # Stop at shortest stream
            "-y",
            output_path
        ]
    
    subprocess.run(cmd, capture_output=True, check=True)


def assemble_video(scenes_dir, plan_file, audio_file, output_file="output.mp4"):
    """
    Main assembly function.
    
    Args:
        scenes_dir: Directory containing scene clips
        plan_file: Scene alignment plan file
        audio_file: Audio/music file to add
        output_file: Final output video file
    """
    print("🎬 Bounce - Final Video Assembly")
    print("=" * 70)
    
    # Load the scene plan
    print(f"\n📋 Loading scene plan from: {plan_file}")
    scenes = load_scene_plan(plan_file)
    print(f"✓ Loaded plan for {len(scenes)} scenes")
    
    # Create temporary directory for trimmed scenes
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n✂️  Trimming scenes to align with measures...")
        
        trimmed_files = []
        
        for i, scene in enumerate(scenes, 1):
            scene_path = os.path.join(scenes_dir, scene['file'])
            trimmed_path = os.path.join(temp_dir, f"trimmed_{i:04d}.mp4")
            
            part_info = f" (part {scene['part']}/{scene['total_parts']})" if scene['total_parts'] > 1 else ""
            offset_info = f" from {scene['start_offset']:.2f}s" if scene['start_offset'] > 0 else ""
            
            print(f"  Scene {i:2d}: {scene['file']}{part_info}{offset_info} - "
                  f"{scene['original_duration']:.2f}s → {scene['trim_to']:.2f}s")
            
            trim_scene(scene_path, scene['trim_to'], trimmed_path, scene['start_offset'])
            trimmed_files.append(trimmed_path)
        
        print(f"✓ Trimmed {len(trimmed_files)} scenes")
        
        # Concatenate all trimmed scenes
        print(f"\n🎞️  Concatenating trimmed scenes...")
        concatenated_path = os.path.join(temp_dir, "concatenated.mp4")
        concatenate_videos(trimmed_files, concatenated_path)
        print(f"✓ Concatenated into single video")
        
        # Add audio track
        print(f"\n🎵 Adding audio track: {audio_file}")
        add_audio(concatenated_path, audio_file, output_file)
        print(f"✓ Added audio track")
    
    # Get final file info
    file_size = os.path.getsize(output_file) / (1024 * 1024)
    
    # Get duration
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        output_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = float(result.stdout.strip())
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS! Final video created!")
    print("=" * 70)
    print(f"📄 Output file: {output_file}")
    print(f"📊 File size:   {file_size:.2f} MB")
    print(f"⏱️  Duration:    {duration:.2f} seconds")
    print("=" * 70)
    
    print("\n🎉 Your beat-synchronized music video is ready!")
    print(f"\nThe video contains {len(scenes)} scenes, each trimmed to align")
    print(f"with musical measure boundaries for perfect synchronization.")


def main():
    if len(sys.argv) < 4:
        print("Usage: python assemble_video.py <scenes_dir> <plan_file> <audio_file> [output_file]")
        print("\nArguments:")
        print("  scenes_dir  - Directory containing scene MP4 files")
        print("  plan_file   - Scene alignment plan (from align_scenes.py)")
        print("  audio_file  - Audio/music file to add to the video")
        print("  output_file - Output video file (default: output.mp4)")
        print("\nExample:")
        print("  python assemble_video.py scenes scene_plan.txt example/mp3/Example.mp3")
        print("  python assemble_video.py scenes scene_plan.txt example/mp3/Example.mp3 final_video.mp4")
        sys.exit(1)
    
    scenes_dir = sys.argv[1]
    plan_file = sys.argv[2]
    audio_file = sys.argv[3]
    output_file = sys.argv[4] if len(sys.argv) > 4 else "output.mp4"
    
    # Validate inputs
    if not os.path.exists(scenes_dir):
        print(f"❌ Error: Scenes directory not found: {scenes_dir}")
        sys.exit(1)
    
    if not os.path.exists(plan_file):
        print(f"❌ Error: Plan file not found: {plan_file}")
        sys.exit(1)
    
    if not os.path.exists(audio_file):
        print(f"❌ Error: Audio file not found: {audio_file}")
        sys.exit(1)
    
    try:
        assemble_video(scenes_dir, plan_file, audio_file, output_file)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ FFmpeg Error: {e}")
        print("Check that FFmpeg is installed and the input files are valid.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
