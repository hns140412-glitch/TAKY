"""Candidate contract; standalone and fail-closed, no authority mutation.

Every evidence entry must point at a real repo-relative file under ``root`` whose bytes match
``evidence_sha256`` and which parses as a JSON object whose ``task_id`` and ``revision`` fields are
EXACTLY equal to the requested task_id / revision (no substring match; unparseable, duplicate-key or
non-object evidence -> BINDING_UNPARSEABLE). No ``root``, ``task_id`` or ``revision`` -> HOLD.

Limits (honest): the sha256 and the task/revision fields only prove the file is the one the record
names and that it declares itself written for this task/revision. They do NOT prove who issued it; no
trusted issuer/approval verifier exists here, so ``issuer`` is always ``UNVERIFIED``.

Race handling: where the platform supports it (POSIX with ``O_NOFOLLOW``, ``O_DIRECTORY`` and
``dir_fd``) the path is walked fd-relative from the root, one component at a time with
``O_NOFOLLOW``, so a symlink swapped in at any component is rejected and nothing is resolved then
re-opened. The final open is ``O_NONBLOCK`` so a FIFO cannot block before the regular-file check.
Where that is unavailable (e.g. Windows) swaps cannot be provably prevented: the best-effort checks
still run, but every otherwise-valid entry is reported ``RACE_SAFETY_UNVERIFIED`` and the result is
HOLD with ``integrity: UNVERIFIED`` -- never PASS. A race after this function returns (between the
caller's check and its later use of the evidence) cannot be excluded on any platform.
"""
import errno
import hashlib
import json
import os
import stat
from pathlib import Path

REQUIRED = ('intent', 'authority', 'dependencies', 'external_counterexamples', 'reuse', 'implementation', 'independent_review', 'integration_e2e', 'regression', 'consumer_evidence')


def _safe_open_supported():
    return (os.name == 'posix' and hasattr(os, 'O_NOFOLLOW') and hasattr(os, 'O_DIRECTORY')
            and os.open in os.supports_dir_fd)


def _open_at(dir_fd, name, flags):
    """Open ``name`` relative to ``dir_fd`` without following links; return (fd, None) or (None, reason)."""
    try:
        return os.open(name, flags | os.O_NOFOLLOW, dir_fd=dir_fd), None
    except OSError as exc:
        if exc.errno not in (errno.ELOOP, errno.ENOTDIR, errno.ENOENT, errno.EMLINK):
            raise
    try:
        st = os.lstat(name, dir_fd=dir_fd)
    except FileNotFoundError:
        return None, 'REF_FILE_MISSING'
    return None, 'REF_SYMLINK' if stat.S_ISLNK(st.st_mode) else 'REF_FILE_MISSING'


def _read_fd_relative(base, parts):
    fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts[:-1]:
            nxt, reason = _open_at(fd, part, os.O_RDONLY | os.O_DIRECTORY)
            if reason:
                return None, reason
            os.close(fd)
            fd = nxt
        nxt, reason = _open_at(fd, parts[-1], os.O_RDONLY | os.O_NONBLOCK)
        if reason:
            return None, reason
    finally:
        os.close(fd)
    try:
        if not stat.S_ISREG(os.fstat(nxt).st_mode):
            return None, 'REF_FILE_MISSING'
        with os.fdopen(nxt, 'rb', closefd=False) as fh:
            return fh.read(), None
    finally:
        os.close(nxt)


def _read_best_effort(base, parts):
    """Path-based read for platforms without fd-relative open; cannot prove swap-safety."""
    cur = base
    for part in parts:
        cur = cur / part
        if cur.is_symlink() or getattr(cur, 'is_junction', lambda: False)():
            return None, 'REF_SYMLINK'
    path = cur.resolve()
    if path.is_dir():
        return None, 'REF_FILE_MISSING'
    if not path.is_relative_to(base):
        return None, 'REF_ESCAPES_ROOT'
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        return None, 'REF_FILE_MISSING'
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            return None, 'REF_FILE_MISSING'
        with os.fdopen(fd, 'rb', closefd=False) as fh:
            data = fh.read()
        if not os.path.samestat(before, os.stat(path)) or cur.resolve() != path:
            return None, 'REF_CHANGED_DURING_READ'
    finally:
        os.close(fd)
    return data, None


def _read_windows_handle(base, parts):
    """Native Windows handle evidence: return (data, reason, evidence).

    Opens the file with ``CreateFileW`` (``\\\\?\\`` form, ``FILE_FLAG_OPEN_REPARSE_POINT``, share-read only so
    the opened file cannot be renamed/deleted/rewritten by others while held), then judges the HANDLE, not the
    path: disk file only, no reparse point, not a directory, and ``GetFinalPathNameByHandleW`` must equal the
    requested path under ``base`` before and after the read (a symlink/junction/rename anywhere in the chain
    changes it). This is evidence only: it never yields PASS and ``_verify_ref`` still reports
    ``RACE_SAFETY_UNVERIFIED`` on Windows, because directory components are checked, not pinned.
    """
    if os.name != 'nt':
        return None, 'WINDOWS_HANDLE_UNSUPPORTED', None
    import ctypes
    import msvcrt
    from ctypes import wintypes
    expected = str(base.joinpath(*parts))
    if expected.startswith('\\\\'):
        return None, 'WINDOWS_ROOT_UNSUPPORTED', None

    class Info(ctypes.Structure):
        _fields_ = [('attrs', wintypes.DWORD), ('created', wintypes.FILETIME), ('accessed', wintypes.FILETIME),
                    ('written', wintypes.FILETIME), ('volume', wintypes.DWORD), ('size_hi', wintypes.DWORD),
                    ('size_lo', wintypes.DWORD), ('links', wintypes.DWORD), ('index_hi', wintypes.DWORD),
                    ('index_lo', wintypes.DWORD)]

    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                                wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.GetFileType.argtypes = [wintypes.HANDLE]
    k32.GetFileType.restype = wintypes.DWORD
    k32.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(Info)]
    k32.GetFileInformationByHandle.restype = wintypes.BOOL
    k32.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    k32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    k32.CloseHandle.argtypes = [wintypes.HANDLE]

    def final_path(handle):
        buf = ctypes.create_unicode_buffer(32768)
        n = k32.GetFinalPathNameByHandleW(handle, buf, len(buf), 0)
        if not 0 < n < len(buf):
            return None
        return os.path.normcase(buf.value[4:] if buf.value.startswith('\\\\?\\') else buf.value)

    # GENERIC_READ, FILE_SHARE_READ only, OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT
    handle = k32.CreateFileW('\\\\?\\' + expected, 0x80000000, 0x1, None, 3, 0x00200000, None)
    if handle in (None, wintypes.HANDLE(-1).value):
        return None, ('REF_FILE_MISSING' if ctypes.get_last_error() in (2, 3) else 'REF_UNREADABLE'), None
    fd = None
    try:
        info = Info()
        if k32.GetFileType(handle) != 0x1 or not k32.GetFileInformationByHandle(handle, ctypes.byref(info)):
            return None, 'REF_FILE_MISSING', None
        if info.attrs & 0x400:  # FILE_ATTRIBUTE_REPARSE_POINT
            return None, 'REF_SYMLINK', None
        if info.attrs & 0x10:  # FILE_ATTRIBUTE_DIRECTORY
            return None, 'REF_FILE_MISSING', None
        want = os.path.normcase(expected)
        if final_path(handle) != want:
            return None, 'REF_ESCAPES_ROOT', None
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY)  # fd now owns the handle
        handle_owned = handle
        handle = None
        with os.fdopen(fd, 'rb', closefd=False) as fh:
            data = fh.read()
        if final_path(handle_owned) != want:
            return None, 'REF_CHANGED_DURING_READ', None
        return data, None, {'final_path': want, 'volume_serial': info.volume,
                            'file_index': (info.index_hi << 32) | info.index_lo, 'size': len(data),
                            'race_safety': 'UNVERIFIED'}
    finally:
        if fd is not None:
            os.close(fd)
        elif handle is not None:
            k32.CloseHandle(handle)


def _no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate key')
        out[key] = value
    return out


def _reject_constant(_):
    raise ValueError('non-finite number')


def _binding_reason(data, task_id, revision):
    """Exact structured binding: JSON object with task_id/revision fields equal to the request."""
    try:
        doc = json.loads(data.decode('utf-8'), object_pairs_hook=_no_duplicates, parse_constant=_reject_constant)
    except (UnicodeDecodeError, ValueError, RecursionError):
        return 'BINDING_UNPARSEABLE'
    if not isinstance(doc, dict):
        return 'BINDING_UNPARSEABLE'
    if doc.get('task_id') != task_id or doc.get('revision') != revision:
        return 'BINDING_MISSING'
    return None


def _verify_ref(entry, base, task_id, revision):
    """Return None when the evidence verifies, else a reason code."""
    ref = entry.get('evidence_ref')
    digest = entry.get('evidence_sha256')
    if not isinstance(ref, str) or not ref.strip():
        return 'REF_INVALID'
    if not isinstance(digest, str) or len(digest) != 64:
        return 'SHA256_MISSING'
    raw = ref.strip().replace('\\', '/')
    parts = raw.split('/')
    if raw.startswith('/') or ':' in raw or any(p in ('', '.', '..') for p in parts):
        return 'REF_NOT_REPO_RELATIVE'
    safe = _safe_open_supported()
    try:
        data, reason = (_read_fd_relative if safe else _read_best_effort)(base, parts)
    except (OSError, ValueError, RuntimeError):
        return 'REF_UNREADABLE'
    if reason:
        return reason
    if not data.strip():
        return 'REF_FILE_EMPTY'
    if hashlib.sha256(data).hexdigest() != digest.lower():
        return 'SHA256_MISMATCH'
    reason = _binding_reason(data, task_id, revision)
    if reason:
        return reason
    if not safe:
        return 'RACE_SAFETY_UNVERIFIED'
    return None


def evaluate(record, root=None, task_id=None, revision=None):
    if not isinstance(record, dict):
        record = {}
    missing = [k for k in REQUIRED if not isinstance(record.get(k), dict) or record[k].get('status') != 'PASS' or not record[k].get('evidence_ref')]
    unverified = {}
    preconditions = []
    if root is None:
        preconditions.append('ROOT_REQUIRED')
    if not isinstance(task_id, str) or not task_id.strip():
        preconditions.append('TASK_ID_REQUIRED')
    if not isinstance(revision, str) or not revision.strip():
        preconditions.append('REVISION_REQUIRED')
    if not preconditions:
        try:
            base = Path(root).resolve()
        except (OSError, ValueError, RuntimeError, TypeError):
            preconditions.append('ROOT_UNREADABLE')
    if not preconditions:
        for k in REQUIRED:
            if k in missing:
                continue
            reason = _verify_ref(record[k], base, task_id, revision)
            if reason:
                unverified[k] = reason
    failed = bool(missing or unverified or preconditions)
    return {'status': 'HOLD' if failed else 'PASS', 'missing': missing, 'unverified': unverified,
            'preconditions': preconditions, 'issuer': 'UNVERIFIED',
            'integrity': 'FD_RELATIVE_NOFOLLOW' if _safe_open_supported() else 'UNVERIFIED',
            'candidate_only': True}
