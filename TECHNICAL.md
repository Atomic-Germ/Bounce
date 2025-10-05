# Technical Details

## Architecture

Bounce is built using Python 3 and FFmpeg, leveraging FFmpeg's powerful video processing capabilities through subprocess calls.

## How It Works

### 1. Video Discovery
- Scans the specified folder for all `.mp4` and `.MP4` files
- Sorts files alphabetically for consistent ordering
- Validates that at least one video file exists

### 2. Duration Analysis
- Uses `ffprobe` to extract exact duration of the audio file
- Uses `ffprobe` to determine total duration of concatenated videos
- Calculates speed adjustment factor needed

### 3. Video Concatenation
- Creates a temporary concat demuxer file listing all videos
- First attempts stream copy (fastest, no re-encoding)
- Falls back to re-encoding if videos have incompatible parameters
- Uses H.264 video codec and AAC audio codec for compatibility

### 4. Speed Adjustment
- Calculates required speed factor: `current_duration / target_duration`
- Uses FFmpeg's `setpts` filter to adjust playback speed
- Maintains video quality while adjusting timing
- Removes audio from video track (will be replaced)

### 5. Audio Combination
- Merges the speed-adjusted video with the audio track
- Copies video stream (no re-encoding)
- Encodes audio as AAC for broad compatibility
- Uses `-shortest` flag to ensure sync

## Technical Specifications

### Video Processing
- **Codec**: H.264 (libx264)
- **Quality**: CRF 23 (medium quality)
- **Preset**: medium (balance of speed and quality)

### Audio Processing
- **Codec**: AAC
- **Bitrate**: 192 kbps
- **Channels**: Preserved from source

### File Handling
- Uses temporary directory for intermediate files
- Automatic cleanup of temporary files
- Safe file path handling with proper escaping

## Dependencies

### FFmpeg
Required binaries:
- `ffmpeg` - Video processing
- `ffprobe` - Media analysis

### Python Packages
- `ffmpeg-python` (0.2.0) - Optional helper library (not strictly required)
- Standard library only for core functionality

## Performance Optimizations

1. **Stream Copy**: When possible, copies video streams without re-encoding
2. **Temporary Files**: Uses temp directory with automatic cleanup
3. **Single Pass**: Processes video in a single pipeline where possible
4. **No Redundant Analysis**: Analyzes duration once per file

## Error Handling

The application handles:
- Missing input files
- Invalid directory paths
- Incompatible video formats
- FFmpeg processing errors
- Insufficient disk space (via FFmpeg)

## Limitations

1. **Format Support**: Currently only MP4/H.264 input videos
2. **Audio Format**: MP3 input (can be extended to support other formats)
3. **Speed Range**: Best results with speed adjustments between 0.5x - 2.0x
4. **Memory**: Large video files may require significant system memory

## Future Enhancements

Potential improvements:
- Support for more video formats (AVI, MOV, MKV)
- Support for more audio formats (WAV, FLAC, AAC)
- Custom output quality settings
- Progress bar for long operations
- Parallel processing for faster concatenation
- GUI interface option
- Beat detection for smarter video transitions
- Automatic video effects/transitions
- Custom video ordering (not just alphabetical)

## Command Line Examples

### Basic FFmpeg Commands Used

**Concatenation:**
```bash
ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4
```

**Speed Adjustment:**
```bash
ffmpeg -i input.mp4 -filter:v "setpts=0.5*PTS" -an output.mp4
```

**Audio Combination:**
```bash
ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -shortest output.mp4
```

## License

MIT License - See LICENSE file for details
