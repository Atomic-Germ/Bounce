# Bounce - Beat-Synchronized Music Video Creator

## ✅ Complete & Working!

Create beat-synchronized music videos by detecting scenes in video and aligning them with musical measure boundaries.

## Quick Start

```bash
python bounce.py <audio_file> <video_file> [output_file]
```

That's it! The script handles all 5 steps automatically.

### Example

```bash
python bounce.py song.mp3 video.mp4 result.mp4
```

### Options

```bash
python bounce.py song.mp3 video.mp4 result.mp4 --scene-threshold=0.2 --max-scene-measures=16
```

- `--scene-threshold=N` - Scene detection sensitivity (0.0-1.0, default: 0.3, lower=more scenes)
- `--beats-per-measure=N` - Beats per measure (default: 4 for 4/4 time)
- `--max-scene-measures=N` - Maximum scene length in measures (default: no limit)
  - Long scenes will be split into chunks for more dynamic cuts
  - Example: `--max-scene-measures=16` splits scenes longer than 16 measures
- `--skip-boring=N` - Skip boring segments where upper half is static for N+ seconds (default: disabled)
  - Useful for motorcycle videos to remove long straight-line sections
  - Example: `--skip-boring=10` removes segments where sky/horizon doesn't change for 10+ seconds

## What It Does

The tool processes your video and audio in 5 automatic steps:

1. **Beat Detection** - Detects beats in the audio using librosa
2. **Measure Filtering** - Filters to downbeats (every 4th beat for 4/4 time)
3. **Scene Detection** - Detects shot changes in video using FFmpeg
4. **Scene Alignment** - Aligns scenes to measure timestamps
5. **Video Assembly** - Trims, concatenates, and adds music

**Result:** A video where all scene changes happen exactly on downbeats!

## Example Results

Using the included example files:

```bash
python bounce.py example/mp3/Example.mp3 example/Example.mp4 output.mp4 --scene-threshold=0.2
```

**Input:**
- Video: 362 seconds, 10 natural scenes detected
- Audio: 215 seconds, 498 beats → 125 measures

**Output:**
- Final video: 215 seconds, 97 MB
- 10 scenes, all aligned to measure boundaries
- Perfect beat synchronization

## Installation

### Requirements

- Python 3.7+
- FFmpeg
- librosa
- numpy

### Install

```bash
# Install FFmpeg
brew install ffmpeg  # macOS
# or: sudo apt-get install ffmpeg  # Linux

# Install Python packages
pip install librosa numpy
```

## How It Works

### Beat Detection
Analyzes the audio to find beats and tempo, then filters to measure starts (downbeats).

### Scene Detection
Uses FFmpeg's scene filter to detect sudden changes in pixel values between frames - exactly where shots change in the video.

### Alignment
Each scene is trimmed to end on the closest measure boundary, ensuring all cuts happen on downbeats.

### Assembly
Scenes are trimmed, concatenated, and combined with the music to create the final synchronized video.

## Individual Scripts

You can also run each step separately if needed:

```bash
# Step 1: Detect beats
python detect_beats.py audio.mp3

# Step 2: Filter to measures
python filter_beats.py beats.txt

# Step 3: Detect scenes
python detect_scenes.py video.mp4 scenes 0.2

# Step 4: Align scenes to measures
python align_scenes.py scenes measures.txt

# Step 5: Assemble final video
python assemble_video.py scenes scene_plan.txt audio.mp3 output.mp4
```

Each script can be run independently for debugging or customization.

## Technical Details

- **Beat Detection:** Uses librosa's beat tracking algorithm
- **Scene Detection:** Uses FFmpeg's scene filter (analyzes frame-to-frame pixel changes)
- **Video Encoding:** H.264 with CRF 23, fast/medium preset
- **Audio Encoding:** AAC at 192 kbps (converted from MP3 for better MP4 compatibility)
- **Temp Files:** Automatically cleaned up after processing

## Notes

- Assumes 4/4 time signature (most popular music)
- Scene detection works best with clear cuts/hard transitions
- Processing time depends on video length (typically 5-10 minutes for a 3-minute video)
- Gradual transitions (fades, dissolves) may not be detected as scene changes

## Troubleshooting

**"librosa not installed"**
```bash
pip install librosa numpy
```

**"FFmpeg not found"**
```bash
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Linux
```

**Too few/many scenes detected**
- Adjust `--scene-threshold`: Lower values (0.2) detect more scenes, higher values (0.5) detect fewer

**Wrong time signature**
- Use `--beats-per-measure=3` for 3/4 time, or other values as needed

## Files in This Repo

- `bounce.py` - **Main CLI script** (runs all steps)
- `detect_beats.py` - Beat detection
- `filter_beats.py` - Measure filtering
- `detect_scenes.py` - Scene detection
- `align_scenes.py` - Scene alignment
- `assemble_video.py` - Video assembly
- `example/` - Example MP3 and MP4 files for testing

## Future Enhancements

- Support for other time signatures
- Custom beat patterns
- Crossfade transitions
- Multiple input videos
- Progress bars
- GUI interface

---

**Built step-by-step, tested at each stage, unified into one simple command!**
