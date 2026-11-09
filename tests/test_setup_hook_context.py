import base64
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HOOK = Path(__file__).resolve().parents[1] / 'scripts' / 'hook_context.py'
SPEC = importlib.util.spec_from_file_location('agent_context_hook', HOOK)
hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hook)


class HookContextTests(unittest.TestCase):
    def run_hook(self, provider, raw, root=tempfile.gettempdir()):
        env = os.environ.copy()
        if root is None:
            env.pop('AGENT_CONTEXT_HOME', None)
        else:
            env['AGENT_CONTEXT_HOME'] = root
        with tempfile.TemporaryDirectory() as status_dir:
            env['AGENT_CONTEXT_HOOK_STATUS_DIR'] = status_dir
            return subprocess.run([sys.executable, str(HOOK), provider], input=raw, capture_output=True, env=env, timeout=3)

    def test_start_event_preserves_opaque_id_and_omits_sensitive_fields(self):
        native = 'opaque id / 雪'
        for provider in ('codex', 'claude', 'copilot'):
            with self.subTest(provider=provider):
                event = {'sessionId': native} if provider == 'copilot' else {
                    'hook_event_name': 'SessionStart', 'session_id': native}
                event.update({'prompt': 'synthetic-private-prompt', 'transcript_path': 'synthetic-private-path'})
                result = self.run_hook(provider, json.dumps(event).encode())
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, b'')
                self.assertNotIn(b'synthetic-private-prompt', result.stdout)
                self.assertNotIn(b'synthetic-private-path', result.stdout)
                output = json.loads(result.stdout)
                context = output['additionalContext'] if provider == 'copilot' else output['hookSpecificOutput']['additionalContext']
                self.assertIn(base64.b64encode(native.encode()).decode(), context)
                self.assertIn('Use unknown', context)
                self.assertIn('agent: ' + provider, context)
                self.assertIn('Observed event: ' + ('sessionStart' if provider == 'copilot' else 'SessionStart'), context)
                self.assertIn('runtime:', context)
                self.assertNotIn('systemMessage', output)

    def test_missing_root_or_id_produces_warning_without_denial(self):
        for provider in ('codex', 'claude', 'copilot'):
            event = {} if provider == 'copilot' else {'hook_event_name': 'SessionStart'}
            result = self.run_hook(provider, json.dumps(event).encode(), root=None)
            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            self.assertNotIn('decision', output)
            self.assertNotIn('continue', output)
            self.assertIn('manual fallback', json.dumps(output))
            self.assertIn('AGENT_CONTEXT_HOME is unset', json.dumps(output))

    def test_invalid_input_and_other_events_do_not_block(self):
        for provider in ('codex', 'claude', 'copilot'):
            for raw in (b'{bad json', b'[' + b' ' * 65537 + b']'):
                result = self.run_hook(provider, raw)
                self.assertEqual(result.returncode, 0)
                self.assertIn('manual fallback', result.stdout.decode())
                self.assertNotIn(b'decision', result.stdout)
        result = self.run_hook('codex', b'{"hook_event_name":"Stop","session_id":"id"}')
        self.assertEqual(json.loads(result.stdout), {})

    def test_invalid_identifier_uses_manual_fallback(self):
        for native in ('   ', 'opaque\u0085id'):
            event = {'hook_event_name': 'SessionStart', 'session_id': native}
            result = self.run_hook('codex', json.dumps(event).encode())
            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            self.assertIn('native session ID unavailable or unsuitable', output['systemMessage'])
            self.assertNotIn(base64.b64encode(native.encode()).decode(),
                             output['hookSpecificOutput']['additionalContext'])

    def test_missing_root_reports_warning_without_denial(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = str(Path(temporary) / 'missing')
            event = b'{"hook_event_name":"SessionStart","session_id":"id"}'
            for provider in ('codex', 'claude'):
                result = self.run_hook(provider, event, root=missing)
                self.assertEqual(result.returncode, 0)
                self.assertIn('registry is missing or inaccessible', json.dumps(json.loads(result.stdout)))
            result = self.run_hook('copilot', b'{"sessionId":"id"}', root=missing)
            self.assertEqual(result.returncode, 0)
            self.assertIn('registry is missing or inaccessible', json.dumps(json.loads(result.stdout)))

    def test_timed_out_root_probe_returns_warning(self):
        event = {'hook_event_name': 'SessionStart', 'session_id': 'id'}
        with mock.patch.object(hook.subprocess, 'run', side_effect=subprocess.TimeoutExpired('probe', 0.75)):
            output = hook.render('codex', event, '/synthetic/root')
        self.assertIn('access check failed or timed out', output['systemMessage'])
        self.assertNotIn('decision', output)

    def test_missing_monitor_reports_that_interruptions_may_be_silent(self):
        env = os.environ.copy()
        env.pop('AGENT_CONTEXT_HOOK_STATUS_DIR', None)
        env['AGENT_CONTEXT_HOME'] = tempfile.gettempdir()
        result = subprocess.run([sys.executable, str(HOOK), 'codex'],
                                input=b'{"hook_event_name":"SessionStart","session_id":"id"}',
                                capture_output=True, env=env, timeout=3)
        self.assertEqual(result.returncode, 0)
        self.assertIn('hook monitor is not active', json.loads(result.stdout)['systemMessage'])

    def test_missing_root_marks_a_warning_for_the_launcher(self):
        with tempfile.TemporaryDirectory() as status_dir:
            env = os.environ.copy()
            env.pop('AGENT_CONTEXT_HOME', None)
            env['AGENT_CONTEXT_HOOK_STATUS_DIR'] = status_dir
            result = subprocess.run([sys.executable, str(HOOK), 'codex'],
                                    input=b'{"hook_event_name":"SessionStart","session_id":"id"}',
                                    capture_output=True, env=env, timeout=3)
            self.assertEqual(result.returncode, 0)
            names = {path.name.split('-', 1)[0] for path in Path(status_dir).iterdir()}
            self.assertEqual(names, {'start', 'warn', 'done'})
            self.assertTrue(all(not path.read_bytes() for path in Path(status_dir).iterdir()))

    def test_worker_interruption_and_timeout_produce_provider_specific_warnings(self):
        stopped = [sys.executable, '-c', 'import os,signal; os.kill(os.getpid(), signal.SIGTERM)']
        delayed = [sys.executable, '-c', 'import time; time.sleep(5)']
        for provider in ('codex', 'claude', 'copilot'):
            for command, expected in ((stopped, 'failed or was interrupted'), (delayed, 'timed out')):
                with self.subTest(provider=provider, expected=expected):
                    output = hook.supervise(provider, b'{}', tempfile.gettempdir(), command=command, timeout=0.2)
                    self.assertIn(expected, json.dumps(output))
                    self.assertIn('manual fallback', json.dumps(output))
                    self.assertNotIn('decision', output)


if __name__ == '__main__':
    unittest.main()
