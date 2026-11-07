import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='agent context cli ', dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT') or None)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'registry with spaces'
        self.env = os.environ.copy()
        self.env['AGENT_CONTEXT_HOME'] = str(self.root)
        self.env['PYTHONPATH'] = str(Path(__file__).resolve().parents[1] / 'src')
        self.env['PYTHONIOENCODING'] = 'ascii'

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, '-m', 'agent_context', *args], text=True, encoding='utf-8', capture_output=True, env=self.env, timeout=30)
        self.assertEqual(result.returncode, expected, (result.stdout, result.stderr))
        self.assertIn(f'Registry root: {self.root}', result.stderr)
        return result

    def register(self, title='Café loan work', **kw):
        args = ['register', '--vendor', 'Codex Agent', '--session', 'opaque / 你好:1', '--project', 'git:https://example.invalid/team/repo', '--title', title, '--producer', 'codex']
        for name, value in kw.items():
            args += ['--' + name.replace('_', '-'), value]
        return self.cli(*args)

    def test_end_to_end_and_two_topics(self):
        first = self.register(body='UTF-8 note 你好', windows_path=r'C:\\Users\\A B\\repo', wsl_path='/mnt/c/Users/A B/repo', status='active',
                              machine='laptop', resume='opaque resume', updated_at='2026-11-07T10:00:00Z',
                              otel_trace_id='trace', a2a_context_id='context', supersedes='acr_old',
                              tag='audit', evidence='https://example.invalid/evidence')
        second = self.register(title='Another topic')
        id1 = first.stdout.split('\t')[0]
        id2 = second.stdout.split('\t')[0]
        self.assertNotEqual(id1, id2)
        listing = self.cli('list').stdout
        self.assertIn(id1, listing)
        self.assertIn(id2, listing)
        for query in ('CAFÉ', 'TEAM/REPO', 'CODEX AGENT', id1[5:15]):
            with self.subTest(query=query): self.assertIn(id1, self.cli('search', query).stdout)
        self.assertNotIn(id1, self.cli('search', 'not present').stdout)
        shown = self.cli('show', id1[4:16]).stdout
        self.assertIn('opaque / 你好:1', shown)
        self.assertIn('UTF-8 note 你好', shown)
        self.assertIn('windows:', shown)
        for field in ('machine:', 'resume:', 'updated_at:', 'otel_trace_id:', 'a2a_context_id:', 'supersedes:', 'tags:', 'evidence:'):
            self.assertIn(field, shown)
        self.assertIn('2 valid, 0 invalid', self.cli('validate').stdout)
        file = Path(first.stdout.strip().split('\t', 1)[1])
        self.assertIn('valid:', self.cli('validate', str(file)).stdout)
        self.cli('show', 'acr_', expected=1)
        self.cli('show', 'no-such-id', expected=1)

    def test_invalid_and_write_failure(self):
        self.register()
        existing = list(self.root.glob('*.md'))[0]
        content = existing.read_bytes()
        self.cli('register', '--vendor', 'x', '--session', 'x', '--project', '/local/path', '--title', 'x', '--producer', 'codex', expected=1)
        self.cli('register', '--vendor', 'x', '--session', 'x', '--project', 'repo-id', '--title', 'x', '--producer', 'codex', '--created-at', '', expected=1)
        self.assertEqual(existing.read_bytes(), content)
        bad = self.root / 'bad name.md'
        bad.write_text('bad metadata', encoding='utf-8')
        self.cli('validate', str(bad), expected=1)
        self.cli('list', expected=1)
        self.cli('search', 'x', expected=1)
        self.cli('validate', expected=1)
        bad.unlink()
        blocked = Path(self.temp.name) / 'not a directory'
        blocked.write_text('preserve me', encoding='utf-8')
        self.env['AGENT_CONTEXT_HOME'] = str(blocked / 'child')
        self.root = blocked / 'child'
        self.register_failure()
        self.assertEqual(blocked.read_text(encoding='utf-8'), 'preserve me')
        self.assertEqual(existing.read_bytes(), content)

    def test_independent_concurrent_processes(self):
        command = [sys.executable, '-m', 'agent_context', 'register', '--producer', 'codex',
                   '--vendor', 'vendor', '--session', 'same opaque session', '--project',
                   'git:example/repo', '--title', 'same topic']
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True, encoding='utf-8', env=self.env) for _ in range(12)]
        ids = set()
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, stderr)
            ids.add(stdout.split('\t', 1)[0])
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(list(self.root.glob('*.md'))), 12)
        self.assertIn('12 valid, 0 invalid', self.cli('validate').stdout)

    @unittest.skipIf(os.name == 'nt', 'POSIX advisory-lock behavior')
    def test_listing_does_not_wait_for_advisory_writer_lock(self):
        import fcntl
        result = self.register()
        record = Path(result.stdout.strip().split('\t', 1)[1])
        with record.open('rb') as writer:
            fcntl.flock(writer, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertIn('Café loan work', self.cli('list').stdout)
            for program, options in (('cat', []), ('less', ['-F', '-X'])):
                with self.subTest(reader=program):
                    executable = shutil.which(program)
                    if not executable:
                        raise unittest.SkipTest(f'{program} is not installed')
                    result = subprocess.run([executable, *options, str(record)], capture_output=True,
                                            env=dict(self.env, TERM='dumb', LESS=''), timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, record.read_bytes())

    @unittest.skipUnless(os.name == 'nt', 'Windows sharing behavior')
    def test_locked_record_is_reported_without_failing_scripts(self):
        import ctypes
        from ctypes import wintypes
        result = self.register(title='busy')
        self.register(title='readable')
        record = Path(result.stdout.strip().split('\t', 1)[1])
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.CreateFileW(str(record), 0x40000000, 0, None, 3, 0x80, None)
        self.assertNotEqual(handle, wintypes.HANDLE(-1).value)
        try:
            listed = self.cli('list')
            self.assertIn('readable', listed.stdout)
            self.assertIn('temporarily unavailable', listed.stderr)
            self.assertIn('readable', self.cli('search', 'readable').stdout)
            self.assertIn('1 unavailable', self.cli('validate').stdout)
            self.assertIn('unavailable:', self.cli('validate', str(record)).stdout)
            shown = self.cli('show', result.stdout.split('\t', 1)[0])
            self.assertEqual(shown.stdout, '')
            self.assertIn('no record shown', shown.stderr)
            type_result = subprocess.run(['cmd.exe', '/d', '/c', 'type', str(record)],
                                         cwd=self.temp.name, capture_output=True, timeout=5)
            self.assertNotEqual(type_result.returncode, 0)
        finally:
            kernel.CloseHandle(handle)
        handle = kernel.CreateFileW(str(record), 0x40000000, 7, None, 3, 0x80, None)
        self.assertNotEqual(handle, wintypes.HANDLE(-1).value)
        try:
            self.assertIn('busy', self.cli('search', 'busy').stdout)
            type_result = subprocess.run(['cmd.exe', '/d', '/c', 'type', str(record)],
                                         cwd=self.temp.name, capture_output=True, timeout=5)
            self.assertEqual(type_result.returncode, 0, type_result.stderr)
            self.assertIn(b'busy', type_result.stdout)
        finally:
            kernel.CloseHandle(handle)

    @unittest.skipUnless(os.name != 'nt' and os.environ.get('AGENT_CONTEXT_CROSS_TEST') == '1',
                         'requires WSL, Windows Python and the shared test mount')
    def test_wsl_readers_with_exclusive_windows_writer(self):
        windows_python = shutil.which('python.exe')
        wslpath = shutil.which('wslpath')
        self.assertTrue(windows_python and wslpath, 'Windows Python and wslpath are required')
        result = self.register(title='locked cross-host')
        self.register(title='readable cross-host')
        record_id, record_path = result.stdout.strip().split('\t', 1)
        record = Path(record_path)
        base = Path(self.temp.name)
        script, ready, stop = (base / name for name in ('writer.py', 'ready', 'stop'))
        script.write_text('''import ctypes, pathlib, sys, time
from ctypes import wintypes
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
k.CreateFileW.restype=wintypes.HANDLE
k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.CreateFileW(sys.argv[1],0x40000000,0,None,3,0x80,None)
if h==wintypes.HANDLE(-1).value: raise ctypes.WinError(ctypes.get_last_error())
try:
    pathlib.Path(sys.argv[2]).write_text('ready')
    deadline=time.monotonic()+30
    while not pathlib.Path(sys.argv[3]).exists() and time.monotonic()<deadline: time.sleep(.05)
finally: k.CloseHandle(h)
''', encoding='utf-8')
        def winpath(path):
            return subprocess.run([wslpath, '-w', str(path)], check=True, capture_output=True,
                                  text=True, timeout=5).stdout.strip()
        writer = subprocess.Popen([windows_python, *(winpath(p) for p in (script, record, ready, stop))],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 10
            while not ready.exists() and writer.poll() is None and time.monotonic() < deadline:
                time.sleep(.05)
            self.assertTrue(ready.exists(), 'Windows writer failed to become ready')
            listed = self.cli('list')
            self.assertIn('readable cross-host', listed.stdout)
            self.assertNotIn('locked cross-host', listed.stdout)
            self.assertIn('record unavailable', listed.stderr)
            self.assertIn('1 unavailable', self.cli('validate').stdout)
            self.assertIn('unavailable:', self.cli('validate', str(record)).stdout)
            shown = self.cli('show', record_id)
            self.assertEqual(shown.stdout, '')
            self.assertIn('no record shown', shown.stderr)
            for program, options in (('cat', []), ('less', ['-F', '-X'])):
                with self.subTest(reader=program):
                    executable = shutil.which(program)
                    if not executable:
                        raise unittest.SkipTest(f'{program} is not installed')
                    read = subprocess.run([executable, *options, str(record)], capture_output=True,
                                          env=dict(self.env, TERM='dumb', LESS=''), timeout=5)
                    self.assertNotIn(record_id.encode(), read.stdout)
        finally:
            stop.touch()
            try:
                _, err = writer.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                writer.kill()
                _, err = writer.communicate()
                self.fail('Windows writer did not stop')
            self.assertEqual(writer.returncode, 0, err)
    def register_failure(self):
        self.cli('register', '--vendor', 'x', '--session', 'x', '--project', 'repo-id', '--title', 'x', '--producer', 'codex', expected=1)


if __name__ == '__main__': unittest.main()
