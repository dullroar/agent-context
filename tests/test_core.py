import concurrent.futures
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from agent_context import core

FIXTURES = Path(__file__).parent / 'fixtures'
VALID = FIXTURES / 'records' / 'valid'
INVALID = FIXTURES / 'records' / 'invalid'


def sample():
    return core.parse_record((VALID / 'minimal.md').read_bytes())[0]


class CoreTests(unittest.TestCase):
    def setUp(self):
        parent = os.environ.get('AGENT_CONTEXT_TEST_PARENT') or None
        self.temp = tempfile.TemporaryDirectory(prefix='agent context test ', dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'registry with spaces'

    def test_fixtures(self):
        for path in VALID.glob('*.md'):
            with self.subTest(path=path.name):
                data, body = core.parse_record(path.read_bytes())
                self.assertEqual(core.parse_record(core.serialize_record(data, body)), (data, body))
        for path in INVALID.glob('*.md'):
            with self.subTest(path=path.name), self.assertRaises(core.RegistryError):
                core.parse_record(path.read_bytes())

    def test_metadata_rules(self):
        data = sample()
        for field in core.REQUIRED:
            with self.subTest(missing=field), self.assertRaises(core.RegistryError):
                core.validate_metadata({k: v for k, v in data.items() if k != field})
        cases = [
            ('native', {'vendor': 'x'}), ('native', {'vendor': 'x', 'session': 'y', 'other': 'z'}),
            ('native', {'vendor': '', 'session': 'y'}), ('project', {'identity': r'C:\\work\\repo'}),
            ('project', {'identity': 'file:///tmp/repo'}), ('project', {'identity': 'C:relative'}),
            ('project', {'identity': ''}), ('title', '  '), ('title', 'a\x00b'), ('created_at', 'bad'),
            ('status', 'ACTIVE'), ('updated_at', 'not-date'), ('machine', 7), ('resume', ''),
            ('otel_trace_id', False), ('a2a_context_id', ''), ('supersedes', None),
            ('path_hints', {}), ('path_hints', {'wsl': 4}), ('tags', 'a'), ('tags', ['']),
            ('evidence', [3]), ('extra', 'x'),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value), self.assertRaises(core.RegistryError):
                core.validate_metadata(dict(data, **{field: value}))
        for status in core.STATUSES:
            core.validate_metadata(dict(data, status=status))
        with self.assertRaises(core.RegistryError):
            core.serialize_record(data, 'bad\x01body')
        with self.assertRaises(core.RegistryError):
            core.serialize_record(data, 'bad\x85body')
        with self.assertRaises(core.RegistryError):
            core.parse_record(b'---\n[not: mapping]\n---\n')

    def test_filename_cases_and_generation(self):
        cases = json.loads((FIXTURES / 'filenames.json').read_text(encoding='utf-8'))
        for value in cases['valid']:
            with self.subTest(value=value): core.validate_filename(value)
        for value in cases['invalid']:
            with self.subTest(value=value), self.assertRaises(core.RegistryError): core.validate_filename(value)
        record_id = sample()['id']
        self.assertEqual(core.filename_for('agent', record_id, '你好'), 'agent-0123456789ab-topic.md')
        ambiguous = core.filename_for('agent', record_id, 'abcdefabcdef more')
        core.validate_filename(ambiguous, record_id)
        nested = core.filename_for('a-abcdefabcdef', record_id, 'title')
        core.validate_filename(nested, record_id)
        name = core.filename_for('a'*24, record_id, 'long ' * 50)
        self.assertLessEqual(len(name.encode('ascii')), 80)
        self.assertFalse(name[:-3].endswith('-'))
        for producer in ['', 'CON', 'con', 'a_b', 'a--b', 'a' * 25, '../x']:
            with self.subTest(producer=producer), self.assertRaises(core.RegistryError):
                core.filename_for(producer, record_id, 'title')
        with self.assertRaises(core.RegistryError):
            core.validate_filename('agent-ffffffffffff-topic.md', record_id)

    def test_root_resolution(self):
        with mock.patch.dict(os.environ, {'AGENT_CONTEXT_HOME': str(self.root)}, clear=True):
            self.assertEqual(core.resolve_root(), self.root.resolve())
        if os.name == 'nt':
            with mock.patch.dict(os.environ, {'LOCALAPPDATA': str(self.root)}, clear=True):
                self.assertEqual(core.resolve_root(), (self.root / 'agent-context').resolve())
        else:
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(core.Path, 'home', return_value=Path('/home/example')):
                self.assertEqual(core.resolve_root(), Path('/home/example/.local/share/agent-context'))

    def test_register_collision_and_two_topics(self):
        data = sample()
        path, first = core.register(self.root, 'agent', data, 'one')
        self.assertEqual(core.read_record(path), (first, 'one'))
        original = path.read_bytes()
        second_id = 'acr_' + 'f' * 32
        with mock.patch.object(core, 'new_id', side_effect=[first['id'], second_id]):
            other, second = core.register(self.root, 'agent', data, 'two')
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(second['id'], second_id)
        self.assertEqual(first['native']['session'], second['native']['session'])
        self.assertNotEqual(path, other)
        self.assertEqual(len(core.records(self.root)[0]), 2)

    def test_new_record_is_complete_before_publication(self):
        real_link = core.os.link
        def inspect_then_link(source, destination):
            self.assertFalse(Path(destination).exists())
            data, body = core.parse_record(Path(source).read_bytes())
            self.assertEqual(data['native']['session'], sample()['native']['session'])
            self.assertEqual(body, 'complete')
            real_link(source, destination)
        with mock.patch.object(core.os, 'link', side_effect=inspect_then_link):
            path, _ = core.register(self.root, 'agent', sample(), 'complete')
        self.assertTrue(path.exists())
        self.assertEqual([p.name for p in self.root.iterdir()], [path.name])

    def test_search_fields_and_unicode(self):
        p, data = core.register(self.root, 'agent', sample())
        items = core.records(self.root)[0]
        for query in ('CAFÉ', 'TEAM/REPO', 'CODEX', data['id'][6:14]):
            with self.subTest(query=query): self.assertEqual(core.search_records(items, query)[0][0], p)
        self.assertEqual(core.search_records(items, 'absent'), [])

    def test_rename_changes_discovery_text_not_identity(self):
        path, data = core.register(self.root, 'agent', sample())
        renamed = path.with_name(core.filename_for('agent', data['id'], 'new subject'))
        path.rename(renamed)
        recovered, _ = core.read_record(renamed)
        self.assertEqual(recovered['id'], data['id'])
        self.assertEqual(recovered['native']['session'], data['native']['session'])

    def test_snapshot_closes_source_before_parsing(self):
        path, data = core.register(self.root, 'agent', sample())
        opened = []
        original_open = Path.open
        original_parse = core.parse_record
        def track_open(source, *args, **kwargs):
            stream = original_open(source, *args, **kwargs)
            if source == path:
                opened.append(stream)
            return stream
        def check_closed(raw):
            self.assertTrue(opened and opened[-1].closed)
            return original_parse(raw)
        if os.name == 'nt':
            self.skipTest('Windows opens with explicit sharing flags; see Windows sharing test')
        with mock.patch.object(Path, 'open', track_open), mock.patch.object(core, 'parse_record', side_effect=check_closed):
            self.assertEqual(core.read_record(path)[0]['id'], data['id'])

    @unittest.skipUnless(os.name == 'nt', 'Windows sharing behavior')
    def test_windows_snapshot_allows_replacement_during_read(self):
        path, data = core.register(self.root, 'agent', sample())
        replacement = self.root / 'replacement.tmp'
        replacement.write_bytes(core.serialize_record(dict(data, status='completed')))
        real_fdopen = core.os.fdopen
        real_parse = core.parse_record
        closed = []
        def intercept(fd, mode):
            stream = real_fdopen(fd, mode)
            class Reader:
                def __enter__(self): return self
                def __exit__(self, *args):
                    stream.close()
                    closed.append(stream.closed)
                def read(self):
                    env = os.environ.copy()
                    env['PYTHONPATH'] = str(Path(__file__).resolve().parents[1] / 'src')
                    result = subprocess.run([sys.executable, '-c',
                        'from agent_context.core import _replace_file; import sys; _replace_file(sys.argv[1], sys.argv[2])',
                        str(replacement), str(path)], env=env, timeout=30)
                    if result.returncode:
                        raise AssertionError(f'concurrent replacement failed: {result.returncode}')
                    return stream.read()
            return Reader()
        def parse_after_close(raw):
            self.assertEqual(closed, [True])
            return real_parse(raw)
        with mock.patch.object(core.os, 'fdopen', side_effect=intercept), mock.patch.object(core, 'parse_record', side_effect=parse_after_close):
            old, _ = core.read_record(path)
        self.assertEqual(old['status'], data['status'])
        self.assertEqual(core.read_record(path)[0]['status'], 'completed')

    def test_parallel_independent_creates(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            result = list(pool.map(lambda i: core.register(self.root, 'agent', dict(sample(), title=f'topic {i}')), range(40)))
        self.assertEqual(len({p for p, _ in result}), 40)
        self.assertEqual(len({r['id'] for _, r in result}), 40)
        self.assertEqual(len(core.records(self.root)[0]), 40)
        self.assertEqual(core.records(self.root)[1], [])

    def test_write_and_replace_failure_preserve_existing(self):
        path, data = core.register(self.root, 'agent', sample(), 'original')
        original = path.read_bytes()
        with mock.patch.object(core.os, 'fsync', side_effect=OSError('simulated failure')):
            with self.assertRaises(OSError): core.register(self.root, 'agent', dict(data, title='another'))
            with self.assertRaises(OSError): core.replace_record(path, dict(data, status='completed'), 'new')
        with mock.patch.object(core.os, 'link', side_effect=OSError('link unavailable')):
            with self.assertRaises(OSError): core.register(self.root, 'agent', dict(data, title='another'))
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual([p.name for p in self.root.iterdir()], [path.name])
        other_id = data['id'][:16] + ('f' * 20 if data['id'][16:] != 'f' * 20 else 'a' * 20)
        with self.assertRaises(core.RegistryError):
            core.replace_record(path, dict(data, id=other_id), 'wrong record')
        self.assertEqual(path.read_bytes(), original)
        core.replace_record(path, dict(data, status='completed'), 'new')
        self.assertEqual(core.read_record(path)[0]['status'], 'completed')
        self.assertEqual(core.read_record(path)[1], 'new')

    def test_bad_files_reported_and_id_consistency(self):
        path, data = core.register(self.root, 'agent', sample())
        path.rename(self.root / 'agent-ffffffffffff-topic.md')
        (self.root / 'unsafe name.md').write_text('bad', encoding='utf-8')
        (self.root / 'unsafe.md.').write_text('bad', encoding='utf-8')
        items, errors = core.records(self.root)
        self.assertEqual(items, [])
        self.assertEqual(len(errors), 3)
        self.assertEqual(core.records(self.root / 'missing'), ([], []))
        with self.assertRaises(core.RegistryError):
            core.records(self.root / 'unsafe.md.')

    def test_scan_reports_an_unavailable_record_without_losing_others(self):
        missing, _ = core.register(self.root, 'agent', sample())
        other, _ = core.register(self.root, 'agent', dict(sample(), title='other'))
        read = core.read_record
        for exception in (FileNotFoundError('concurrent removal'), PermissionError('sharing or access denied')):
            def unavailable(path):
                if path == missing:
                    raise exception
                return read(path)
            with self.subTest(exception=exception), mock.patch.object(core, 'read_record', side_effect=unavailable):
                items, errors = core.records(self.root)
                self.assertEqual([item[0] for item in items], [other])
                self.assertEqual(len(errors), 1)
                self.assertIsInstance(errors[0][1], core.RecordBusy)


if __name__ == '__main__': unittest.main()
