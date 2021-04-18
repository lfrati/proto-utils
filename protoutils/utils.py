import os
import pickle
from collections import defaultdict
from datetime import timedelta
from hashlib import md5
from inspect import currentframe, getouterframes, stack
from pathlib import Path
from pprint import pformat
from time import time


def search_scopes(name):
    """
    Search name in current and outer frames.

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
    """
    Calculates size of folder in MegaBytes

    :param folder: path of the target folder
    :type name: str
    :return: Folder size in MegaBytes
    :rtype: float
    """
    files = [f for f in Path(folder).glob("**/*") if f.is_file()]
    # divide by 1e6 to get megabytes
    return sum(os.path.getsize(file) for file in files) / 1e6


class CodeMemo:
    """
    Serialized memoization class for medium running scripts (seconds to minutes).
    The results of the decorated functions are serialized to pickles in the ./saved folder.
    Pickles are named using the md5 hash of code before the function call (ingoring imports and formatting.)
    If the code before the decorated function call is unchanged the results are retrieved from the pickles.

    :param fn: The function being decorated.
    :param threshold: The maximum size (in MegaBytes) of the ./saved folder before older memos are deleted. 
    """
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
        """
        Adds names to list of tracked variables.
        """
        for name in names:
            self.names.append(name)
            self.tracked[name] = []

    def record(self):
        """
        Inspects current and calling frames to record the value of tracked variables.
        """
        for name in self.names:
            val = search_scopes(name)
            self.tracked[name].append(val)

    def get(self, name):
        """
        Returns the recorded values for name.

        :param name: the variable whose recorded values need to be returned.
        :type name: str
        :return: List of recorded values.
        :rtype: list
        """
        if name in self.tracked:
            return self.tracked[name]
        else:
            print(f"Name {name} not found.")


class StopWatch:
    """A simple class implementing a stopwatch"""

    def __init__(self):
        self.running = False
        self._start = 0
        self._stop = 0

    def start(self):
        """Start the stopwatch and raises an error if already running."""
        if not self.running:
            self.running = True
            self._start = time()
        else:
            raise RuntimeError("Stopwatch already running!")

    def stop(self):
        """Stops the stopwatch and raises an error if it hadn't been started."""
        if self.running:
            self.running = False
            self._stop = time()
        else:
            raise RuntimeError("Stopwatch not started yet!")

    def elapsed(self):
        """
        Formats and return elapsed time.

        :return: the elapsed time.
        :rtype: str
        """
        return str(timedelta(seconds=self._stop - self._start))


colors = {
    "HEADER": "\033[95m",
    "OKBLUE": "\033[94m",
    "OKCYAN": "\033[96m",
    "OKGREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
}


def flatten(l):
    """
    Turns a list lists into a flat list.

    :Example:

    e.g. [[1,2,3],[a,b,c]] becomes [1,2,3,a,b,c]
    """
    return [a for b in l for a in b]


def unzip(l):
    """
    Transpose list of lists.

    :Example:

    e.g. [[1,2,3],[a,b,c]] becomes [[1,a], [2,b], [3,c]]
    """
    return list(zip(*l))


def color(text, c):
    """
    Color text for better terminal visibility.

    :param text: The text to be colored.
    :type text: str
    :param c: The desired color: "green", "red" or "warn"
    :type c: str
    :return: Colored version of the desired text
    :rtype: str
    """
    if c == "red":
        return f"{colors['FAIL']}{text}{colors['ENDC']}"
    elif c == "green":
        return f"{colors['OKGREEN']}{text}{colors['ENDC']}"
    elif c == "warn":
        return f"{colors['WARNING']+colors['BOLD']}{text}{colors['ENDC']}"
    else:
        return text


def iprint(*args, smart=5):
    """
    Enhance prints in scripts with line info and caller stack.
    Lists are truncated and dictionaries are formatted with pretty-print.
    """

    call_frame = getouterframes(currentframe())[-1]
    call_stack = "/".join([frame.function for frame in reversed(stack()[1:-1])])

    lineinfo = (
        color("[", "green")
        + color(f"{call_frame.lineno}", "warn")
        + color(f"{' '+call_stack if len(call_stack)>0 else ''}]: ", "green")
    )
    print(lineinfo, end="")

    for arg in args:
        # Print only some elements of lists and dictionaries to avoid flooding the screen
        if smart > 0:
            if type(arg) == list:
                if len(arg) > smart:
                    els = ", ".join([str(el) for el in arg[:smart]])
                    print(f"[{els}, ... ]({len(arg)})", end=" ")
            elif type(arg) == dict or type(arg) == defaultdict:
                cols = os.get_terminal_size().columns
                rep = pformat(arg, depth=1, width=cols)
                print(rep, end=" ")
            else:
                print(arg, end=" ")
        else:
            print(arg, end=" ")
    print()
