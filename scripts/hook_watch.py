#!/usr/bin/env python3
"""Per-launch hook liveness tracking for the tested WSL CLI integrations.

Markers contain only a process ID and a random token, never hook input or user
content. A monitor observes markers without controlling the agent or its tools.
"""
import os
from pathlib import Path
import re
import time
import uuid

PREFIX = re.compile(r'^start-([0-9]+)-([0-9a-f]{32})$')


def mark_start(directory):
    if not directory:
        return None
    name = f'{os.getpid()}-{uuid.uuid4().hex}'
    path = Path(directory) / ('start-' + name)
    with path.open('xb'):
        pass
    return name


def mark_done(directory, name):
    if name:
        with (Path(directory) / ('done-' + name)).open('xb'):
            pass


def mark_warning(directory, name):
    if name:
        with (Path(directory) / ('warn-' + name)).open('xb'):
            pass


def process_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # A terminated but not yet reaped child is still visible to kill(pid, 0).
    try:
        stat = (Path('/proc') / str(pid) / 'stat').read_text(encoding='ascii')
        if stat.rsplit(')', 1)[1].lstrip().startswith('Z '):
            return False
    except (OSError, IndexError):
        pass
    return True


class HookMonitor:
    def __init__(self, directory, emit, timeout_seconds=3.0, clock=time.monotonic):
        self.directory = Path(directory)
        self.emit = emit
        self.timeout_seconds = timeout_seconds
        self.clock = clock
        self.seen = {}
        self.reported = set()
        self.completed = set()
        self.warning_reported = set()
        self.monitor_error_reported = False

    def scan(self, final=False):
        try:
            names = {entry.name for entry in self.directory.iterdir()}
        except OSError:
            if not self.monitor_error_reported:
                self.emit('agent-context: hook monitor unavailable; continue work and use the manual fallback')
                self.monitor_error_reported = True
            return
        for filename in names:
            match = PREFIX.fullmatch(filename)
            if not match:
                continue
            token = filename[len('start-'):]
            warning_exists = 'warn-' + token in names or (self.directory / ('warn-' + token)).exists()
            if warning_exists and token not in self.warning_reported:
                self.emit('agent-context: hook reported a warning; continue work and use the manual fallback')
                self.warning_reported.add(token)
            if 'done-' + token in names:
                self.completed.add(token)
                continue
            if token in self.reported:
                continue
            now = self.clock()
            self.seen.setdefault(token, now)
            if final or not process_alive(int(match.group(1))):
                # The completion marker can be published after the directory
                # snapshot but before the process exits.
                if (self.directory / ('done-' + token)).exists():
                    self.completed.add(token)
                    continue
                self.emit('agent-context: hook was interrupted or did not finish; continue work and use the manual fallback')
                self.reported.add(token)
            elif now - self.seen[token] >= self.timeout_seconds:
                self.emit('agent-context: hook status timed out; continue work and use the manual fallback')
                self.reported.add(token)
