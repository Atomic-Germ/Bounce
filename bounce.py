#!/usr/bin/env python3
"""
Bounce - Video Music Mixer
Combines MP4 video clips with an MP3 audio track
"""

import os
import sys
import subprocess
import json
import tempfile
from pathlib import Path


def get_video_files(folder_path):
    """Get all MP4 files from the specified folder, sorted alphabetically."""
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"Invalid folder path: {folder_path}")
    
    video_files = sorted(folder.glob("*.mp4")) + sorted(folder.glob("*.MP4"))
    
    if not video_files:
        raise ValueError(f"No MP4 files found in {folder_path}")
    
    return [str(f) for f in video_files]


def get_duration(file_path):
    """Get duration of a media file in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception as e:
        raise RuntimeError(f"Failed to get duration for {file_path}: {e}")


def concatenate_videos(video_files, output_path):
    """Concatenate multiple video files into one."""
    # Create a temporary file list for ffmpeg concat
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        concat_file = f.name
        for video in video_files:
            # Convert to absolute path and escape single quotes
            abs_path = os.path.abspath(video)
            escaped_path = abs_path.replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    
    try:
        # Try copy first for speed, fallback to re-encode if needed
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Copy failed, likely due to incompatible codecs/parameters
            # Re-encode to ensure compatibility
            print("  ⚠ Videos have different parameters, re-encoding...")
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                "-y",
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                raise RuntimeError(f"FFmpeg concatenation failed")
        
        print(f"✓ Concatenated {len(video_files)} video clips")
    finally:
        os.unlink(concat_file)


def adjust_video_speed(input_video, target_duration, output_path):
    """Adjust video speed to match target duration."""
    current_duration = get_duration(input_video)
    speed_factor = current_duration / target_duration
    
    if abs(speed_factor - 1.0) < 0.01:
        # Duration is close enough, just copy
        subprocess.run([
            "ffmpeg", "-i", input_video,
            "-c", "copy", "-y", output_path
        ], check=True, capture_output=True)
        print(f"✓ Video duration matches audio (no speed adjustment needed)")
    else:
        # Adjust speed using setpts filter for video
        if speed_factor > 1:
            print(f"✓ Speeding up video by {speed_factor:.2f}x to match audio duration")
        else:
            print(f"✓ Slowing down video by {1/speed_factor:.2f}x to match audio duration")
        
        cmd = [
            "ffmpeg",
            "-i", input_video,
            "-filter:v", f"setpts={1/speed_factor:.6f}*PTS",
            "-an",  # Remove audio from video
            "-y",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)


def combine_video_audio(video_path, audio_path, output_path):
    """Combine video with audio track."""
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "-y",
        output_path
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"✓ Combined video with audio track")


def create_video_with_music(audio_file, video_folder, output_file="output.mp4"):
    """Main function to create video with music."""
    print("🎬 Bounce - Video Music Mixer")
    print("=" * 50)
    
    # Validate inputs
    if not os.path.exists(audio_file):
        raise ValueError(f"Audio file not found: {audio_file}")
    
    print(f"Audio file: {audio_file}")
    print(f"Video folder: {video_folder}")
    print(f"Output file: {output_file}")
    print()
    
    # Get video files
    print("📁 Scanning for video files...")
    video_files = get_video_files(video_folder)
    print(f"✓ Found {len(video_files)} video file(s):")
    for i, vf in enumerate(video_files, 1):
        print(f"   {i}. {Path(vf).name}")
    print()
    
    # Get audio duration
    print("🎵 Analyzing audio duration...")
    audio_duration = get_duration(audio_file)
    print(f"✓ Audio duration: {audio_duration:.2f} seconds")
    print()
    
    # Create temporary files
    with tempfile.TemporaryDirectory() as temp_dir:
        concat_video = os.path.join(temp_dir, "concatenated.mp4")
        adjusted_video = os.path.join(temp_dir, "adjusted.mp4")
        
        # Step 1: Concatenate videos
        print("🎞️  Concatenating video clips...")
        concatenate_videos(video_files, concat_video)
        
        # Get concatenated video duration
        concat_duration = get_duration(concat_video)
        print(f"✓ Total video duration: {concat_duration:.2f} seconds")
        print()
        
        # Step 2: Adjust video speed to match audio
        print("⚡ Adjusting video timing...")
        adjust_video_speed(concat_video, audio_duration, adjusted_video)
        print()
        
        # Step 3: Combine with audio
        print("🎶 Adding audio track...")
        combine_video_audio(adjusted_video, audio_file, output_file)
    
    print()
    print("=" * 50)
    print(f"✅ Success! Video created: {output_file}")
    
    # Show final file size
    file_size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"📊 File size: {file_size:.2f} MB")


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python bounce.py <audio.mp3> <videos_folder> [output.mp4]")
        print()
        print("Arguments:")
        print("  audio.mp3      - Path to your MP3 audio file")
        print("  videos_folder  - Path to folder containing MP4 video files")
        print("  output.mp4     - (Optional) Output file name (default: output.mp4)")
        print()
        print("Example:")
        print("  python bounce.py music.mp3 ./clips/ final_video.mp4")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    video_folder = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "output.mp4"
    
    try:
        create_video_with_music(audio_file, video_folder, output_file)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
