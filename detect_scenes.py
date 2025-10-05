#!/usr/bin/env python3
"""
Scene Detection Script
Detects scene changes in a video and splits it into separate silent MP4 clips.
"""

import sys
import os
import subprocess
import json
from pathlib import Path


def get_duration(video_file):
    """Get duration of a video file in seconds."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def detect_scene_changes(video_file, threshold=0.3):
    """
    Detect scene changes in a video file using FFmpeg's scene detection.
    The scene filter calculates the difference between consecutive frames.
    
    Args:
        video_file: Path to video file
        threshold: Scene detection threshold (0.0-1.0, lower=more sensitive)
                  Default 0.3 works for most hard cuts
    
    Returns:
        List of scene change timestamps in seconds
    """
    print(f"Analyzing video: {video_file}")
    print(f"Scene detection threshold: {threshold}")
    print("  (Lower = more sensitive to changes)")
    
    # Get video duration
    duration = get_duration(video_file)
    print(f"✓ Video duration: {duration:.2f} seconds")
    
    print("\nDetecting scene changes (this may take a while)...")
    
    # Use ffmpeg's scene filter with showinfo to get pts_time values
    # The select filter only passes frames where scene > threshold
    cmd = [
        "ffmpeg",
        "-i", video_file,
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-vsync", "vfr",
        "-f", "null",
        "-"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse scene change times from showinfo output (in stderr)
    scene_times = [0.0]  # Always start at 0
    
    for line in result.stderr.split('\n'):
        # Look for showinfo lines with pts_time
        if 'Parsed_showinfo' in line and 'pts_time:' in line:
            try:
                # Extract pts_time value
                # Format: ... pts_time:146.112633 ...
                parts = line.split('pts_time:')
                if len(parts) > 1:
                    time_str = parts[1].split()[0]
                    scene_time = float(time_str)
                    if scene_time > 0.1:  # Ignore very early detections
                        scene_times.append(scene_time)
            except (ValueError, IndexError):
                continue
    
    # Remove duplicates and sort
    scene_times = sorted(set(scene_times))
    
    print(f"✓ Initial detection: {len(scene_times)} scene changes")
    
    # If very few scenes detected, try with lower threshold
    if len(scene_times) <= 3:
        print(f"\n  Few scenes detected, trying with lower threshold ({threshold * 0.6:.2f})...")
        lower_threshold = threshold * 0.6
        
        cmd = [
            "ffmpeg",
            "-i", video_file,
            "-vf", f"select='gt(scene,{lower_threshold})',showinfo",
            "-vsync", "vfr",
            "-f", "null",
            "-"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        scene_times = [0.0]
        for line in result.stderr.split('\n'):
            if 'Parsed_showinfo' in line and 'pts_time:' in line:
                try:
                    parts = line.split('pts_time:')
                    if len(parts) > 1:
                        time_str = parts[1].split()[0]
                        scene_time = float(time_str)
                        if scene_time > 0.1:
                            scene_times.append(scene_time)
                except (ValueError, IndexError):
                    continue
        
        scene_times = sorted(set(scene_times))
        print(f"  ✓ With lower threshold: {len(scene_times)} scene changes")
    
    # If still too few, try an even more aggressive threshold
    if len(scene_times) <= 3:
        print(f"\n  Still few scenes, trying very sensitive threshold (0.15)...")
        
        cmd = [
            "ffmpeg",
            "-i", video_file,
            "-vf", "select='gt(scene,0.15)',showinfo",
            "-vsync", "vfr",
            "-f", "null",
            "-"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        scene_times = [0.0]
        for line in result.stderr.split('\n'):
            if 'Parsed_showinfo' in line and 'pts_time:' in line:
                try:
                    parts = line.split('pts_time:')
                    if len(parts) > 1:
                        time_str = parts[1].split()[0]
                        scene_time = float(time_str)
                        if scene_time > 0.1:
                            scene_times.append(scene_time)
                except (ValueError, IndexError):
                    continue
        
        scene_times = sorted(set(scene_times))
        print(f"  ✓ With very sensitive threshold: {len(scene_times)} scene changes")
    
    return scene_times, duration


def split_video_into_scenes(video_file, scene_times, duration, output_dir):
    """
    Split video into separate clips at scene change points.
    
    Args:
        video_file: Path to input video
        scene_times: List of scene change timestamps
        duration: Total video duration
        output_dir: Directory to save scene clips
    
    Returns:
        List of paths to created scene clip files
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nSplitting video into {len(scene_times)} scenes...")
    print(f"Output directory: {output_dir}")
    
    scene_files = []
    
    for i in range(len(scene_times)):
        start_time = scene_times[i]
        end_time = scene_times[i + 1] if i + 1 < len(scene_times) else duration
        scene_duration = end_time - start_time
        
        # Skip very short scenes (< 0.2 seconds)
        if scene_duration < 0.2:
            print(f"  Skipping scene {i+1} (too short: {scene_duration:.2f}s)")
            continue
        
        scene_file = os.path.join(output_dir, f"scene_{i+1:04d}.mp4")
        
        print(f"  Creating scene {i+1}: {start_time:.2f}s - {end_time:.2f}s ({scene_duration:.2f}s)")
        
        # Extract scene with no audio
        cmd = [
            "ffmpeg",
            "-i", video_file,
            "-ss", str(start_time),
            "-t", str(scene_duration),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-an",  # Remove audio
            "-avoid_negative_ts", "1",
            "-y",
            scene_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            scene_files.append(scene_file)
        else:
            print(f"    ⚠ Warning: Failed to create scene {i+1}")
    
    print(f"\n✓ Created {len(scene_files)} scene clips")
    
    return scene_files


def main():
    if len(sys.argv) < 2:
        print("Usage: python detect_scenes.py <video_file> [output_dir] [threshold]")
        print("\nArguments:")
        print("  video_file  - Path to input video file")
        print("  output_dir  - Directory for scene clips (default: scenes/)")
        print("  threshold   - Scene detection sensitivity 0.0-1.0 (default: 0.3)")
        print("\nExample:")
        print("  python detect_scenes.py example/Example.mp4")
        print("  python detect_scenes.py example/Example.mp4 my_scenes 0.4")
        sys.exit(1)
    
    video_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "scenes"
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3
    
    if not os.path.exists(video_file):
        print(f"❌ Error: Video file not found: {video_file}")
        sys.exit(1)
    
    try:
        # Detect scene changes
        scene_times, duration = detect_scene_changes(video_file, threshold)
        
        if len(scene_times) <= 1:
            print("\n⚠ No scene changes detected!")
            print("  The video appears to be a single continuous shot.")
            print("  Try lowering the threshold (e.g., 0.2 or 0.1)")
            sys.exit(0)
        
        # Split into scene clips
        scene_files = split_video_into_scenes(video_file, scene_times, duration, output_dir)
        
        # Print summary
        print("\n" + "="*60)
        print("✅ Scene detection complete!")
        print(f"   Detected scenes: {len(scene_times)}")
        print(f"   Created clips:   {len(scene_files)}")
        print(f"   Output dir:      {output_dir}")
        print("="*60)
        
        # Show scene durations
        print("\nScene durations:")
        for i, scene_file in enumerate(scene_files[:10], 1):
            scene_duration = get_duration(scene_file)
            print(f"  Scene {i:2d}: {scene_duration:6.2f}s - {Path(scene_file).name}")
        
        if len(scene_files) > 10:
            print(f"  ... and {len(scene_files) - 10} more scenes")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
