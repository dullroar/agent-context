"""Opt-in Copilot CLI hook tests with a local fake chat provider."""
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

@unittest.skipUnless(os.environ.get('AGENT_CONTEXT_COPILOT_MOCK') == '1',
                     'opt-in test requires an isolated network namespace')
class CopilotMockHookTests(unittest.TestCase):
    def test_start_hook_result_failure_and_timeout(self):
        interfaces = {item['ifname'] for item in json.loads(subprocess.check_output(
            ['ip', '-j', 'link', 'show'], text=True))}
        self.assertEqual(interfaces, {'lo'}, 'refusing to run with non-loopback interfaces')
        copilot = shutil.which('copilot')
        if not copilot:
            self.skipTest('Copilot CLI is unavailable')
        self.run_hook_scenario(copilot, 'context')
        for mode in ('adapter', 'adapter_no_root', 'adapter_missing', 'adapter_stopped', 'adapter_timeout', 'exit_two', 'timeout', 'interrupted'):
            with self.subTest(mode=mode):
                self.run_hook_scenario(copilot, mode)

    def run_hook_scenario(self, copilot, mode):
        with tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT')) as directory:
            base = Path(directory)
            home = base / 'home'
            home.mkdir()
            fake_bin = base / 'fake-bin'
            fake_bin.mkdir()
            fake_gh = fake_bin / 'gh'
            fake_gh.write_text('#!/bin/sh\nexit 1\n', encoding='utf-8')
            fake_gh.chmod(0o700)
            project = base / 'project'
            project.mkdir()
            (base / 'registry').mkdir()
            events_path = base / 'events.jsonl'
            hook = base / 'hook.py'
            hook.write_text('''import json,os,pathlib,signal,subprocess,sys,time
x=json.load(sys.stdin)
event=sys.argv[2]
with pathlib.Path(sys.argv[1]).open("a",encoding="utf-8") as f:
    f.write(json.dumps({"event":event,"id_present":bool(x.get("sessionId")),"source":x.get("source"),"reason":x.get("reason")})+"\\n")
if event == "sessionStart":
    mode=sys.argv[3]
    if mode in ("exit_two", "timeout", "interrupted"):
        import importlib.util
        spec=importlib.util.spec_from_file_location("watch",sys.argv[5])
        watch=importlib.util.module_from_spec(spec); spec.loader.exec_module(watch)
        watch.mark_start(os.environ["AGENT_CONTEXT_HOOK_STATUS_DIR"])
    if mode == "context":
        print(json.dumps({"additionalContext":"agent-context synthetic hook marker"}))
    elif mode in ("adapter", "adapter_no_root", "adapter_missing"):
        env=dict(os.environ)
        if mode == "adapter_no_root": env.pop("AGENT_CONTEXT_HOME",None)
        if mode == "adapter_missing": env["AGENT_CONTEXT_HOME"] += "/missing"
        p=subprocess.run([sys.executable,sys.argv[4],"copilot"],input=json.dumps(x),text=True,capture_output=True,timeout=2,env=env)
        print(p.stdout,end="")
    elif mode in ("adapter_stopped", "adapter_timeout"):
        import importlib.util
        spec=importlib.util.spec_from_file_location("hook",sys.argv[4])
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        code = "import os,signal;os.kill(os.getpid(),signal.SIGTERM)" if mode == "adapter_stopped" else "import time;time.sleep(5)"
        print(json.dumps(module.supervise("copilot",json.dumps(x).encode(),os.environ.get("AGENT_CONTEXT_HOME",""),command=[sys.executable,"-c",code],timeout=0.2)))
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
            def handler(event):
                command = ' '.join(shlex.quote(str(v)) for v in
                                   ('/usr/bin/python3', hook, events_path, event, mode, HOOK, WATCH))
                return {'type': 'command', 'bash': command, 'timeoutSec': 1}
            (home / 'hooks').mkdir()
            config = {'version': 1, 'hooks': {'sessionStart': [handler('sessionStart')],
                                              'sessionEnd': [handler('sessionEnd')]}}
            (home / 'hooks' / 'test.json').write_text(json.dumps(config), encoding='utf-8')

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
                    def chunk(delta, finish=None):
                        return {'id': 'chatcmpl_fake', 'object': 'chat.completion.chunk', 'created': 0,
                                'model': 'mock-model', 'choices': [{'index': 0, 'delta': delta,
                                                                    'finish_reason': finish}]}
                    events = [chunk({'role': 'assistant', 'content': ''}),
                              chunk({'content': 'Synthetic response.'}), chunk({}, 'stop')]
                    payload = (''.join('data: ' + json.dumps(event) + '\n\n' for event in events)
                               + 'data: [DONE]\n\n').encode()
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
            threading.Thread(target=server.serve_forever, daemon=True).start()
            env = {'PATH': str(fake_bin) + os.pathsep + os.environ['PATH'], 'HOME': str(home), 'COPILOT_HOME': str(home),
                   'COPILOT_PROVIDER_BASE_URL': f'http://127.0.0.1:{server.server_port}/v1',
                   'COPILOT_MODEL': 'mock-model', 'COPILOT_PROVIDER_API_KEY': 'local-fake-key',
                   'AGENT_CONTEXT_HOME': str(base / 'registry'),
                   'NO_PROXY': '127.0.0.1,localhost', 'LC_ALL': 'C.UTF-8'}
            start = time.monotonic()
            try:
                command = [sys.executable, str(LAUNCH), '--', copilot, '-p', 'synthetic local hook check', '--trust-folder',
                           '--no-auto-update', '--sync-session=off', '--disable-client-telemetry']
                process = subprocess.Popen(command, cwd=project, env=env, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True, start_new_session=True)
                try:
                    stdout, stderr = process.communicate(timeout=20)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.communicate()
                    raise
                result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
            finally:
                server.shutdown()
                server.server_close()
            duration = time.monotonic() - start
            recorded = [json.loads(line) for line in events_path.read_text(encoding='utf-8').splitlines()]
            self.assertEqual(recorded[0]['event'], 'sessionStart')
            self.assertTrue(recorded[0]['id_present'])
            self.assertIn(recorded[0]['source'], ('new', 'startup'))
            self.assertEqual(recorded[-1]['event'], 'sessionEnd')
            self.assertTrue(recorded[-1]['id_present'])
            self.assertEqual(recorded[-1]['reason'], 'complete')
            self.assertTrue(server.paths)
            self.assertTrue(all(path == '/v1/chat/completions' for path in server.paths))
            self.assertEqual(result.returncode, 0, result.stderr[-1000:])
            self.assertIn('Synthetic response.', result.stdout)
            self.assertEqual(server.marker_seen, mode == 'context')
            self.assertEqual(server.adapter_seen, mode in ('adapter', 'adapter_no_root', 'adapter_missing'))
            self.assertEqual(server.warning_seen, mode in ('adapter_stopped', 'adapter_timeout'))
            self.assertEqual(server.no_root_seen, mode == 'adapter_no_root')
            self.assertEqual(server.missing_seen, mode == 'adapter_missing')
            if mode in ('exit_two', 'timeout', 'interrupted'):
                self.assertIn('hook was interrupted or did not finish', result.stderr)
            if mode == 'adapter':
                self.assertNotIn('no completed hook event was observed', result.stderr)
            if mode == 'timeout':
                self.assertLess(duration, 12, 'configured one-second timeout did not bound the hook')
            hook_lines = [line for line in result.stderr.splitlines() if 'hook' in line.lower()]
            stdout_hook_lines = [line for line in result.stdout.splitlines() if 'hook' in line.lower()]
            print(f'{mode}: completed synthetic turn, session ID observed, {duration:.2f}s; '
                  f'visible hook lines: {stdout_hook_lines + hook_lines}')


if __name__ == '__main__':
    unittest.main()
