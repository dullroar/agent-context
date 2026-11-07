"""Command line interface for the local session registry."""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import sys

from . import core


def parser():
    p = argparse.ArgumentParser(prog='agent-context', description='Find and record local session pointers.')
    sub = p.add_subparsers(dest='command', required=True)
    register = sub.add_parser('register', help='create a session-topic pointer')
    for flag in ('vendor', 'session', 'project', 'title', 'producer'):
        register.add_argument('--' + flag, required=True)
    register.add_argument('--status', choices=sorted(core.STATUSES), default='unknown')
    register.add_argument('--created-at', help='ISO 8601 timestamp including timezone (default: now in UTC)')
    register.add_argument('--body', default='', help='short human note')
    register.add_argument('--machine')
    register.add_argument('--resume')
    register.add_argument('--updated-at', help='ISO 8601 timestamp including timezone')
    register.add_argument('--otel-trace-id')
    register.add_argument('--a2a-context-id')
    register.add_argument('--supersedes')
    register.add_argument('--windows-path')
    register.add_argument('--wsl-path')
    register.add_argument('--tag', action='append')
    register.add_argument('--evidence', action='append')
    sub.add_parser('list', help='list records')
    search = sub.add_parser('search', help='search title, project, vendor or ID')
    search.add_argument('query')
    show = sub.add_parser('show', help='show the record for a unique ID or fragment')
    show.add_argument('id')
    validate = sub.add_parser('validate', help='validate all records or one file')
    validate.add_argument('path', nargs='?', help='record file (default: all records in root)')
    return p


def _errors(errors):
    for path, message in errors:
        prefix = 'warning: ' if isinstance(message, core.RecordBusy) else ''
        print(f'{prefix}{path}: {message}', file=sys.stderr)


def _print_items(items):
    for path, data, _ in items:
        print(f"{data['id']}\t{data['status']}\t{data['native']['vendor']}\t{data['project']['identity']}\t{data['title']}\t{path.name}")


def run(args, root):
    if args.command == 'register':
        data = {'native': {'vendor': args.vendor, 'session': args.session},
                'project': {'identity': args.project}, 'title': args.title,
                'created_at': args.created_at if args.created_at is not None else dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
                'status': args.status}
        for attr, key in (('machine', 'machine'), ('resume', 'resume'), ('updated_at', 'updated_at'),
                          ('otel_trace_id', 'otel_trace_id'), ('a2a_context_id', 'a2a_context_id'),
                          ('supersedes', 'supersedes'), ('tag', 'tags'), ('evidence', 'evidence')):
            value = getattr(args, attr)
            if value is not None:
                data[key] = value
        hints = {key: value for key, value in (('windows', args.windows_path), ('wsl', args.wsl_path)) if value is not None}
        if hints:
            data['path_hints'] = hints
        path, record = core.register(root, args.producer, data, args.body)
        print(f"{record['id']}\t{path}")
        return 0
    if args.command == 'validate' and args.path:
        path = Path(args.path)
        try:
            core.read_record(path)
        except (core.RecordBusy, PermissionError) as exc:
            print(f'warning: {path}: unavailable: {exc}', file=sys.stderr)
            print(f'unavailable: {path}')
            return 0
        print(f'valid: {path}')
        return 0
    items, errors = core.records(root)
    _errors(errors)
    busy = sum(isinstance(error, core.RecordBusy) for _, error in errors)
    if args.command == 'validate':
        for path, _, _ in items:
            print(f'valid: {path}')
        print(f'{len(items)} valid, {len(errors) - busy} invalid' + (f', {busy} unavailable' if busy else ''))
        return int(any(not isinstance(error, core.RecordBusy) for _, error in errors))
    if args.command == 'list':
        _print_items(items)
    elif args.command == 'search':
        _print_items(core.search_records(items, args.query))
    elif args.command == 'show':
        if busy:
            print('warning: no record shown; cannot establish a unique ID while a record is unavailable', file=sys.stderr)
            return int(any(not isinstance(error, core.RecordBusy) for _, error in errors))
        matches = [item for item in items if args.id.casefold() in item[1]['id'].casefold()]
        if not args.id or len(matches) != 1:
            raise core.RegistryError(f'ID fragment matched {len(matches)} records; specify a unique ID')
        sys.stdout.write(core.serialize_record(matches[0][1], matches[0][2]).decode('utf-8'))
    return int(any(not isinstance(error, core.RecordBusy) for _, error in errors))


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    args = parser().parse_args(argv)
    root = core.resolve_root()
    print(f'Registry root: {root}', file=sys.stderr)
    try:
        return run(args, root)
    except (core.RegistryError, OSError, UnicodeError) as exc:
        print(f'agent-context: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
