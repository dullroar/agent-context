"""Opt-in Codex hook tests against a local fake Responses server.

Run only inside a private network namespace with loopback enabled. This test
uses synthetic inputs and a fake credential; it records no raw hook payloads.
"""
import http.server
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HOOK = Path(__file__).resolve().parents[1] / 'scripts' / 'hook_context.py'
WATCH = HOOK.with_name('hook_watch.py')
LAUNCH = HOOK.with_name('launch_with_hook_watch.py')


def run_bounded(command, cwd, env, timeout):
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

@unittest.skipUnless(os.environ.get('AGENT_CONTEXT_CODEX_MOCK') == '1',
                     'opt-in test requires an isolated network namespace')
class CodexMockHookTests(unittest.TestCase):
    def test_start_hook_result_failure_and_timeout(self):
        interfaces = {item['ifname'] for item in json.loads(subprocess.check_output(
            ['ip', '-j', 'link', 'show'], text=True))}
        self.assertEqual(interfaces, {'lo'}, 'refusing to run with non-loopback interfaces')
        codex = shutil.which('codex')
        if not codex:
            self.skipTest('Codex CLI is unavailable')
        for mode in ('context', 'adapter', 'config_merge', 'adapter_no_root', 'adapter_missing', 'adapter_stopped', 'adapter_timeout', 'exit_two', 'timeout', 'interrupted'):
            with self.subTest(mode=mode):
                self.run_hook_scenario(codex, mode)

    def run_hook_scenario(self, codex, mode):
        with tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT')) as directory:
            base = Path(directory)
            home = base / 'home'
            home.mkdir()
            project = base / 'project'
            project.mkdir()
            (base / 'registry').mkdir()
            events_path = base / 'events.jsonl'
            hook = base / 'hook.py'
            hook.write_text('''import json,os,pathlib,signal,subprocess,sys,time
x=json.load(sys.stdin)
p=pathlib.Path(sys.argv[1])
with p.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"event":x.get("hook_event_name"),"id_present":bool(x.get("session_id")),"source":x.get("source")})+"\\n")
if x.get("hook_event_name") == "SessionStart":
    mode=sys.argv[2]
    if mode in ("exit_two", "timeout", "interrupted"):
        import importlib.util
        spec=importlib.util.spec_from_file_location("watch",sys.argv[4])
        watch=importlib.util.module_from_spec(spec); spec.loader.exec_module(watch)
        watch.mark_start(os.environ["AGENT_CONTEXT_HOOK_STATUS_DIR"])
    if mode == "context":
        print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"agent-context synthetic hook marker"}}))
    elif mode in ("adapter", "config_merge", "adapter_no_root", "adapter_missing"):
        env=dict(os.environ)
        if mode == "adapter_no_root": env.pop("AGENT_CONTEXT_HOME",None)
        if mode == "adapter_missing": env["AGENT_CONTEXT_HOME"] += "/missing"
        p=subprocess.run([sys.executable,sys.argv[3],"codex"],input=json.dumps(x),text=True,capture_output=True,timeout=2,env=env)
        print(p.stdout,end="")
    elif mode in ("adapter_stopped", "adapter_timeout"):
        import importlib.util
        spec=importlib.util.spec_from_file_location("hook",sys.argv[3])
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        code = "import os,signal;os.kill(os.getpid(),signal.SIGTERM)" if mode == "adapter_stopped" else "import time;time.sleep(5)"
        print(json.dumps(module.supervise("codex",json.dumps(x).encode(),os.environ.get("AGENT_CONTEXT_HOME",""),command=[sys.executable,"-c",code],timeout=0.2)))
    elif mode == "exit_two":
        print("synthetic hook failure",file=sys.stderr)
        sys.exit(2)
    elif mode == "timeout":
        time.sleep(5)
    elif mode == "interrupted":
        os.kill(os.getpid(),signal.SIGKILL)
else:
    print("{}")
''', encoding='utf-8')
            import shlex
            command = ' '.join(shlex.quote(str(v)) for v in ('/usr/bin/python3', hook, events_path, mode, HOOK, WATCH))
            handler = {'type': 'command', 'command': command, 'timeout': 1}
            config = {'hooks': {'SessionStart': [{'hooks': [handler]}],
                                'SessionEnd': [{'hooks': [handler]}]}}
            extra_config = []
            if mode == 'config_merge':
                existing = base / 'existing.py'
                existing.write_text('import json,sys;print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":sys.argv[1]}}))\n', encoding='utf-8')
                inline_cmd = ' '.join(shlex.quote(str(v)) for v in ('/usr/bin/python3', existing, 'existing inline hook marker'))
                file_cmd = ' '.join(shlex.quote(str(v)) for v in ('/usr/bin/python3', existing, 'existing file hook marker'))
                (home / 'config.toml').write_text('[[hooks.SessionStart]]\n[[hooks.SessionStart.hooks]]\ntype = "command"\ncommand = ' + json.dumps(inline_cmd) + '\n', encoding='utf-8')
                config['hooks']['SessionStart'] = [{'hooks': [{'type': 'command', 'command': file_cmd}]}]
                extra_config = ['-c', 'hooks.SessionStart=[{ hooks = [{ type = "command", command = ' + json.dumps(command) + ', timeout = 3 }] }]']
            (home / 'hooks.json').write_text(json.dumps(config), encoding='utf-8')

            class Handler(http.server.BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_POST(self):
                    body = self.rfile.read(int(self.headers.get('content-length', '0')))
                    self.server.paths.append(self.path)
                    self.server.marker_seen |= b'agent-context synthetic hook marker' in body
                    self.server.adapter_seen |= b'agent-context session registry' in body
                    self.server.warning_seen |= b'agent-context: hook worker' in body
                    self.server.no_root_seen |= b'AGENT_CONTEXT_HOME is unset' in body
                    self.server.missing_seen |= b'registry is missing or inaccessible' in body
                    self.server.inline_seen |= b'existing inline hook marker' in body
                    self.server.file_seen |= b'existing file hook marker' in body
                    response = {'id': 'resp_fake', 'object': 'response', 'created_at': 0,
                                'status': 'completed', 'model': 'mock-model',
                                'output': [{'id': 'msg_fake', 'type': 'message', 'status': 'completed',
                                            'role': 'assistant', 'content': [{'type': 'output_text',
                                            'text': 'Synthetic response.', 'annotations': []}]}],
                                'usage': {'input_tokens': 1, 'output_tokens': 1, 'total_tokens': 2}}
                    events = [{'type': 'response.created', 'response': {'id': 'resp_fake',
                              'status': 'in_progress', 'output': []}},
                              {'type': 'response.output_item.done', 'output_index': 0,
                               'item': response['output'][0]},
                              {'type': 'response.completed', 'response': response}]
                    payload = ''.join('event: ' + event['type'] + '\ndata: ' + json.dumps(event) + '\n\n'
                                      for event in events).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Content-Length', str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)

            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            server.paths = []
            server.marker_seen = False
            server.adapter_seen = False
            server.warning_seen = False
            server.no_root_seen = False
            server.missing_seen = False
            server.inline_seen = False
            server.file_seen = False
            threading.Thread(target=server.serve_forever, daemon=True).start()
            url = f'http://127.0.0.1:{server.server_port}/v1'
            env = {'PATH': os.environ['PATH'], 'HOME': str(home), 'CODEX_HOME': str(home),
                   'MOCK_KEY': 'local-synthetic-key', 'NO_PROXY': '127.0.0.1,localhost',
                   'AGENT_CONTEXT_HOME': str(base / 'registry'), 'LC_ALL': 'C.UTF-8'}
            provider = ['-c', 'model_provider="local_mock"',
                        '-c', 'model_providers.local_mock.name="Local mock"',
                        '-c', 'model_providers.local_mock.base_url="' + url + '"',
                        '-c', 'model_providers.local_mock.env_key="MOCK_KEY"',
                        '-c', 'model_providers.local_mock.wire_api="responses"',
                        '-c', 'model_providers.local_mock.requires_openai_auth=false',
                        '-c', 'model_providers.local_mock.supports_websockets=false']
            start = time.monotonic()
            try:
                result = run_bounded([sys.executable, str(LAUNCH), '--', codex, 'exec', '--skip-git-repo-check', '--ephemeral',
                                      '--enable', 'hooks', '--dangerously-bypass-hook-trust', '--json',
                                      *provider, *extra_config, '-m', 'mock-model', 'synthetic local hook check'],
                                     cwd=project, env=env, timeout=30)
            finally:
                server.shutdown()
                server.server_close()
            duration = time.monotonic() - start
            recorded = [json.loads(line) for line in events_path.read_text(encoding='utf-8').splitlines()]
            self.assertEqual(recorded[0], {'event': 'SessionStart', 'id_present': True, 'source': 'startup'})
            self.assertEqual(recorded[-1]['event'], 'SessionEnd')
            self.assertTrue(recorded[-1]['id_present'])
            self.assertEqual(server.paths, ['/v1/responses'])
            self.assertEqual(result.returncode, 0, result.stderr[-1000:])
            items = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertTrue(any(item.get('type') == 'turn.completed' for item in items))
            self.assertEqual(server.marker_seen, mode == 'context')
            self.assertEqual(server.adapter_seen, mode in ('adapter', 'config_merge', 'adapter_no_root', 'adapter_missing'))
            self.assertEqual(server.inline_seen, mode == 'config_merge')
            self.assertEqual(server.file_seen, mode == 'config_merge')
            self.assertEqual(server.warning_seen, mode in ('adapter_stopped', 'adapter_timeout'))
            self.assertEqual(server.no_root_seen, mode == 'adapter_no_root')
            self.assertEqual(server.missing_seen, mode == 'adapter_missing')
            if mode in ('exit_two', 'timeout', 'interrupted'):
                self.assertIn('hook was interrupted or did not finish', result.stderr)
            if mode == 'adapter':
                self.assertNotIn('no completed hook event was observed', result.stderr)
            if mode == 'timeout':
                self.assertLess(duration, 12, 'configured one-second timeout did not bound the hook')
            warnings = [item.get('item', {}).get('message', '') for item in items
                        if item.get('item', {}).get('type') == 'error']
            hook_warnings = [message for message in warnings
                             if 'hook' in message.lower() and 'bypass-hook-trust' not in message]
            stderr_hook_lines = [line for line in result.stderr.splitlines()
                                 if 'hook' in line.lower() and 'bypass-hook-trust' not in line]
            hook_statuses = [{'event': item.get('type'), 'kind': item.get('item', {}).get('type'),
                              'status': item.get('item', {}).get('status')}
                             for item in items if 'hook' in str(item.get('item', {}).get('type', '')).lower()]
            print(f'{mode}: completed synthetic turn, session ID observed, {duration:.2f}s; '
                  f'hook warnings: {hook_warnings}; stderr hook lines: {stderr_hook_lines}; '
                  f'hook statuses: {hook_statuses}')


if __name__ == '__main__':
    unittest.main()
