#!/usr/bin/env python3
"""
Align Scenes to Measures
Analyzes scene clips and aligns them to measure timestamps for precise cutting.
"""

import sys
import os
import json
import subprocess
from pathlib import Path


def get_video_duration(video_file):
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


def load_measures(measures_file):
    """Load measure timestamps from file."""
    measures = []
    with open(measures_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse CSV format: measure_number, timestamp
            try:
                parts = line.split(',')
                if len(parts) >= 2:
                    timestamp = float(parts[1].strip())
                    measures.append(timestamp)
            except (ValueError, IndexError):
                continue
    
    return measures


def find_closest_measure_before(target_time, measures):
    """
    Find the measure timestamp closest to but not exceeding target_time.
    
    Args:
        target_time: The time we want to get close to
        measures: List of measure timestamps
    
    Returns:
        (measure_index, measure_time) or (None, None) if none found
    """
    best_index = None
    best_time = None
    
    for i, measure_time in enumerate(measures):
        if measure_time <= target_time:
            best_index = i
            best_time = measure_time
        else:
            break  # Past our target, stop searching
    
    return best_index, best_time


def align_scenes_to_measures(scenes_dir, measures_file, output_file="scene_plan.txt", max_measures=None):
    """
    Analyze scene clips and align them to measure timestamps.
    
    Creates a plan showing how to cut each scene to align with measures.
    Optionally splits long scenes into multiple parts.
    
    Args:
        scenes_dir: Directory containing scene MP4 files
        measures_file: File containing measure timestamps
        output_file: Output file for the alignment plan
        max_measures: Maximum length in measures for a scene (None = no limit)
    """
    print(f"Loading measures from: {measures_file}")
    measures = load_measures(measures_file)
    print(f"✓ Loaded {len(measures)} measure timestamps")
    
    if max_measures:
        print(f"✓ Max scene length: {max_measures} measures")
    
    print(f"\nAnalyzing scenes in: {scenes_dir}")
    
    # Get all scene files sorted
    scene_files = sorted(Path(scenes_dir).glob("scene_*.mp4"))
    
    if not scene_files:
        print(f"❌ No scene files found in {scenes_dir}")
        return
    
    print(f"✓ Found {len(scene_files)} scene files")
    
    # Calculate average measure duration for max length calculation
    if len(measures) > 1 and max_measures:
        measure_intervals = [measures[i+1] - measures[i] for i in range(len(measures)-1)]
        avg_measure_duration = sum(measure_intervals) / len(measure_intervals)
        max_scene_duration = max_measures * avg_measure_duration
        print(f"  Average measure duration: {avg_measure_duration:.2f}s")
        print(f"  Max scene duration: {max_scene_duration:.2f}s ({max_measures} measures)")
    
    # Analyze each scene
    scene_data = []
    
    for scene_file in scene_files:
        scene_name = scene_file.name
        duration = get_video_duration(str(scene_file))
        
        # If max_measures is set and scene is too long, split it
        if max_measures and duration > max_scene_duration:
            print(f"  {scene_name}: {duration:.2f}s - SPLITTING (exceeds {max_measures} measures)")
            
            # Split into multiple parts
            num_parts = int(duration / max_scene_duration) + 1
            for part in range(num_parts):
                start_time = part * max_scene_duration
                end_time = min((part + 1) * max_scene_duration, duration)
                part_duration = end_time - start_time
                
                # Find closest measure for this part's end
                closest_measure_idx, closest_measure_time = find_closest_measure_before(part_duration, measures)
                
                if closest_measure_time is not None:
                    trim_duration = closest_measure_time
                    time_lost = part_duration - trim_duration
                else:
                    trim_duration = part_duration
                    time_lost = 0.0
                    closest_measure_idx = 0
                
                scene_info = {
                    'file': scene_name,
                    'part': part + 1,
                    'total_parts': num_parts,
                    'start_offset': start_time,
                    'original_duration': part_duration,
                    'trim_to': trim_duration,
                    'time_lost': time_lost,
                    'closest_measure': closest_measure_idx + 1 if closest_measure_idx is not None else 0,
                    'measure_time': closest_measure_time if closest_measure_time is not None else 0.0
                }
                
                scene_data.append(scene_info)
                print(f"    Part {part+1}/{num_parts}: {part_duration:.2f}s → {trim_duration:.2f}s "
                      f"(measure {scene_info['closest_measure']}, lose {time_lost:.2f}s)")
        else:
            # Scene is within limit, process normally
            # Find the closest measure to the end of this scene
            closest_measure_idx, closest_measure_time = find_closest_measure_before(duration, measures)
            
            if closest_measure_time is not None:
                trim_duration = closest_measure_time
                time_lost = duration - trim_duration
            else:
                # Scene is shorter than first measure, keep as is
                trim_duration = duration
                time_lost = 0.0
                closest_measure_idx = 0
            
            scene_info = {
                'file': scene_name,
                'part': 1,
                'total_parts': 1,
                'start_offset': 0.0,
                'original_duration': duration,
                'trim_to': trim_duration,
                'time_lost': time_lost,
                'closest_measure': closest_measure_idx + 1 if closest_measure_idx is not None else 0,
                'measure_time': closest_measure_time if closest_measure_time is not None else 0.0
            }
            
            scene_data.append(scene_info)
            
            print(f"  {scene_name}: {duration:.2f}s → trim to {trim_duration:.2f}s "
                  f"(measure {scene_info['closest_measure']}, lose {time_lost:.2f}s)")
    
    # Save the plan
    print(f"\nSaving alignment plan to: {output_file}")
    
    with open(output_file, 'w') as f:
        f.write("# Scene Alignment Plan\n")
        f.write("# Each scene will be trimmed to align with measure timestamps\n")
        if max_measures:
            f.write(f"# Max scene length: {max_measures} measures\n")
        f.write("#\n")
        f.write("# Format: scene_file, part, total_parts, start_offset, original_duration, trim_to_duration, measure_number, measure_time, time_lost\n")
        f.write("#\n")
        
        for scene in scene_data:
            f.write(f"{scene['file']}, {scene['part']}, {scene['total_parts']}, {scene['start_offset']:.6f}, "
                   f"{scene['original_duration']:.6f}, {scene['trim_to']:.6f}, "
                   f"{scene['closest_measure']}, {scene['measure_time']:.6f}, {scene['time_lost']:.6f}\n")
    
    print(f"✓ Saved alignment plan for {len(scene_data)} scene parts")
    
    # Print summary statistics
    total_original = sum(s['original_duration'] for s in scene_data)
    total_trimmed = sum(s['trim_to'] for s in scene_data)
    total_lost = sum(s['time_lost'] for s in scene_data)
    
    print("\n" + "="*70)
    print("Summary:")
    print(f"  Total scene parts:       {len(scene_data)}")
    print(f"  Total original duration: {total_original:.2f}s")
    print(f"  Total after trimming:    {total_trimmed:.2f}s")
    print(f"  Total time trimmed:      {total_lost:.2f}s ({total_lost/total_original*100:.1f}%)")
    print("="*70)
    
    # Show which scenes get trimmed the most
    print("\nScenes with significant trimming (>1s):")
    significant = [s for s in scene_data if s['time_lost'] > 1.0]
    if significant:
        for scene in sorted(significant, key=lambda x: x['time_lost'], reverse=True):
            part_info = f" (part {scene['part']}/{scene['total_parts']})" if scene['total_parts'] > 1 else ""
            print(f"  {scene['file']}{part_info}: {scene['original_duration']:.2f}s → {scene['trim_to']:.2f}s "
                  f"(lose {scene['time_lost']:.2f}s)")
    else:
        print("  None - all scenes trim cleanly!")
    
    return scene_data


def main():
    if len(sys.argv) < 3:
        print("Usage: python align_scenes.py <scenes_dir> <measures_file> [output_file] [max_measures]")
        print("\nArguments:")
        print("  scenes_dir    - Directory containing scene MP4 files")
        print("  measures_file - File with measure timestamps (from filter_beats.py)")
        print("  output_file   - Output file for alignment plan (default: scene_plan.txt)")
        print("  max_measures  - Maximum scene length in measures (default: no limit)")
        print("\nExample:")
        print("  python align_scenes.py scenes measures.txt")
        print("  python align_scenes.py scenes measures.txt scene_plan.txt")
        print("  python align_scenes.py scenes measures.txt scene_plan.txt 16")
        print("\nThe max_measures option will split long scenes into multiple parts.")
        print("For example, max_measures=16 means scenes longer than 16 measures")
        print("will be split into chunks of up to 16 measures each.")
        sys.exit(1)
    
    scenes_dir = sys.argv[1]
    measures_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "scene_plan.txt"
    max_measures = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    # Handle case where output_file looks like a number (max_measures)
    if output_file.isdigit():
        max_measures = int(output_file)
        output_file = "scene_plan.txt"
    
    if not os.path.exists(scenes_dir):
        print(f"❌ Error: Scenes directory not found: {scenes_dir}")
        sys.exit(1)
    
    if not os.path.exists(measures_file):
        print(f"❌ Error: Measures file not found: {measures_file}")
        sys.exit(1)
    
    try:
        scene_data = align_scenes_to_measures(scenes_dir, measures_file, output_file, max_measures)
        
        print(f"\n✅ Success! Alignment plan created.")
        print(f"\nThe plan shows how to trim each scene to align with measure boundaries.")
        if max_measures:
            print(f"Long scenes were split to a maximum of {max_measures} measures each.")
        else:
            print(f"Each scene will be cut at the closest measure to its natural end.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
