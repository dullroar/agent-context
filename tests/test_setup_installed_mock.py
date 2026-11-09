"""End-to-end opt-in WSL installer test with only local synthetic providers."""
import base64
import http.server
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run_bounded(command, cwd, env, timeout=30):
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


@unittest.skipUnless(os.environ.get('AGENT_CONTEXT_INSTALLED_MOCK') == '1',
                     'opt-in test requires an isolated network namespace')
class InstalledMockTests(unittest.TestCase):
    def test_installed_hooks_preserve_user_settings_and_receive_real_session_ids(self):
        interfaces = {item['ifname'] for item in json.loads(subprocess.check_output(
            ['ip', '-j', 'link', 'show'], text=True))}
        self.assertEqual(interfaces, {'lo'}, 'refusing to run with non-loopback interfaces')
        for name in ('codex', 'claude', 'copilot'):
            if not shutil.which(name):
                self.skipTest(name + ' CLI is unavailable')
        with tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT')) as directory:
            base = Path(directory)
            project = base / 'project with spaces'
            project.mkdir()
            home = base / 'home with spaces'
            home.mkdir()
            codex_home, claude_home, copilot_home = (home / name for name in ('codex', 'claude', 'copilot'))
            for path in (codex_home, claude_home, copilot_home / 'hooks'):
                path.mkdir(parents=True)
            fake_bin = base / 'fake bin'
            fake_bin.mkdir()
            temp_root = base / 'watch temp'
            temp_root.mkdir()
            (fake_bin / 'gh').write_text('#!/bin/sh\nexit 1\n', encoding='utf-8')
            (fake_bin / 'gh').chmod(0o700)
            existing = base / 'existing.py'
            existing.write_text('''import json,sys
p=sys.argv[1]
text="existing-"+p+"-hook-marker"
print(json.dumps({"additionalContext":text} if p=="copilot" else {"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":text}}))
''', encoding='utf-8')
            def existing_command(name):
                return shlex.join(['/usr/bin/python3', str(existing), name])
            claude_config = claude_home / 'settings.json'
            claude_config.write_text(json.dumps({'hooks': {'SessionStart': [{'hooks': [
                {'type': 'command', 'command': existing_command('claude')}]}]}}), encoding='utf-8')
            copilot_config = copilot_home / 'hooks' / 'existing.json'
            copilot_config.write_text(json.dumps({'version': 1, 'hooks': {'sessionStart': [
                {'type': 'command', 'bash': existing_command('copilot'), 'timeoutSec': 4}]}}), encoding='utf-8')

            class Handler(http.server.BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass
                def do_POST(self):
                    body = self.rfile.read(int(self.headers.get('content-length', '0')))
                    self.server.observations.append((self.path,
                        b'agent-context session registry' in body,
                        b'existing-codex-hook-marker' in body,
                        b'existing-claude-hook-marker' in body,
                        b'existing-copilot-hook-marker' in body,
                        b'registry is missing or inaccessible' in body))
                    match = re.search(rb'Observed native session ID, encoded as UTF-8 base64: ([A-Za-z0-9+/=]+)', body)
                    self.server.ids.append(base64.b64decode(match.group(1)).decode('utf-8') if match else None)
                    if self.path.startswith('/v1/responses'):
                        response = {'id': 'resp_fake', 'object': 'response', 'created_at': 0,
                                    'status': 'completed', 'model': 'mock-model', 'output': [
                                    {'id': 'msg_fake', 'type': 'message', 'status': 'completed', 'role': 'assistant',
                                     'content': [{'type': 'output_text', 'text': 'Synthetic response.', 'annotations': []}]}],
                                    'usage': {'input_tokens': 1, 'output_tokens': 1, 'total_tokens': 2}}
                        events = [{'type': 'response.created', 'response': {'id': 'resp_fake', 'status': 'in_progress', 'output': []}},
                                  {'type': 'response.output_item.done', 'output_index': 0, 'item': response['output'][0]},
                                  {'type': 'response.completed', 'response': response}]
                        payload = ''.join('event: ' + e['type'] + '\ndata: ' + json.dumps(e) + '\n\n' for e in events).encode()
                    elif self.path.startswith('/v1/messages'):
                        usage = {'input_tokens': 1, 'output_tokens': 1, 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}
                        events = [{'type': 'message_start', 'message': {'id': 'msg_fake', 'type': 'message', 'role': 'assistant',
                                   'content': [], 'model': 'claude-sonnet-4-5', 'stop_reason': None, 'stop_sequence': None, 'usage': usage}},
                                  {'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}},
                                  {'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': 'Synthetic response.'}},
                                  {'type': 'content_block_stop', 'index': 0},
                                  {'type': 'message_delta', 'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 1}},
                                  {'type': 'message_stop'}]
                        payload = ''.join('event: ' + e['type'] + '\ndata: ' + json.dumps(e) + '\n\n' for e in events).encode()
                    else:
                        def chunk(delta, finish=None):
                            return {'id': 'chatcmpl_fake', 'object': 'chat.completion.chunk', 'created': 0, 'model': 'mock-model',
                                    'choices': [{'index': 0, 'delta': delta, 'finish_reason': finish}]}
                        events = [chunk({'role': 'assistant', 'content': ''}), chunk({'content': 'Synthetic response.'}), chunk({}, 'stop')]
                        payload = (''.join('data: ' + json.dumps(e) + '\n\n' for e in events) + 'data: [DONE]\n\n').encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Content-Length', str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)

            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            server.observations, server.ids = [], []
            threading.Thread(target=server.serve_forever, daemon=True).start()
            url = f'http://127.0.0.1:{server.server_port}'
            codex_config = codex_home / 'config.toml'
            user_cmd = json.dumps(existing_command('codex'))
            codex_config.write_text('model_provider = "local_mock"\n[model_providers.local_mock]\n'
                'name = "Local mock"\nbase_url = ' + json.dumps(url + '/v1') + '\n'
                'env_key = "MOCK_KEY"\nwire_api = "responses"\nrequires_openai_auth = false\nsupports_websockets = false\n'
                '[[hooks.SessionStart]]\n[[hooks.SessionStart.hooks]]\ntype = "command"\ncommand = ' + user_cmd + '\n', encoding='utf-8')
            preserved = {path: path.read_bytes() for path in (codex_config, claude_config, copilot_config)}
            env = {'PATH': str(fake_bin) + os.pathsep + os.environ['PATH'], 'HOME': str(home),
                   'CODEX_HOME': str(codex_home), 'CLAUDE_CONFIG_DIR': str(claude_home),
                   'COPILOT_HOME': str(copilot_home), 'AGENT_CONTEXT_SETUP_HOME': str(base / 'managed'),
                   'MOCK_KEY': 'local-fake-key', 'ANTHROPIC_API_KEY': 'local-fake-key',
                   'ANTHROPIC_BASE_URL': url, 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
                   'COPILOT_PROVIDER_BASE_URL': url + '/v1', 'COPILOT_MODEL': 'mock-model',
                   'COPILOT_PROVIDER_API_KEY': 'local-fake-key', 'NO_PROXY': '127.0.0.1,localhost',
                   'TMPDIR': str(temp_root), 'LC_ALL': 'C.UTF-8'}
            registry = base / 'registry with spaces'
            setup = ROOT / 'scripts' / 'setup.sh'
            try:
                installed = run_bounded([str(setup), str(registry)], project, env, 60)
                self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
                for name in ('codex', 'claude', 'copilot'):
                    self.assertIn(name + ': hook verified only with a synthetic local provider', installed.stdout)
                for path, before in preserved.items():
                    self.assertEqual(path.read_bytes(), before)
                managed = base / 'managed'
                commands = {
                    'codex': [str(managed / 'codex' / 'codex'), 'exec', '--skip-git-repo-check', '--ephemeral',
                              '--dangerously-bypass-hook-trust', '--json', '-m', 'mock-model', 'synthetic local hook check'],
                    'claude': [str(managed / 'claude' / 'claude'), '-p', 'synthetic local hook check',
                               '--model', 'claude-sonnet-4-5', '--output-format', 'json'],
                    'copilot': [str(managed / 'copilot' / 'copilot'), '-p', 'synthetic local hook check',
                                '--trust-folder', '--no-auto-update', '--sync-session=off', '--disable-client-telemetry'],
                }
                for name, command in commands.items():
                    with self.subTest(agent=name):
                        server.observations.clear()
                        server.ids.clear()
                        result = run_bounded(command, project, env, 45)
                        self.assertEqual(result.returncode, 0, result.stdout[-1500:] + result.stderr[-1500:])
                        self.assertTrue(server.observations, 'no synthetic model request observed')
                        observed = server.observations[0]
                        self.assertTrue(observed[1], 'installed hook guidance was not delivered')
                        self.assertTrue(observed[{'codex': 2, 'claude': 3, 'copilot': 4}[name]], 'existing user hook did not run')
                        self.assertTrue(server.ids[0], 'no opaque session ID was included in hook guidance')
                        self.assertNotIn('no completed hook event was observed', result.stderr)
                        self.assertIn('session-start hook completed', result.stderr)
                        if name == 'codex':
                            events = [json.loads(line) for line in result.stdout.splitlines()]
                            self.assertEqual(next(e['thread_id'] for e in events if e['type'] == 'thread.started'), server.ids[0])
                        elif name == 'claude':
                            self.assertEqual(json.loads(result.stdout)['session_id'], server.ids[0])
                        print(name + ': installed hook and pre-existing hook both reached the local mock')
                for name, command in commands.items():
                    with self.subTest(agent=name, hook='interrupted'):
                        stop = threading.Event()
                        killed = threading.Event()
                        def interrupt_hook():
                            while not stop.is_set():
                                for status_dir in temp_root.glob('agent-context-hook-watch-*'):
                                    for marker in status_dir.glob('start-*'):
                                        try:
                                            pid = int(marker.name.split('-')[1])
                                            cmdline = (Path('/proc') / str(pid) / 'cmdline').read_bytes()
                                            if b'hook_context.py' in cmdline and name.encode() in cmdline:
                                                os.kill(pid, signal.SIGKILL)
                                                killed.set()
                                                return
                                        except (OSError, ValueError, IndexError):
                                            pass
                                time.sleep(0.001)
                        observer = threading.Thread(target=interrupt_hook, daemon=True)
                        observer.start()
                        try:
                            result = run_bounded(command, project, env, 45)
                        finally:
                            stop.set()
                            observer.join(timeout=2)
                        self.assertTrue(killed.is_set(), 'did not observe the installed hook in time')
                        self.assertEqual(result.returncode, 0, result.stdout[-1500:] + result.stderr[-1500:])
                        self.assertIn('hook was interrupted or did not finish', result.stderr)
                        self.assertIn('Synthetic response.', result.stdout)
                        print(name + ': interrupted installed hook warned and the synthetic turn completed')
                for name, command in commands.items():
                    with self.subTest(agent=name, hook='timeout'):
                        stop = threading.Event()
                        suspended = []
                        def suspend_hook():
                            while not stop.is_set():
                                for status_dir in temp_root.glob('agent-context-hook-watch-*'):
                                    for marker in status_dir.glob('start-*'):
                                        try:
                                            pid = int(marker.name.split('-')[1])
                                            cmdline = (Path('/proc') / str(pid) / 'cmdline').read_bytes()
                                            if b'hook_context.py' in cmdline and name.encode() in cmdline:
                                                os.kill(pid, signal.SIGSTOP)
                                                suspended.append(pid)
                                                return
                                        except (OSError, ValueError, IndexError):
                                            pass
                                time.sleep(0.001)
                        observer = threading.Thread(target=suspend_hook, daemon=True)
                        observer.start()
                        try:
                            result = run_bounded(command, project, env, 45)
                        finally:
                            stop.set()
                            observer.join(timeout=2)
                            for pid in suspended:
                                try:
                                    cmdline = (Path('/proc') / str(pid) / 'cmdline').read_bytes()
                                    if b'hook_context.py' in cmdline and name.encode() in cmdline:
                                        os.kill(pid, signal.SIGKILL)
                                except OSError:
                                    pass
                        self.assertTrue(suspended, 'did not observe the installed hook in time')
                        self.assertEqual(result.returncode, 0, result.stdout[-1500:] + result.stderr[-1500:])
                        self.assertIn('hook status timed out', result.stderr)
                        self.assertIn('Synthetic response.', result.stdout)
                        print(name + ': timed-out installed hook warned and the synthetic turn completed')
                saved_registry = base / 'temporarily absent registry'
                registry.rename(saved_registry)
                try:
                    for name, command in commands.items():
                        with self.subTest(agent=name, root='missing'):
                            server.observations.clear()
                            result = run_bounded(command, project, env, 45)
                            self.assertEqual(result.returncode, 0, result.stdout[-1500:] + result.stderr[-1500:])
                            self.assertTrue(server.observations and server.observations[0][5],
                                            'missing-root warning was not delivered to the agent')
                            self.assertIn('hook reported a warning', result.stderr)
                            self.assertIn('session-start hook completed', result.stderr)
                            self.assertIn('Synthetic response.', result.stdout)
                            print(name + ': missing registry warning reached the local mock; turn completed')
                finally:
                    saved_registry.rename(registry)
                repeated = run_bounded([str(setup), str(registry)], project, env, 60)
                self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
                removed = run_bounded([str(setup), '--uninstall'], project, env, 30)
                self.assertEqual(removed.returncode, 0, removed.stdout + removed.stderr)
                for path, before in preserved.items():
                    self.assertEqual(path.read_bytes(), before)
                self.assertFalse((copilot_home / 'hooks' / 'agent-context.json').exists())
            finally:
                server.shutdown()
                server.server_close()


if __name__ == '__main__':
    unittest.main()
