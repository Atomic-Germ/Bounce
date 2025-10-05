#!/usr/bin/env python3
"""
Bounce - Beat-Synchronized Music Video Creator
Main CLI that orchestrates all steps to create a music video.
"""

import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path


def run_step(step_name, command, description):
    """
    Run a processing step and handle errors.
    
    Args:
        step_name: Name of the step for display
        command: Command to run (list of arguments)
        description: Description of what the step does
    """
    print(f"\n{'='*70}")
    print(f"Step: {step_name}")
    print(f"{'='*70}")
    print(f"{description}\n")
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Print output
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0:
        print(f"\n❌ Error in {step_name}")
        if result.stderr:
            print(result.stderr)
        raise RuntimeError(f"{step_name} failed with exit code {result.returncode}")
    
    return result


def main():
    """Main CLI entry point."""
    
    if len(sys.argv) < 3:
        print("Bounce - Beat-Synchronized Music Video Creator")
        print("=" * 70)
        print("\nUsage: python bounce.py <audio_file> <video_file> [output_file] [options]")
        print("\nArguments:")
        print("  audio_file  - MP3 audio file (the music)")
        print("  video_file  - MP4 video file (the footage)")
        print("  output_file - Output video file (default: output.mp4)")
        print("\nOptions:")
        print("  --scene-threshold=N    - Scene detection sensitivity 0.0-1.0 (default: 0.3)")
        print("                           Lower = more sensitive, detects more scenes")
        print("  --beats-per-measure=N  - Beats per measure (default: 4 for 4/4 time)")
        print("  --max-scene-measures=N - Maximum scene length in measures (default: no limit)")
        print("                           Long scenes will be split into chunks")
        print("\nExamples:")
        print("  python bounce.py song.mp3 video.mp4")
        print("  python bounce.py song.mp3 video.mp4 result.mp4")
        print("  python bounce.py song.mp3 video.mp4 result.mp4 --scene-threshold=0.2")
        print("  python bounce.py song.mp3 video.mp4 result.mp4 --max-scene-measures=16")
        print("\nWhat it does:")
        print("  1. Detects beats in the audio")
        print("  2. Filters beats to measures (downbeats)")
        print("  3. Detects scene changes in the video")
        print("  4. Aligns scenes to measure timestamps")
        print("  5. Assembles final beat-synchronized video")
        print("\n" + "=" * 70)
        sys.exit(1)
    
    # Parse arguments
    audio_file = sys.argv[1]
    video_file = sys.argv[2]
    output_file = "output.mp4"
    scene_threshold = 0.3
    beats_per_measure = 4
    max_scene_measures = None
    
    # Parse optional arguments
    for arg in sys.argv[3:]:
        if arg.startswith("--scene-threshold="):
            try:
                scene_threshold = float(arg.split("=")[1])
            except ValueError:
                print("⚠ Warning: Invalid scene threshold, using default 0.3")
        elif arg.startswith("--beats-per-measure="):
            try:
                beats_per_measure = int(arg.split("=")[1])
            except ValueError:
                print("⚠ Warning: Invalid beats per measure, using default 4")
        elif arg.startswith("--max-scene-measures="):
            try:
                max_scene_measures = int(arg.split("=")[1])
            except ValueError:
                print("⚠ Warning: Invalid max scene measures, ignoring")
        elif not arg.startswith("--"):
            output_file = arg
    
    # Validate inputs
    if not os.path.exists(audio_file):
        print(f"❌ Error: Audio file not found: {audio_file}")
        sys.exit(1)
    
    if not os.path.exists(video_file):
        print(f"❌ Error: Video file not found: {video_file}")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("🎬 Bounce - Beat-Synchronized Music Video Creator")
    print("=" * 70)
    print(f"\nInput audio:  {audio_file}")
    print(f"Input video:  {video_file}")
    print(f"Output file:  {output_file}")
    print(f"\nSettings:")
    print(f"  Scene threshold:      {scene_threshold}")
    print(f"  Beats per measure:    {beats_per_measure}")
    if max_scene_measures:
        print(f"  Max scene measures:   {max_scene_measures}")
    else:
        print(f"  Max scene measures:   no limit")
    
    # Create working directory for temporary files
    work_dir = tempfile.mkdtemp(prefix="bounce_")
    print(f"\nWorking directory: {work_dir}")
    
    try:
        # Define file paths
        beats_file = os.path.join(work_dir, "beats.txt")
        measures_file = os.path.join(work_dir, "measures.txt")
        scenes_dir = os.path.join(work_dir, "scenes")
        scene_plan_file = os.path.join(work_dir, "scene_plan.txt")
        
        # Step 1: Detect beats
        run_step(
            "1. Beat Detection",
            ["python3", "detect_beats.py", audio_file, beats_file],
            "Analyzing audio to detect beats..."
        )
        
        # Step 2: Filter to measures
        run_step(
            "2. Measure Filtering",
            ["python3", "filter_beats.py", beats_file, measures_file, str(beats_per_measure)],
            f"Filtering beats to measures ({beats_per_measure}/4 time)..."
        )
        
        # Step 3: Detect scenes
        run_step(
            "3. Scene Detection",
            ["python3", "detect_scenes.py", video_file, scenes_dir, str(scene_threshold)],
            "Detecting scene changes in video..."
        )
        
        # Step 4: Align scenes to measures
        align_cmd = ["python3", "align_scenes.py", scenes_dir, measures_file, scene_plan_file]
        if max_scene_measures:
            align_cmd.append(str(max_scene_measures))
        
        run_step(
            "4. Scene Alignment",
            align_cmd,
            "Aligning scenes to measure timestamps..."
        )
        
        # Step 5: Assemble final video
        run_step(
            "5. Video Assembly",
            ["python3", "assemble_video.py", scenes_dir, scene_plan_file, audio_file, output_file],
            "Assembling final beat-synchronized video..."
        )
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! Your beat-synchronized music video is ready!")
        print("=" * 70)
        print(f"\n📄 Output file: {output_file}")
        
        # Show file size and duration
        if os.path.exists(output_file):
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"📊 File size:   {size_mb:.2f} MB")
            
            # Get duration
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "default=noprint_wrappers=1:nokey=1", output_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                print(f"⏱️  Duration:    {duration:.2f} seconds")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Clean up working directory
        if os.path.exists(work_dir):
            print(f"\n🧹 Cleaning up temporary files...")
            shutil.rmtree(work_dir)
            print(f"✓ Removed {work_dir}")


if __name__ == "__main__":
    main()
