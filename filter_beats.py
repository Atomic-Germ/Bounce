#!/usr/bin/env python3
"""
Filter Beats Script
Filters beat timestamps to keep only downbeats (every 4th beat for 4/4 time).
"""

import sys


def filter_beats_to_measures(input_file, output_file="measures.txt", beats_per_measure=4):
    """
    Filter beat timestamps to keep only downbeats (measure starts).
    
    For 4/4 time, this keeps every 4th beat.
    
    Args:
        input_file: Path to input beats.txt file
        output_file: Path to output file for measure timestamps
        beats_per_measure: Number of beats per measure (default: 4 for 4/4 time)
    
    Returns:
        List of measure timestamps
    """
    print(f"Reading beats from: {input_file}")
    
    # Read beat timestamps from file
    beat_times = []
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse CSV format: beat_number, timestamp
            try:
                parts = line.split(',')
                if len(parts) >= 2:
                    timestamp = float(parts[1].strip())
                    beat_times.append(timestamp)
            except (ValueError, IndexError):
                continue
    
    print(f"✓ Read {len(beat_times)} beats")
    
    # Filter to keep only every Nth beat (downbeats)
    measure_times = []
    for i in range(0, len(beat_times), beats_per_measure):
        measure_times.append(beat_times[i])
    
    print(f"✓ Filtered to {len(measure_times)} measures (every {beats_per_measure} beats)")
    
    # Calculate BPM from measure intervals
    if len(measure_times) > 1:
        intervals = [measure_times[i+1] - measure_times[i] for i in range(len(measure_times)-1)]
        avg_measure_duration = sum(intervals) / len(intervals)
        measures_per_minute = 60.0 / avg_measure_duration
        print(f"✓ Average: {measures_per_minute:.1f} measures per minute")
        print(f"✓ That's {measures_per_minute * beats_per_measure:.1f} BPM")
    
    # Save measure timestamps
    print(f"\nSaving measure timestamps to: {output_file}")
    with open(output_file, 'w') as f:
        f.write(f"# Measure timestamps (every {beats_per_measure} beats)\n")
        f.write(f"# Filtered from: {input_file}\n")
        f.write(f"# Total measures: {len(measure_times)}\n")
        f.write(f"# Format: measure_number, timestamp_seconds\n")
        f.write("#\n")
        
        for i, measure_time in enumerate(measure_times, 1):
            f.write(f"{i}, {measure_time:.6f}\n")
    
    print(f"✓ Saved {len(measure_times)} measure timestamps")
    
    # Print first 10 measures
    print("\nFirst 10 measures:")
    for i, measure_time in enumerate(measure_times[:10], 1):
        print(f"  Measure {i:3d}: {measure_time:7.3f}s")
    
    if len(measure_times) > 10:
        print(f"  ... and {len(measure_times) - 10} more measures")
    
    # Print last 3 measures
    if len(measure_times) > 10:
        print("\nLast 3 measures:")
        for i, measure_time in enumerate(measure_times[-3:], len(measure_times) - 2):
            print(f"  Measure {i:3d}: {measure_time:7.3f}s")
    
    return measure_times


def main():
    if len(sys.argv) < 2:
        print("Usage: python filter_beats.py <beats_file> [output_file] [beats_per_measure]")
        print("\nArguments:")
        print("  beats_file        - Input beats.txt file from detect_beats.py")
        print("  output_file       - Output file for measures (default: measures.txt)")
        print("  beats_per_measure - Beats per measure (default: 4 for 4/4 time)")
        print("\nExample:")
        print("  python filter_beats.py beats.txt")
        print("  python filter_beats.py beats.txt measures.txt 4")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "measures.txt"
    beats_per_measure = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    
    try:
        measure_times = filter_beats_to_measures(input_file, output_file, beats_per_measure)
        print(f"\n✅ Success! Created {len(measure_times)} measure timestamps.")
        print(f"\nThese timestamps represent the start of each measure in the song.")
        print(f"We dropped {beats_per_measure - 1} out of every {beats_per_measure} beats,")
        print(f"keeping only the downbeats (1st beat of each measure).")
    except FileNotFoundError:
        print(f"\n❌ Error: File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
