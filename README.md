# Bounce - Video Music Mixer

A simple CLI application that combines multiple MP4 video clips with an MP3 audio track, creating a single video output synced to the music.

## Features

- Concatenates multiple MP4 video clips
- Replaces audio with your chosen MP3 track
- Automatically loops videos or speeds them up to match audio duration
- Simple command-line interface

## Requirements

- Python 3.7+
- FFmpeg installed on your system

## Installation

1. Install FFmpeg (if not already installed):
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg`
   - Windows: Download from https://ffmpeg.org/

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python bounce.py <audio.mp3> <videos_folder> [output.mp4]
```

### Arguments

- `audio.mp3` - Path to your MP3 audio file
- `videos_folder` - Path to folder containing MP4 video files
- `output.mp4` - (Optional) Output file name (default: output.mp4)

### Example

```bash
python bounce.py music.mp3 ./video_clips/ final_video.mp4
```

## How It Works

1. Scans the videos folder for all MP4 files
2. Concatenates all videos in alphabetical order
3. Adjusts video duration to match the audio track length
4. Combines the processed video with your audio track
5. Outputs the final MP4 file

## License

MIT
