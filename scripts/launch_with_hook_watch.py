#!/usr/bin/env python3
"""POSIX agent launcher with per-session hook liveness tracking."""
import os
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from hook_watch import HookMonitor


def emit(message):
    try:
        print(message, file=sys.stderr, flush=True)
    except OSError:
        pass


def direct_launch(command, env):
    try:
        result = subprocess.call(command, env=env)
    except OSError:
        emit('agent-context: could not start the agent')
        return 127
    return 128 - result if result < 0 else result


def add_hook_config(provider, config_path, command, reporter=emit):
    if not provider or provider == 'copilot':
        return command
    args = command[1:]
    if provider == 'codex':
        if any(value in ('-c', '--config') or value.startswith('--config=') or
               (value.startswith('-c') and len(value) > 2) for value in args):
            reporter('agent-context: explicit Codex config preserved; hook setup not injected')
            return command
        try:
            value = Path(config_path).read_text(encoding='utf-8').strip()
        except OSError:
            reporter('agent-context: hook configuration unavailable; continue work and use the manual fallback')
            return command
        return [command[0], '-c', value, *args]
    if any(value == '--settings' or value.startswith('--settings=') for value in args):
        reporter('agent-context: explicit Claude settings preserved; hook setup not injected')
        return command
    if not Path(config_path).is_file():
        reporter('agent-context: hook configuration unavailable; continue work and use the manual fallback')
        return command
    return [command[0], '--settings', config_path, *args]


def launch(command, env=None, reporter=emit, interval=0.1, hook_timeout=3.0, startup_grace=5.0):
    """Run the agent without capturing its I/O; monitoring failure is nonfatal."""
    agent_env = dict(os.environ if env is None else env)
    try:
        temporary = tempfile.TemporaryDirectory(prefix='agent-context-hook-watch-')
    except OSError:
        reporter('agent-context: hook monitor unavailable; continue work and use the manual fallback')
        return direct_launch(command, agent_env)
    try:
        agent_env['AGENT_CONTEXT_HOOK_STATUS_DIR'] = temporary.name
        reporter('agent-context: hook monitoring active; hook execution is not yet confirmed')
        monitor = HookMonitor(temporary.name, reporter, timeout_seconds=hook_timeout)
        reported_completions = set()
        startup_deadline = time.monotonic() + startup_grace
        unconfirmed_reported = False
        try:
            agent = subprocess.Popen(command, env=agent_env)
        except OSError:
            reporter('agent-context: could not start the agent')
            return 127
        try:
            while True:
                result = agent.poll()
                try:
                    monitor.scan(final=result is not None)
                    for token in monitor.completed - reported_completions:
                        reporter('agent-context: session-start hook completed')
                        reported_completions.add(token)
                    if (result is None and not monitor.completed and not unconfirmed_reported and
                            time.monotonic() >= startup_deadline):
                        reporter('agent-context: session-start hook has not been confirmed; continue work and use the manual fallback')
                        unconfirmed_reported = True
                except Exception:
                    reporter('agent-context: hook monitor failed; continue work and use the manual fallback')
                    return_code = agent.wait()
                    return 128 - return_code if return_code < 0 else return_code
                if result is not None:
                    if not monitor.completed:
                        reporter('agent-context: no completed hook event was observed; use the manual fallback if needed')
                    return 128 - result if result < 0 else result
                time.sleep(interval)
        except KeyboardInterrupt:
            # The child remains in the same foreground process group and receives
            # the terminal interrupt directly; do not send a duplicate signal.
            return_code = agent.wait()
            return 128 - return_code if return_code < 0 else return_code
    finally:
        try:
            temporary.cleanup()
        except OSError:
            reporter('agent-context: hook monitor cleanup failed; continue work')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', choices=('codex', 'claude', 'copilot'))
    parser.add_argument('--config', default='')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == '--':
        command = command[1:]
    if not command:
        print('usage: launch_with_hook_watch.py -- AGENT [ARGS...]', file=sys.stderr)
        return 2
    command = add_hook_config(args.provider, args.config, command)
    if not sys.platform.startswith('linux'):
        emit('agent-context: hook monitoring is unverified on this host; use the manual fallback')
        return direct_launch(command, os.environ.copy())
    return launch(command)


if __name__ == '__main__':
    sys.exit(main())
