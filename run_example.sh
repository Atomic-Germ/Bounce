#!/bin/bash
# Real Example - Using the included sample files
# This demonstrates Bounce with the actual example files in the repo

echo "🎬 Bounce - Real Example Demonstration"
echo "========================================"
echo ""
echo "This will create a video using:"
echo "  📁 13 MP4 video clips from example/mp4/"
echo "  🎵 Audio: 'SUPER-Hi x NEEKA - Following The Sun.mp3'"
echo "  📤 Output: my_video.mp4"
echo ""
echo "The process will:"
echo "  1. Concatenate all 13 video clips"
echo "  2. Speed up the video to match the 215-second song"
echo "  3. Replace audio with the music track"
echo ""
read -p "Press Enter to start or Ctrl+C to cancel..."
echo ""

python3 bounce.py \
  "example/mp3/SUPER-Hi x NEEKA - Following The Sun.mp3" \
  example/mp4/ \
  my_video.mp4

echo ""
echo "Done! Check out 'my_video.mp4' to see the result!"
