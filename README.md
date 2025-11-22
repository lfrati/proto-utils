# Prototyping utilities

Some simple utilities to make prototyping a more enjoyable process.

## Installation

```bash
git clone <repository-url>
cd proto-utils
```

## Quick Start

```python
from utils import iprint, StopWatch, NameLog, CodeMemo, Tagger, GracefulDeath

# Enhanced printing with line info and stack traces
iprint("Hello world!", [1, 2, 3, 4, 5])

# Timing your code
watch = StopWatch()
watch.start()
# ... your code here ...
watch.stop()
print(f"Elapsed: {watch.elapsed()}")

# Track variable values across function calls
log = NameLog()
log.track("accuracy", "loss")
# ... your code ...
log.record()  # Records current values
print(log.tracked)
```

## Utilities Overview

### Task spinner

```python
"""
 Each job spec is a mapping with:
            - label (str): unique job identifier (display + result key)
            - fn (callable): function to execute
            - args (iterable, optional): positional args for fn
            - kwargs (mapping, optional): keyword args for fn
"""
results = Spinner.run_jobs(job_specs, max_workers=len(jobs))
for label, result in results.items():
    print(f"  {label}: {result}")

```

![spinner](https://github.com/user-attachments/assets/d986ba08-6e6c-494f-839e-15db5371245f)


### Enhanced Printing (`iprint`)

Smart printing with line information, call stack, and intelligent truncation of large data structures.

```python
from utils import iprint

# Basic usage
iprint("hello")
# Output: [6 main]: hello

# With lists (automatically truncated)
a = [1, 2, 3, 4, 5, 6]
iprint(a)  # Output: [19 main]: [1, 2, 3, 4, 5, ... ](6)

# With larger lists
b = [i for i in range(1000)]
iprint(b)  # Output: [22 main]: [0, 1, 2, 3, 4, ... ](1000)

# Function call stack example
def foo():
    iprint("inside foo")  # Output: [9 main/foo]: inside foo
    
def bar():
    iprint("inside bar")  # Output: [13 main/foo/bar]: inside bar (when called from foo)
                          # Output: [13 main/bar]: inside bar (when called directly)
```

### StopWatch

Simple timing utility for measuring code execution time.

```python
from utils import StopWatch

# Basic usage
watch = StopWatch()
watch.start()
# ... your code here ...
watch.stop()
print(f"Elapsed: {watch.elapsed()}")

# Error handling
watch = StopWatch()
watch.start()
watch.start()  # Raises RuntimeError: Stopwatch already running!

watch = StopWatch()
watch.stop()   # Raises RuntimeError: Stopwatch not started yet!
```

### NameLog

Track variable values across function calls and record their history.

```python
from utils import NameLog

# Create loggers and track variables
log1 = NameLog()
log2 = NameLog()
log1.track("test1", "test2")
log2.track("accuracy")

# Set initial values
test1 = 4

def baz(log1, log2):
    test2 = 42
    log1.record()  # Records test1=4, test2=42
    for accuracy in range(10):
        log2.record()  # Records accuracy=0,1,2,...,9

baz(log1, log2)

# Access recorded values
print(log1.tracked)  # Output: {'test1': [4], 'test2': [42]}
print(log2.tracked)  # Output: {'accuracy': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}

# Get specific variable history
print(log2.get("accuracy"))  # Output: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

### CodeMemo

Serialized memoization for medium-running scripts. Caches function results based on code state.

```python
from utils import CodeMemo
import time

@CodeMemo
def expensive_computation(x, y, operation="add"):
    """This function will be cached based on its input and surrounding code."""
    print("Computing...")
    time.sleep(2)  # Simulate expensive computation
    
    if operation == "add":
        return x + y
    elif operation == "multiply":
        return x * y

# First call - computes and caches
result1 = expensive_computation(5, 3, "add")  # Takes 2 seconds

# Second call with same inputs - retrieves from cache
result2 = expensive_computation(5, 3, "add")  # Instant!

# Different inputs - computes again
result3 = expensive_computation(5, 3, "multiply")  # Takes 2 seconds

# Results are cached in ./saved/ folder

# Example with timing
watch = StopWatch()
watch.start()
res = longjob(5, ret=4)  # Output: Sleeping...\nDone.
watch.stop()
iprint(f"Got {res}")      # Output: [54 main]: Got 4
iprint(f"Elapsed {watch.elapsed()}")  # Output: [55 main]: Elapsed 0:00:05.007341
```

### Tagger

Generate unique experiment tags using adjective-noun combinations.

```python
from utils import Tagger

# Basic tagger (adjective-noun format)
tagger = Tagger()
print(f"# possible tags: {tagger.size():,}")  # Output: # possible tags: 1,637,871

for i in range(5):
    print(tagger.make())
# Output examples:
# b'unlucky-feed'
# b'boring-cell'
# b'marked-path'
# b'adept-past'
# b'decorous-hook'

# Numeric tags (adjective-noun-number)
tagger = Tagger(10)  # Numbers 0-9
print(f"# possible tags: {tagger.size():,}")  # Output: # possible tags: 16,378,710

for i in range(5):
    print(tagger.make())
# Output examples:
# b'bizarre-rich-1'
# b'labored-spray-6'
# b'agitated-plan-3'
# b'utilized-kitchen-6'
# b'shy-repeat-0'

# Letter tags (adjective-noun-letters)
tagger = Tagger("aaa")  # 3 lowercase letters
print(f"# possible tags: {tagger.size():,}")  # Output: # possible tags: 28,787,220,696

for i in range(5):
    print(tagger.make())
# Output examples:
# b'klutzy-neck-wgf'
# b'cute-crash-miu'
# b'dry-hello-lbh'
# b'watchful-hire-zwf'
# b'untried-ambition-jzx'
```

### GracefulDeath

Handle Ctrl+C and Ctrl+Z signals gracefully in long-running scripts.

```python
from utils import GracefulDeath
import time

with GracefulDeath() as cm:
    while True:
        # Your main loop
        print("Working...")
        time.sleep(1)
        
        if cm.signalled():
            print("Ctrl+Z received - pausing...")
            time.sleep(2)
            
        if cm.killed():
            print("Ctrl+C received - cleaning up...")
            # Clean up resources
            break

print("Exited gracefully")
```

### Color Utilities

Add colors to your terminal output.

```python
from utils import color

print(color("Success!", "green"))
print(color("Warning!", "warn"))
print(color("Error!", "red"))
```

### File Utilities

```python
from utils import folder_size, here

# Get current script directory
script_dir = here()
print(f"Script location: {script_dir}")

# Calculate folder size in MB
size_mb = folder_size("./saved")
print(f"Saved folder size: {size_mb:.2f} MB")
```

### List Utilities

```python
from utils import flatten, unzip, chunker

# Flatten nested lists
nested = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = flatten(nested)
print(flat)  # [1, 2, 3, 4, 5, 6, 7, 8, 9]

# Transpose lists
data = [[1, 2, 3], ['a', 'b', 'c']]
transposed = unzip(data)
print(transposed)  # [(1, 'a'), (2, 'b'), (3, 'c')]

# Chunk data
numbers = list(range(10))
chunks = list(chunker(numbers, 3))
print(chunks)  # [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
```



## Requirements

- Python 3.6+
- No external dependencies

## License

This project is open source and available under the [MIT License](LICENSE).
