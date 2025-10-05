#!/usr/bin/env python3
"""
Detect Boring Segments
Identifies segments where the upper half of the video hasn't changed much.
Useful for removing long straight-line sections in motorcycle videos.
"""

import sys
import os
import subprocess
import json
import tempfile
from pathlib import Path
from spinner import Spinner


def analyze_upper_half_changes(video_path, window_seconds=5.0, threshold=0.02):
    """
    Analyze video to find boring segments (minimal change in upper half).
    
    Args:
        video_path: Path to video file
        window_seconds: Time window to analyze for changes (seconds)
        threshold: Change threshold (0.0-1.0, lower=more sensitive)
    
    Returns:
        List of (start_time, end_time) tuples for boring segments
    """
    print(f"Analyzing upper half of video for boring segments...")
    print(f"  Window size: {window_seconds}s")
    print(f"  Threshold: {threshold}")
    
    # Create temp directory for analysis
    with tempfile.TemporaryDirectory() as temp_dir:
        stats_file = os.path.join(temp_dir, "stats.log")
        
        # Use FFmpeg to analyze scene changes in the upper half only
        # We'll crop to upper half and use freezedetect filter
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"crop=iw:ih/2:0:0,freezedetect=n={threshold}:d={window_seconds}",
            "-f", "null",
            "-"
        ]
        
        spinner = Spinner("Analyzing video (this may take a while)...")
        spinner.start()
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        spinner.stop()
        
        # Parse freeze detection output from stderr (ffmpeg outputs to stderr)
        boring_segments = []
        lines = result.stderr.split('\n')
        
        freeze_start = None
        for line in lines:
            if 'lavfi.freezedetect.freeze_start' in line:
                # Extract start time
                try:
                    parts = line.split('lavfi.freezedetect.freeze_start:')
                    if len(parts) > 1:
                        freeze_start = float(parts[1].strip())
                except (ValueError, IndexError):
                    continue
            
            elif 'lavfi.freezedetect.freeze_end' in line and freeze_start is not None:
                # Extract end time
                try:
                    parts = line.split('lavfi.freezedetect.freeze_end:')
                    if len(parts) > 1:
                        freeze_end = float(parts[1].strip())
                        duration = freeze_end - freeze_start
                        
                        # Only include if duration is significant
                        if duration >= window_seconds:
                            boring_segments.append((freeze_start, freeze_end))
                        
                        freeze_start = None
                except (ValueError, IndexError):
                    continue
        
        return boring_segments


def get_video_duration(video_path):
    """Get video duration in seconds."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def create_interesting_segments(video_duration, boring_segments):
    """
    Create list of interesting segments (inverse of boring).
    
    Args:
        video_duration: Total video duration
        boring_segments: List of (start, end) boring segments
    
    Returns:
        List of (start, end) tuples for interesting segments
    """
    if not boring_segments:
        # No boring segments, entire video is interesting
        return [(0.0, video_duration)]
    
    interesting = []
    current_pos = 0.0
    
    for start, end in sorted(boring_segments):
        # Add the interesting part before this boring segment
        if start > current_pos + 1.0:  # At least 1 second of interesting content
            interesting.append((current_pos, start))
        current_pos = end
    
    # Add remaining interesting part after last boring segment
    if current_pos < video_duration - 1.0:
        interesting.append((current_pos, video_duration))
    
    return interesting


def save_segments(segments, output_file, segment_type="interesting"):
    """Save segments to file."""
    with open(output_file, 'w') as f:
        f.write(f"# {segment_type.capitalize()} Segments\n")
        f.write("# Format: start_time, end_time, duration\n")
        f.write("#\n")
        
        for start, end in segments:
            duration = end - start
            f.write(f"{start:.6f}, {end:.6f}, {duration:.6f}\n")


def main():
    if len(sys.argv) < 2:
        print("Detect Boring Segments - Find unchanged upper half sections")
        print("=" * 70)
        print("\nUsage: python detect_boring_segments.py <video_file> [window_seconds] [threshold] [output_prefix]")
        print("\nArguments:")
        print("  video_file     - Input video file")
        print("  window_seconds - Minimum duration to consider boring (default: 5.0)")
        print("  threshold      - Change sensitivity 0.0-1.0 (default: 0.02)")
        print("                   Lower = more sensitive to changes")
        print("  output_prefix  - Output file prefix (default: current directory)")
        print("\nOutputs:")
        print("  boring_segments.txt       - Segments to remove")
        print("  interesting_segments.txt  - Segments to keep")
        print("\nExamples:")
        print("  python detect_boring_segments.py video.mp4")
        print("  python detect_boring_segments.py video.mp4 10.0 0.01")
        print("\nUse case:")
        print("  Motorcycle videos: Detects long straight-line sections where the")
        print("  upper half (sky/horizon) doesn't change, removing boring content.")
        print("\n" + "=" * 70)
        sys.exit(1)
    
    video_file = sys.argv[1]
    window_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.02
    output_prefix = sys.argv[4] if len(sys.argv) > 4 else ""
    
    if not os.path.exists(video_file):
        print(f"❌ Error: Video file not found: {video_file}")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("🎥 Boring Segment Detection")
    print("=" * 70)
    print(f"\nInput video:    {video_file}")
    print(f"Window size:    {window_seconds}s")
    print(f"Threshold:      {threshold}")
    print(f"\nAnalyzing upper half of frame for static content...")
    
    try:
        # Get video duration
        video_duration = get_video_duration(video_file)
        print(f"Video duration: {video_duration:.2f}s")
        
        # Detect boring segments
        boring_segments = analyze_upper_half_changes(video_file, window_seconds, threshold)
        
        # Calculate statistics
        total_boring = sum(end - start for start, end in boring_segments)
        boring_percent = (total_boring / video_duration * 100) if video_duration > 0 else 0
        
        print("\n" + "=" * 70)
        print("Results:")
        print("=" * 70)
        print(f"Boring segments found:  {len(boring_segments)}")
        print(f"Total boring time:      {total_boring:.2f}s ({boring_percent:.1f}%)")
        print(f"Interesting time:       {video_duration - total_boring:.2f}s ({100 - boring_percent:.1f}%)")
        
        if boring_segments:
            print("\nBoring segments:")
            for i, (start, end) in enumerate(boring_segments, 1):
                duration = end - start
                print(f"  Segment {i:2d}: {start:7.2f}s - {end:7.2f}s ({duration:6.2f}s)")
        else:
            print("\n✨ No boring segments detected - video is all interesting!")
        
        # Create interesting segments
        interesting_segments = create_interesting_segments(video_duration, boring_segments)
        
        print(f"\nInteresting segments:   {len(interesting_segments)}")
        for i, (start, end) in enumerate(interesting_segments, 1):
            duration = end - start
            print(f"  Segment {i:2d}: {start:7.2f}s - {end:7.2f}s ({duration:6.2f}s)")
        
        # Save results
        boring_output = os.path.join(output_prefix, "boring_segments.txt") if output_prefix else "boring_segments.txt"
        interesting_output = os.path.join(output_prefix, "interesting_segments.txt") if output_prefix else "interesting_segments.txt"
        
        save_segments(boring_segments, boring_output, "boring")
        save_segments(interesting_segments, interesting_output, "interesting")
        
        print("\n" + "=" * 70)
        print("✅ Segment detection complete!")
        print("=" * 70)
        print("\nOutput files:")
        print(f"  {boring_output}")
        print(f"  {interesting_output}")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
