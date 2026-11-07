"""Record parsing, validation and filesystem operations."""
from __future__ import annotations

import datetime as dt
import errno
import ntpath
import os
from pathlib import Path
import re
import tempfile
import unicodedata
import uuid

import yaml
from yaml.events import AliasEvent


class RegistryError(ValueError):
    """Invalid record, input or registry operation."""


class RecordBusy(OSError):
    """A file is temporarily unavailable due to a sharing or lock conflict."""


class RecordLoader(yaml.SafeLoader):
    # Do not mutate SafeLoader's global resolvers. Timestamps must remain strings.
    yaml_implicit_resolvers = {
        key: [(tag, regexp) for tag, regexp in resolvers
              if tag != 'tag:yaml.org,2002:timestamp']
        for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }

    def compose_node(self, parent, index):
        if self.check_event(AliasEvent):
            raise RegistryError('YAML aliases are not supported')
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise RegistryError('metadata keys must be strings')
            if key in result:
                raise RegistryError(f'duplicate key: {key}')
            result[key] = self.construct_object(value_node, deep=deep)
        return result


REQUIRED = {'id', 'native', 'project', 'title', 'created_at', 'status'}
OPTIONAL_STRINGS = {'machine', 'resume', 'otel_trace_id', 'a2a_context_id', 'supersedes'}
OPTIONAL = OPTIONAL_STRINGS | {'path_hints', 'updated_at', 'tags', 'evidence'}
STATUSES = {'active', 'paused', 'completed', 'abandoned', 'unknown'}
ID_RE = re.compile(r'acr_[0-9a-f]{32}\Z')
SEGMENT_RE = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
SHORT_ID_RE = re.compile(r'(?=\-([0-9a-f]{12})\-)')
DEVICES = {'con', 'prn', 'aux', 'nul'} | {f'{x}{i}' for x in ('com', 'lpt') for i in range(1, 10)}


def resolve_root():
    configured = os.environ.get('AGENT_CONTEXT_HOME')
    if configured:
        return Path(configured).expanduser().resolve()
    if os.name == 'nt':
        return (Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'agent-context').resolve()
    return (Path.home() / '.local' / 'share' / 'agent-context').resolve()


def _string(value, field):
    if not isinstance(value, str) or not value.strip() or any(unicodedata.category(c) == 'Cc' for c in value):
        raise RegistryError(f'{field} must be a nonempty string without control characters')


def _timestamp(value, field):
    _string(value, field)
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise RegistryError(f'{field} must be an ISO 8601 timestamp with timezone') from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RegistryError(f'{field} must include a timezone')


def validate_metadata(data):
    if not isinstance(data, dict) or any(not isinstance(k, str) for k in data):
        raise RegistryError('metadata must be a string-keyed mapping')
    missing, extra = REQUIRED - data.keys(), data.keys() - REQUIRED - OPTIONAL
    if missing or extra:
        raise RegistryError(f'missing fields: {sorted(missing)}; unknown fields: {sorted(extra)}')
    _string(data['id'], 'id')
    if not ID_RE.fullmatch(data['id']):
        raise RegistryError('invalid id')
    for key, fields in (('native', {'vendor', 'session'}), ('project', {'identity'})):
        mapping = data[key]
        if not isinstance(mapping, dict) or set(mapping) != fields:
            raise RegistryError(f'{key} must contain exactly {sorted(fields)}')
        for field in fields:
            _string(mapping[field], f'{key}.{field}')
    identity = data['project']['identity']
    if identity.startswith('/') or ntpath.isabs(identity) or re.match(r'^[a-zA-Z]:', identity) or identity.lower().startswith('file:'):
        raise RegistryError('project.identity must be environment-neutral, not a local path')
    _string(data['title'], 'title')
    _timestamp(data['created_at'], 'created_at')
    _string(data['status'], 'status')
    if data['status'] not in STATUSES:
        raise RegistryError('invalid status')
    for key in OPTIONAL_STRINGS & data.keys():
        _string(data[key], key)
    if 'updated_at' in data:
        _timestamp(data['updated_at'], 'updated_at')
    if 'path_hints' in data:
        hints = data['path_hints']
        if not isinstance(hints, dict) or not hints or not set(hints) <= {'windows', 'wsl'}:
            raise RegistryError('path_hints must contain windows and/or wsl')
        for key, value in hints.items():
            _string(value, f'path_hints.{key}')
    for key in ('tags', 'evidence'):
        if key in data:
            if not isinstance(data[key], list):
                raise RegistryError(f'{key} must be a list')
            for value in data[key]:
                _string(value, key)
    return data


def validate_body(body):
    if not isinstance(body, str) or any(unicodedata.category(c) == 'Cc' and c not in '\n\r\t' for c in body):
        raise RegistryError('body contains invalid control characters')


def parse_record(raw):
    try:
        text = raw.decode('utf-8') if isinstance(raw, bytes) else raw
    except UnicodeDecodeError as exc:
        raise RegistryError('record is not UTF-8') from exc
    if not isinstance(text, str):
        raise RegistryError('record must be UTF-8 text')
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip('\r\n') != '---':
        raise RegistryError('missing opening front matter delimiter')
    end = next((i for i in range(1, len(lines)) if lines[i].rstrip('\r\n') == '---'), None)
    if end is None:
        raise RegistryError('missing closing front matter delimiter')
    try:
        data = yaml.load(''.join(lines[1:end]), Loader=RecordLoader)
    except yaml.YAMLError as exc:
        raise RegistryError(f'invalid YAML: {exc}') from exc
    body = ''.join(lines[end + 1:])
    validate_metadata(data)
    validate_body(body)
    return data, body


def serialize_record(data, body=''):
    validate_metadata(data)
    validate_body(body)
    metadata = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return ('---\n' + metadata + '---\n' + body).encode('utf-8')


def validate_producer(producer):
    if not isinstance(producer, str) or len(producer) > 24 or not SEGMENT_RE.fullmatch(producer) or producer in DEVICES:
        raise RegistryError('producer must be 1-24 safe lowercase ASCII characters and not a device name')


def validate_filename(name, record_id=None):
    if not isinstance(name, str) or not name.isascii() or len(name.encode('ascii')) > 80 or '/' in name or '\\' in name:
        raise RegistryError('unsafe filename')
    if name.endswith('.md'):
        stem = name[:-3]
        for match in SHORT_ID_RE.finditer(stem):
            producer, slug = stem[:match.start()], stem[match.start() + 14:]
            try:
                validate_producer(producer)
            except RegistryError:
                continue
            if SEGMENT_RE.fullmatch(slug) and (record_id is None or match.group(1) == record_id[4:16]):
                return name
    raise RegistryError('noncanonical filename or short ID mismatch')


def filename_for(producer, record_id, title):
    validate_producer(producer)
    if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
        raise RegistryError('invalid id')
    _string(title, 'title')
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or 'topic'
    prefix = f'{producer}-{record_id[4:16]}-'
    slug = slug[:80 - len(prefix) - 3].rstrip('-') or 'topic'
    name = f'{prefix}{slug}.md'
    return validate_filename(name, record_id)


def new_id():
    return 'acr_' + uuid.uuid4().hex


def register(root, producer, data, body=''):
    root = Path(root)
    validate_producer(producer)
    root.mkdir(parents=True, exist_ok=True)
    for _ in range(100):
        record = dict(data, id=new_id())
        payload = serialize_record(record, body)
        name = filename_for(producer, record['id'], record['title'])
        path = root / name
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(mode='wb', dir=root, prefix='.agent-context-', delete=False) as stream:
                tmp = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(tmp, path)
            except FileExistsError:
                continue
            return path, record
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
    raise RegistryError('could not allocate a unique filename')


def _replace_file(source, target):
    if os.name != 'nt':
        os.replace(source, target)
        return

    # POSIX-style replacement permits readers opened with FILE_SHARE_DELETE to
    # finish reading the old file while new opens see the replacement. Legacy
    # MoveFileEx (used by os.replace) can fail while any reader is open.
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel32.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel32.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    set_info = kernel32.SetFileInformationByHandle
    set_info.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    set_info.restype = wintypes.BOOL
    destination = str(Path(target).resolve())
    name_bytes = len(destination.encode('utf-16-le'))

    class RenameInfo(ctypes.Structure):
        _fields_ = [('flags', wintypes.DWORD), ('root', wintypes.HANDLE),
                    ('name_length', wintypes.DWORD),
                    ('name', wintypes.WCHAR * (name_bytes // 2 + 1))]

    handle = create(str(source), 0x10000, 0x7, None, 3, 0x80, None)  # DELETE access
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        info = RenameInfo(0x3, None, name_bytes, destination)  # REPLACE | POSIX semantics
        if not set_info(handle, 22, ctypes.byref(info), ctypes.sizeof(info)):  # FileRenameInfoEx
            error = ctypes.get_last_error()
            if error not in (1, 50, 87, 120):
                raise ctypes.WinError(error)
            # Older systems/filesystems may not support this operation. A
            # legacy replace remains safe but can fail while a reader is open.
            fallback = True
        else:
            fallback = False
    finally:
        close(handle)
    if fallback:
        os.replace(source, target)


def replace_record(path, data, body=''):
    path = Path(path)
    validate_filename(path.name, data.get('id'))
    payload = serialize_record(data, body)
    existing, _ = read_record(path)
    if existing['id'] != data['id']:
        raise RegistryError('replacement ID does not match existing record')
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, prefix='.agent-context-', delete=False) as stream:
            tmp = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _replace_file(tmp, path)
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()


def _read_snapshot(path):
    """Copy a record to memory, closing the source before it is interpreted."""
    try:
        if os.name != 'nt':
            return path.read_bytes()

        # Python's default Windows file sharing omits FILE_SHARE_DELETE, which
        # can prevent an independent writer from replacing the file we read.
        import ctypes
        from ctypes import wintypes
        import msvcrt

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        create = kernel32.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        close = kernel32.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        close.restype = wintypes.BOOL
        # GENERIC_READ; FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE;
        # OPEN_EXISTING; FILE_ATTRIBUTE_NORMAL.
        handle = create(str(path), 0x80000000, 0x7, None, 3, 0x80, None)
        if handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except BaseException:
            close(handle)
            raise
        try:
            stream = os.fdopen(fd, 'rb')
        except BaseException:
            os.close(fd)
            raise
        with stream:
            return stream.read()
    except OSError as exc:
        if getattr(exc, 'winerror', None) in (32, 33) or exc.errno in (errno.EAGAIN, errno.EBUSY, errno.ETXTBSY):
            raise RecordBusy(f'temporarily unavailable due to a file-sharing conflict: {exc}') from exc
        raise


def read_record(path):
    path = Path(path)
    validate_filename(path.name)
    data, body = parse_record(_read_snapshot(path))
    validate_filename(path.name, data['id'])
    return data, body


def records(root):
    root = Path(root)
    if not root.exists():
        return [], []
    if not root.is_dir():
        raise RegistryError(f'registry root is not a directory: {root}')
    valid, errors = [], []
    for path in sorted(root.iterdir()):
        if path.name.startswith('.') or not path.is_file():
            continue
        try:
            data, body = read_record(path)
            valid.append((path, data, body))
        except RecordBusy as exc:
            errors.append((path, exc))
        except FileNotFoundError as exc:
            errors.append((path, RecordBusy(f'record disappeared during the scan: {exc}')))
        except PermissionError as exc:
            # WSL may report a Windows sharing violation as EACCES, which is
            # indistinguishable here from ordinary filesystem permissions.
            errors.append((path, RecordBusy(f'record unavailable (permission or sharing conflict): {exc}')))
        except (OSError, RegistryError) as exc:
            errors.append((path, str(exc)))
    return valid, errors


def search_records(items, query):
    folded = query.casefold()
    return [item for item in items if any(folded in value.casefold() for value in
            (item[1]['title'], item[1]['project']['identity'], item[1]['native']['vendor'], item[1]['id']))]
