"""Transient Chrome profile lifecycle: create under the OS tmp, always remove, never swallow a leak.

Only the exact directory this helper created is deleted, and only after the browser process
trees it was told about have exited. Anything still present after bounded retries raises
ProfileLeakError (HOLD); it is never ignored. Messages carry the directory basename only.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PREFIX = "taky_chrome_"
WIN = sys.platform == "win32"


class ProfileLeakError(RuntimeError):
    pass


def _tree_kill(proc):
    if proc.poll() is None:
        if WIN:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.kill()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        return f"pid {proc.pid} did not exit within 10s"
    return None


def _kill_orphans(path):
    """Windows: stop processes whose command line names this exact (random) profile dir."""
    if not WIN:
        return
    script = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($env:TAKY_PROFILE) }"
              " | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                   capture_output=True, timeout=30, env={**os.environ, "TAKY_PROFILE": str(path)})


class ChromeProfile:
    """Context manager owning one transient profile directory and the processes using it."""

    def __init__(self, prefix=PREFIX, attempts=8, delay=0.25):
        self.path = Path(tempfile.mkdtemp(prefix=prefix))
        self.attempts, self.delay = attempts, delay
        self.procs = []
        self.problems = []

    def adopt(self, proc):
        self.procs.append(proc)
        return proc

    def terminate(self):
        for proc in self.procs:
            problem = _tree_kill(proc)
            if problem:
                self.problems.append(problem)

    def cleanup(self):
        """Remove the profile; return a list of problems (empty means clean and verified)."""
        self.terminate()
        last = ""
        for attempt in range(self.attempts):
            if not self.path.exists():
                break
            try:
                shutil.rmtree(self.path)
            except OSError as exc:
                last = f"{type(exc).__name__}"
            if self.path.exists():
                if attempt == 2:
                    _kill_orphans(self.path)
                time.sleep(self.delay)
        if self.path.exists():
            self.problems.append(f"profile {self.path.name} still present after {self.attempts} attempts ({last or 'unknown'})")
        return self.problems

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        problems = self.cleanup()
        if not problems:
            return False
        message = "CHROME_PROFILE_LEAK HOLD: " + "; ".join(problems)
        if exc is None:
            raise ProfileLeakError(message)
        # keep the underlying failure as the raised error; the leak must still be visible
        sys.stderr.write(message + "\n")
        if hasattr(exc, "add_note"):
            exc.add_note(message)
        return False
