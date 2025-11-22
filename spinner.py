import sys
import threading
import time
import itertools
import random
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional, Sequence

BLUE = "\033[34m"
BOLD = "\033[1m"
CYAN = "\033[36m"
DIM = "\033[2m"
GRAY = "\033[90m"
GREEN = "\033[32m"
LIGHT_BLUE = "\033[94m"
LIGHT_CYAN = "\033[96m"
LIGHT_GREEN = "\033[92m"
LIGHT_MAGENTA = "\033[95m"
LIGHT_RED = "\033[91m"
LIGHT_YELLOW = "\033[93m"
MAGENTA = "\033[35m"
ORANGE = "\033[38;5;208m"
ORANGE = "\033[38;5;208m"
PINK = "\033[38;5;205m"
PURPLE = "\033[38;5;93m"
RED = "\033[31m"
RESET = "\033[0m"
TEAL = "\033[38;5;37m"
WHITE = "\033[97m"
YELLOW = "\033[33m"

FRAMES = ["⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽", "⣾"]

ElapsedSupplier = Callable[[], float]
JobCallable = Callable[..., Any]
JobSpec = Dict[str, Any]
JobResult = Dict[str, Any]


class SpinnerDisplay:
    """Manages terminal output so each spinner stays on its own line."""

    def __init__(self):
        self._lock = threading.Lock()
        self._order = []
        self._lines = {}
        self._last_line_count = 0
        self._id_iter = itertools.count()
        self._active_count = 0

    def register(self, initial_line: str = "") -> int:
        spinner_id = next(self._id_iter)
        with self._lock:
            self._order.append(spinner_id)
            self._lines[spinner_id] = initial_line
            self._active_count += 1
            self._render_locked()
        return spinner_id

    def update(self, spinner_id: int, line: str):
        with self._lock:
            if spinner_id not in self._lines:
                return
            self._lines[spinner_id] = line
            self._render_locked()

    def release(self, spinner_id: int):
        with self._lock:
            if spinner_id not in self._lines:
                return
            self._active_count = max(0, self._active_count - 1)
            if self._active_count == 0:
                self._order.clear()
                self._lines.clear()
                self._last_line_count = 0

    def _render_locked(self):
        lines = [self._lines[i] for i in self._order]
        prev = self._last_line_count
        buf = []
        if prev:
            buf.append("\r")
            buf.append(f"\033[{prev}F")
        for line in lines:
            buf.append("\033[K")
            buf.append(line)
            buf.append("\n")
        sys.stdout.write("".join(buf))
        sys.stdout.flush()
        self._last_line_count = len(lines)


DEFAULT_DISPLAY = SpinnerDisplay()


class SpinnerController:
    """Runs a single render thread for all active spinners."""

    def __init__(self, interval: float = 0.08):
        self._interval = interval
        self._lock = threading.Lock()
        self._spinners: Dict[int, "Spinner"] = {}
        self._wake = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def add(self, spinner: "Spinner"):
        with self._lock:
            self._spinners[id(spinner)] = spinner
            self._ensure_thread()
            self._wake.set()

    def remove(self, spinner: "Spinner"):
        with self._lock:
            self._spinners.pop(id(spinner), None)
            if not self._spinners:
                self._wake.set()

    def _ensure_thread(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def _run(self):
        while True:
            with self._lock:
                spinners = list(self._spinners.values())
            if not spinners:
                self._wake.wait()
                self._wake.clear()
                continue
            for spinner in spinners:
                spinner._render_tick()
            time.sleep(self._interval)


DEFAULT_CONTROLLER = SpinnerController()


class Spinner:
    """Lightweight terminal spinner.

    Usage:
        s = Spinner("Running wiki_search…")
        s.start()
        try:
            ... work ...
            s.stop(success=True)
        except Exception:
            s.stop(success=False)
            raise
    """

    def __init__(
        self,
        text: str,
        msg: str = "Running: ",
        elapsed_supplier: Optional[ElapsedSupplier] = None,
        display: Optional[SpinnerDisplay] = None,
        controller: Optional[SpinnerController] = None,
    ):
        self.text = text
        self.msg = msg
        self._elapsed_supplier = elapsed_supplier
        self._display = display or DEFAULT_DISPLAY
        self._controller = controller or DEFAULT_CONTROLLER
        self._stop = threading.Event()
        self._idx = random.randrange(len(FRAMES))  # desynchronize spinner frames
        self._start_time = None
        self._display_id: Optional[int] = None

    def _format_elapsed(self, seconds: float) -> str:
        total_seconds = max(0, int(seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _current_elapsed(self) -> float:
        if self._elapsed_supplier is not None:
            return max(0.0, self._elapsed_supplier())
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def _format_running_line(self, frame: str, elapsed_str: str) -> str:
        return (
            f"{CYAN}{self.msg}{RESET}{BOLD}{self.text}{RESET} "
            f"{DIM}{frame} [{elapsed_str}]{RESET}"
        )

    def _format_final_line(self, status_icon: str, elapsed_str: str) -> str:
        return (
            f"{CYAN}{self.msg}{RESET}{BOLD}{self.text}{RESET} "
            f"{status_icon} {DIM}[{elapsed_str}]{RESET}"
        )

    def _render_tick(self):
        if self._display_id is None or self._stop.is_set():
            return
        frame = FRAMES[self._idx % len(FRAMES)]
        self._idx += 1
        elapsed_str = self._format_elapsed(self._current_elapsed())
        line = self._format_running_line(frame, elapsed_str)
        self._display.update(self._display_id, line)

    def start(self):
        if self._elapsed_supplier is None:
            self._start_time = time.time()
        initial_elapsed = self._format_elapsed(self._current_elapsed())
        frame = FRAMES[self._idx % len(FRAMES)]
        initial_line = self._format_running_line(frame, initial_elapsed)
        self._display_id = self._display.register(initial_line)
        self._idx += 1
        self._controller.add(self)

    def stop(self, success: bool = True, elapsed: Optional[float] = None):
        self._stop.set()
        self._controller.remove(self)
        if elapsed is None:
            elapsed = self._current_elapsed()
        elapsed_str = self._format_elapsed(elapsed)
        status_icon = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
        final_line = self._format_final_line(status_icon, elapsed_str)
        if self._display_id is not None:
            self._display.update(self._display_id, final_line)
            release = getattr(self._display, "release", None)
            if callable(release):
                release(self._display_id)
            self._display_id = None

    @staticmethod
    def run_jobs(
        jobs: Sequence[JobSpec],
        *,
        max_workers: Optional[int] = None,
        msg: str = "Running: ",
        display: Optional[SpinnerDisplay] = None,
    ) -> Dict[str, Any]:
        """Run the provided jobs concurrently and return their results.

        Each job spec is a mapping with:
            - label (str): unique job identifier (display + result key)
            - fn (callable): function to execute
            - args (iterable, optional): positional args for fn
            - kwargs (mapping, optional): keyword args for fn

        Returns a mapping from label -> JobResult. Each JobResult exposes:
            - ok: bool shortcut for success
            - result: the callable's return value when ok is True, else None
            - error: {"type": str, "message": str} when ok is False, else None
        """
        normalized = []
        for job in jobs:
            if not isinstance(job, dict):
                raise TypeError("Each job specification must be a dict")
            if "label" not in job:
                raise ValueError("Job specification missing 'label'")
            if "fn" not in job:
                raise ValueError("Job specification missing 'fn'")
            label = job["label"]
            fn = job["fn"]
            args = tuple(job.get("args", ()))
            kwargs = dict(job.get("kwargs", {}))
            normalized.append((label, fn, args, kwargs))

        if not normalized:
            return {}

        with SpinnerPool(
            max_workers=max_workers,
            msg=msg,
            display=display,
        ) as pool:
            for label, fn, args, kwargs in normalized:
                pool.submit(label, fn, *args, **kwargs)
            return pool.wait_all()


class SpinnerPool:
    """Simple thread pool that runs jobs with dedicated spinners."""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        msg: str = "Running: ",
        display: Optional[SpinnerDisplay] = None,
        controller: Optional[SpinnerController] = None,
    ):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._msg = msg
        self._display = display or DEFAULT_DISPLAY
        self._controller = controller or DEFAULT_CONTROLLER
        self._jobs: Dict[str, Future] = {}
        self._lock = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.shutdown()

    def submit(
        self,
        label: str,
        fn: JobCallable,
        *args,
        **kwargs,
    ) -> Future:
        """Submit a job to the pool and immediately start its spinner."""
        with self._lock:
            if label in self._jobs:
                raise ValueError(f"Job with label '{label}' already submitted")
        start_time = time.time()

        def elapsed_supplier():
            return time.time() - start_time

        # elapsed_supplier = lambda: time.time() - start_time
        spinner = Spinner(
            label,
            msg=self._msg,
            elapsed_supplier=elapsed_supplier,
            display=self._display,
            controller=self._controller,
        )
        spinner.start()

        def runner():
            success = False
            result_value: Any = None
            error_info: Optional[Dict[str, str]] = None
            try:
                result_value = fn(*args, **kwargs)
                success = True
            except Exception as exc:
                error_info = {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                }
            finally:
                spinner.stop(success=success, elapsed=elapsed_supplier())
            return {
                "ok": success,
                "result": result_value,
                "error": error_info,
            }

        future = self._executor.submit(runner)
        with self._lock:
            self._jobs[label] = future
        return future

    def shutdown(self, wait: bool = True):
        """Shut down the underlying executor."""
        self._executor.shutdown(wait=wait)

    def wait_all(self) -> Dict[str, JobResult]:
        """Block until all submitted jobs finish and return their results.

        Each result has the structure:
            {
                "ok": bool,
                "result": Any,  # valid only when ok is True
                "error": Optional[Dict[str, str]],  # populated when ok is False
            }
        """
        with self._lock:
            items = list(self._jobs.items())
        results: Dict[str, JobResult] = {}
        for label, future in items:
            results[label] = future.result()
        return results

    def result_for(self, label: str) -> JobResult:
        """Block until the requested job finishes and return its result."""
        with self._lock:
            future = self._jobs.get(label)
        if future is None:
            raise KeyError(f"No job found with label '{label}'")
        return future.result()
