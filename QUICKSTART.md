# Bounce - Quick Start Guide

## What It Does

Bounce is a simple CLI tool that combines multiple MP4 video clips with an MP3 audio track. It automatically:
- Concatenates all your video clips in order
- Adjusts the video speed to match your audio length
- Replaces the video audio with your music track
- Creates a single, polished output file

## Installation

### Prerequisites
1. **FFmpeg** - Must be installed on your system
   ```bash
   # macOS
   brew install ffmpeg
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

2. **Python 3.7+** - Already installed on most systems
   ```bash
   python3 --version
   ```

### Install Dependencies
```bash
pip3 install -r requirements.txt
```

## Usage

### Basic Command
```bash
python3 bounce.py <audio_file> <videos_folder> [output_file]
```

### Example
```bash
python3 bounce.py music.mp3 ./clips/ final_video.mp4
```

### Arguments
- `audio_file` - Your MP3 audio track (required)
- `videos_folder` - Folder containing your MP4 clips (required)
- `output_file` - Name for the output video (optional, defaults to "output.mp4")

## Tips

1. **Video Order**: Videos are concatenated in alphabetical order. Name them like:
   - `01_intro.mp4`, `02_middle.mp4`, `03_end.mp4`
   - Or: `clip_a.mp4`, `clip_b.mp4`, `clip_c.mp4`

2. **Video Speed**: If your combined videos are:
   - Longer than the audio → videos will be sped up
   - Shorter than the audio → videos will be slowed down

3. **Best Results**: Use videos with similar resolution and frame rate for smoothest results

4. **File Sizes**: The tool re-encodes videos for compatibility, so expect some processing time for large files

## Troubleshooting

### "No MP4 files found"
- Make sure your folder path is correct
- Check that files have `.mp4` extension
- Use quotes around paths with spaces: `"My Videos/"`

### FFmpeg not found
- Install FFmpeg using the commands above
- Verify installation: `ffmpeg -version`

### Videos won't concatenate
- Videos may have very different parameters
- The tool will automatically re-encode them (takes longer but works)

## Example Workflow

1. Create a folder with your video clips:
   ```
   my_clips/
     ├── 01_opening.mp4
     ├── 02_action.mp4
     └── 03_closing.mp4
   ```

2. Have your music ready:
   ```
   my_song.mp3
   ```

3. Run Bounce:
   ```bash
   python3 bounce.py my_song.mp3 my_clips/ awesome_video.mp4
   ```

4. Wait for processing (you'll see progress updates)

5. Enjoy your new video! 🎉

## Performance

- Small projects (< 10 clips, < 5 minutes): ~30 seconds
- Medium projects (10-20 clips, 5-10 minutes): 1-3 minutes
- Large projects (20+ clips, 10+ minutes): 5-10 minutes

Processing time depends on your computer's CPU and the total video size.
