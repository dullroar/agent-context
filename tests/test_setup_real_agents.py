"""Optional, no-prompt checks against installed Linux agent executables."""
import os
from pathlib import Path
import signal
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


def process_tree(root_pid):
    pending, seen = [root_pid], set()
    while pending:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid)
        yield pid
        try:
            children = (Path('/proc') / str(pid) / 'task' / str(pid) / 'children').read_text().split()
            pending.extend(int(child) for child in children)
        except (OSError, ValueError):
            pass


@unittest.skipUnless(os.environ.get('AGENT_CONTEXT_SETUP_REAL_AGENTS') == '1' and
                     os.name == 'posix' and Path('/proc/self/environ').exists(),
                     'opt-in check requires Linux /proc and real agent CLIs')
class RealAgentWrapperTests(unittest.TestCase):
    def test_real_agents_receive_selected_root_without_a_prompt(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT')) as directory:
            base = Path(directory)
            home = base / 'isolated home'
            home.mkdir()
            registry = base / "registry's space"
            integrations = base / 'integrations'
            # Do not pass credentials or a personal configuration into the
            # agent processes. These probes run only --version and --help.
            env = {'PATH': os.environ.get('PATH', ''), 'LC_ALL': 'C.UTF-8'}
            env.update({
                'HOME': str(home),
                'CODEX_HOME': str(home / 'codex'),
                'CLAUDE_CONFIG_DIR': str(home / 'claude'),
                'COPILOT_HOME': str(home / 'copilot'),
                'XDG_CACHE_HOME': str(home / 'cache'),
                'XDG_DATA_HOME': str(home / 'data'),
                'XDG_STATE_HOME': str(home / 'state'),
                'AGENT_CONTEXT_SETUP_HOME': str(integrations),
            })
            installed = [name for name in ('codex', 'claude', 'copilot') if shutil.which(name, path=env['PATH'])]
            if not installed:
                self.skipTest('no agent executables are available')
            result = subprocess.run([str(ROOT / 'scripts' / 'setup.sh'), str(registry)],
                                    env=env, text=True, capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for name in installed:
                with self.subTest(agent=name):
                    wrapper = integrations / name / name
                    self.assertTrue(wrapper.is_file(), name + ' was not installed')
                    process = subprocess.Popen([str(wrapper), '--version'], env=env,
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
                    found = False
                    try:
                        deadline = time.monotonic() + 5
                        while process.poll() is None and time.monotonic() < deadline:
                            for pid in process_tree(process.pid):
                                try:
                                    proc = Path('/proc') / str(pid)
                                    exe = os.path.basename(os.readlink(proc / 'exe'))
                                    cmdline = (proc / 'cmdline').read_bytes().lower()
                                    environment = (proc / 'environ').read_bytes().split(b'\0')
                                    native_process = (exe not in ('sh', 'bash', 'env') and not exe.startswith('python') and
                                                      (name.encode() in cmdline or (name == 'copilot' and b'npm-loader' in cmdline)))
                                    if native_process and os.fsencode('AGENT_CONTEXT_HOME=' + str(registry)) in environment:
                                        found = True
                                        break
                                except (FileNotFoundError, ProcessLookupError, PermissionError):
                                    pass
                            if found:
                                break
                            time.sleep(0.001)
                        stdout, stderr = process.communicate(timeout=10)
                    finally:
                        if process.poll() is None:
                            try:
                                os.killpg(process.pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                            process.communicate()
                    self.assertEqual(process.returncode, 0, (stdout + stderr).decode(errors='replace'))
                    self.assertTrue(found, 'did not observe the selected root in the real agent process')
                    print(f'{name}: selected root observed in --version process')


if __name__ == '__main__':
    unittest.main()
