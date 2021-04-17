from inspect import currentframe, getouterframes, stack
from collections import defaultdict
from pprint import pformat
import os
from pathlib import Path
from hashlib import md5
import pickle
from time import time
from datetime import timedelta


def search_scopes(name):
    """
    Search name in current and calling frames
    :param name: variable name
    :type name: str
    :return: value of the variable "name", None if not found.
    """
    frame = currentframe()
    while name not in frame.f_locals:
        frame = frame.f_back
        if frame is None:
            return None
    return frame.f_locals[name]


def folder_size(folder):
    files = [f for f in Path(folder).glob("**/*") if f.is_file()]
    # divide by 1e6 to get megabytes
    return sum(os.path.getsize(file) for file in files) / 1e6


class CodeMemo:
    def __init__(self, fn, threshold=10):
        self.fn = fn
        self.save_folder = Path("./saved")
        self.save_folder.mkdir(exist_ok=True, parents=True)
        self.threshold = threshold  # Megabytes

    def state(self):
        # Get the outermost caller
        info = getouterframes(currentframe())[-1]
        with open(info.filename, "r") as f:
            # ignore spaces and empylines
            code = [next(f).strip().replace(" ", "") for _ in range(info.lineno)]
        # ignore imports
        prev_code = "".join([line for line in code if "import" not in line])
        # print(prev_code)
        state_hash = md5(prev_code.encode("utf-8")).hexdigest()
        return state_hash

    def __call__(self, *args, **kwargs):
        s = self.state()
        s += f"-{self.fn.__name__}"
        if len(args) > 0:
            s += "-" + "-".join([f"{arg}" for arg in args])
        if len(kwargs) > 0:
            s += "-" + "-".join([f"{key}={val}" for key, val in kwargs.items()])
        loc = self.save_folder / s

        if folder_size(self.save_folder) > self.threshold:
            # remove oldest
            paths = sorted(
                [f for f in self.save_folder.iterdir() if f.is_file()],
                key=os.path.getmtime,
            )
            if len(paths) > 0:
                paths[0].unlink()

        if loc.exists():
            with open(loc, "rb") as f:
                ret = pickle.load(f)
        else:
            ret = self.fn(*args, **kwargs)
            with open(loc, "wb") as f:
                pickle.dump(ret, f)
        return ret


class Log:
    """
    Simple logger to record the value of variables.
    """

    def __init__(self):
        self.names = []
        self.tracked = {}

    def track(self, *names):
        for name in names:
            self.names.append(name)
            self.tracked[name] = []

    def record(self):
        for name in self.names:
            val = search_scopes(name)
            self.tracked[name].append(val)

    def get(self, name):
        if name in self.tracked:
            return self.tracked[name]
        else:
            print(f"Name {name} not found.")


class StopWatch:
    def __init__(self):
        self.running = False
        self._start = 0
        self._stop = 0

    def start(self):
        if not self.running:
            self.running = True
            self._start = time()
        else:
            raise RuntimeError("Stopwatch already running!")

    def stop(self):
        if self.running:
            self.running = False
            self._stop = time()
        else:
            raise RuntimeError("Stopwatch not started yet!")

    def elapsed(self):
        return str(timedelta(seconds=self._stop - self._start))


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def flatten(l):
    return [a for b in l for a in b]


def unzip(l):
    return list(zip(*l))


def red(s):
    return f"{bcolors.FAIL}{s}{bcolors.ENDC}"


def green(s):
    return f"{bcolors.OKGREEN}{s}{bcolors.ENDC}"


def warn(s):
    return f"{bcolors.WARNING+bcolors.BOLD}{s}{bcolors.ENDC}"


def iprint(*args, smart=5):

    call_frame = getouterframes(currentframe())[-1]
    call_stack = "/".join([frame.function for frame in reversed(stack()[1:-1])])

    lineinfo = (
        green("[")
        + warn(f"{call_frame.lineno}")
        + green(f"{' '+call_stack if len(call_stack)>0 else ''}]: ")
    )
    print(lineinfo, end="")

    for arg in args:
        # Print only some elements of lists and dictionaries to avoid flooding the screen
        if smart > 0:
            if type(arg) == list:
                if len(arg) > smart:
                    els = ", ".join([str(el) for el in arg[:smart]])
                    print(f"[{els}, ... ]({len(arg)})")
            elif type(arg) == dict or type(arg) == defaultdict:
                cols = os.get_terminal_size().columns
                rep = pformat(arg, depth=1, width=cols)
                print(rep)
            else:
                print(arg)
        else:
            print(arg)
