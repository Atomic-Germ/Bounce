#!/usr/bin/env python3
"""
Shared Spinner Utility
A simple animated spinner for showing progress during long operations.
"""

import sys
import threading
import time


class Spinner:
    """A simple spinner to show progress during long operations."""
    
    def __init__(self, message="Processing"):
        self.message = message
        self.running = False
        self.thread = None
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.frame_index = 0
    
    def _spin(self):
        """Run the spinner animation."""
        while self.running:
            frame = self.frames[self.frame_index % len(self.frames)]
            sys.stdout.write(f"\r{frame} {self.message}")
            sys.stdout.flush()
            self.frame_index += 1
            time.sleep(0.1)
    
    def start(self):
        """Start the spinner."""
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the spinner and clear the line."""
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * (len(self.message) + 3) + "\r")
        sys.stdout.flush()
