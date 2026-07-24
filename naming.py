"""
naming.py

Thread-safe human naming request.

Processor waits here.
UI provides the name.
"""

import threading


class NameRequest:

    def __init__(self):
        self.name = None
        self.preview = None
        self.event = threading.Event()
        self.regenerate_requested = False
        self.preview_version = 0

    def request_name(self, preview):
        self.name = None
        self.preview = preview
        self.regenerate_requested = False
        self.preview_version = 0
        self.event.clear()
        return self

    def submit(self, name: str):
        self.name = name
        self.event.set()

    def request_regenerate(self):
        self.regenerate_requested = True
        self.event.set()

    def wait(self):
        self.event.wait()
        return self.name
