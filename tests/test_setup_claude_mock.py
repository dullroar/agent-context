"""Opt-in Claude Code hook tests with a local fake Messages server."""
import http.server
import json
import os
from pathlib import Path
import shlex
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

@unittest.skipUnless(os.environ.get('AGENT_CONTEXT_CLAUDE_MOCK') == '1',
                     'opt-in test requires an isolated network namespace')
class ClaudeMockHookTests(unittest.TestCase):
    def test_start_hook_result_failure_and_timeout(self):
        interfaces = {item['ifname'] for item in json.loads(subprocess.check_output(
            ['ip', '-j', 'link', 'show'], text=True))}
        self.assertEqual(interfaces, {'lo'}, 'refusing to run with non-loopback interfaces')
        claude = shutil.which('claude')
        if not claude:
            self.skipTest('Claude Code CLI is unavailable')
        for mode in ('context', 'adapter', 'settings_merge', 'adapter_no_root', 'adapter_missing', 'adapter_stopped', 'adapter_timeout', 'exit_two', 'timeout', 'interrupted'):
            with self.subTest(mode=mode):
                self.run_hook_scenario(claude, mode)

    def run_hook_scenario(self, claude, mode):
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
with p.open("a",encoding="utf-8") as f:
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
    elif mode in ("adapter", "settings_merge", "adapter_no_root", "adapter_missing"):
        env=dict(os.environ)
        if mode == "adapter_no_root": env.pop("AGENT_CONTEXT_HOME",None)
        if mode == "adapter_missing": env["AGENT_CONTEXT_HOME"] += "/missing"
        p=subprocess.run([sys.executable,sys.argv[3],"claude"],input=json.dumps(x),text=True,capture_output=True,timeout=2,env=env)
        print(p.stdout,end="")
    elif mode in ("adapter_stopped", "adapter_timeout"):
        import importlib.util
        spec=importlib.util.spec_from_file_location("hook",sys.argv[3])
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        code = "import os,signal;os.kill(os.getpid(),signal.SIGTERM)" if mode == "adapter_stopped" else "import time;time.sleep(5)"
        print(json.dumps(module.supervise("claude",json.dumps(x).encode(),os.environ.get("AGENT_CONTEXT_HOME",""),command=[sys.executable,"-c",code],timeout=0.2)))
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
            command = ' '.join(shlex.quote(str(v)) for v in ('/usr/bin/python3', hook, events_path, mode, HOOK, WATCH))
            handler = {'type': 'command', 'command': command, 'timeout': 1}
            config = {'hooks': {'SessionStart': [{'hooks': [handler]}],
                                'SessionEnd': [{'hooks': [handler]}]}}
            overlay_args = []
            if mode == 'settings_merge':
                existing = base / 'existing.py'
                existing.write_text('import json;print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"existing user hook marker"}}))\n', encoding='utf-8')
                existing_cmd = ' '.join(shlex.quote(str(v)) for v in ('/usr/bin/python3', existing))
                user_config = {'hooks': {'SessionStart': [{'hooks': [{'type': 'command', 'command': existing_cmd}]}]}}
                (home / 'settings.json').write_text(json.dumps(user_config), encoding='utf-8')
                overlay = base / 'overlay.json'
                overlay.write_text(json.dumps(config), encoding='utf-8')
                overlay_args = ['--settings', str(overlay)]
            else:
                (home / 'settings.json').write_text(json.dumps(config), encoding='utf-8')

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
                    self.server.existing_seen |= b'existing user hook marker' in body
                    if '/messages' not in self.path:
                        payload = b'{}'
                        content_type = 'application/json'
                    else:
                        usage = {'input_tokens': 1, 'output_tokens': 1,
                                 'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}
                        events = [{'type': 'message_start', 'message': {'id': 'msg_fake', 'type': 'message',
                                  'role': 'assistant', 'content': [], 'model': 'claude-sonnet-4-5',
                                  'stop_reason': None, 'stop_sequence': None, 'usage': usage}},
                                  {'type': 'content_block_start', 'index': 0,
                                   'content_block': {'type': 'text', 'text': ''}},
                                  {'type': 'content_block_delta', 'index': 0,
                                   'delta': {'type': 'text_delta', 'text': 'Synthetic response.'}},
                                  {'type': 'content_block_stop', 'index': 0},
                                  {'type': 'message_delta', 'delta': {'stop_reason': 'end_turn',
                                   'stop_sequence': None}, 'usage': {'output_tokens': 1}},
                                  {'type': 'message_stop'}]
                        payload = ''.join('event: ' + event['type'] + '\ndata: ' + json.dumps(event) + '\n\n'
                                          for event in events).encode()
                        content_type = 'text/event-stream'
                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
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
            server.existing_seen = False
            threading.Thread(target=server.serve_forever, daemon=True).start()
            env = {'PATH': os.environ['PATH'], 'HOME': str(home), 'CLAUDE_CONFIG_DIR': str(home),
                   'ANTHROPIC_API_KEY': 'local-fake-key',
                   'ANTHROPIC_BASE_URL': f'http://127.0.0.1:{server.server_port}',
                   'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
                   'AGENT_CONTEXT_HOME': str(base / 'registry'),
                   'NO_PROXY': '127.0.0.1,localhost', 'LC_ALL': 'C.UTF-8'}
            start = time.monotonic()
            try:
                result = run_bounded([sys.executable, str(LAUNCH), '--', claude, '-p', 'synthetic local hook check',
                                      '--model', 'claude-sonnet-4-5', '--output-format', 'json', *overlay_args],
                                     cwd=project, env=env, timeout=30)
            finally:
                server.shutdown()
                server.server_close()
            duration = time.monotonic() - start
            recorded = [json.loads(line) for line in events_path.read_text(encoding='utf-8').splitlines()]
            self.assertEqual(recorded[0], {'event': 'SessionStart', 'id_present': True, 'source': 'startup'})
            self.assertEqual(recorded[-1]['event'], 'SessionEnd')
            self.assertTrue(recorded[-1]['id_present'])
            self.assertEqual(server.paths, ['/v1/messages?beta=true'])
            self.assertEqual(result.returncode, 0, result.stderr[-1000:])
            message = json.loads(result.stdout)
            self.assertFalse(message['is_error'])
            self.assertEqual(message['result'], 'Synthetic response.')
            self.assertEqual(server.marker_seen, mode == 'context')
            self.assertEqual(server.adapter_seen, mode in ('adapter', 'settings_merge', 'adapter_no_root', 'adapter_missing'))
            self.assertEqual(server.existing_seen, mode == 'settings_merge')
            self.assertEqual(server.warning_seen, mode in ('adapter_stopped', 'adapter_timeout'))
            self.assertEqual(server.no_root_seen, mode == 'adapter_no_root')
            self.assertEqual(server.missing_seen, mode == 'adapter_missing')
            if mode in ('exit_two', 'timeout', 'interrupted'):
                self.assertIn('hook was interrupted or did not finish', result.stderr)
            if mode == 'adapter':
                self.assertNotIn('no completed hook event was observed', result.stderr)
            if mode == 'timeout':
                self.assertLess(duration, 10, 'configured one-second timeout did not bound the hook')
            hook_lines = [line for line in result.stderr.splitlines() if 'hook' in line.lower()]
            print(f'{mode}: completed synthetic turn, session ID observed, {duration:.2f}s; '
                  f'stderr hook lines: {hook_lines}')


if __name__ == '__main__':
    unittest.main()
