from utils import NameLog, CodeMemo, StopWatch, iprint, Tagger
from time import sleep


def main():
    iprint("hello")

    def foo():
        iprint("inside foo")
        bar()

    def bar():
        iprint("inside bar")

    foo()
    bar()

    a = [1, 2, 3, 4, 5, 6]
    iprint(a)

    b = [i for i in range(1000)]
    iprint(b)

    watch = StopWatch()
    log1 = NameLog()
    log2 = NameLog()
    log1.track("test1", "test2")
    log2.track("accuracy")
    test1 = 4

    def baz(log1, log2):
        test2 = 42
        log1.record()
        for accuracy in range(10):
            log2.record()

    baz(log1, log2)
    print(log1.tracked)
    print(log2.tracked)

    @CodeMemo
    def longjob(t, ret):
        print("Sleeping...")
        sleep(t)
        print("Done.")
        return ret

    def worker():
        return longjob(5, ret=4)

    watch.start()
    res = worker()
    watch.stop()
    iprint(f"Got {res}")
    iprint(f"Elapsed {watch.elapsed()}")

    exit()

    tagger = Tagger()
    print("Basic")
    print(f"# possible tags: {tagger.size():,}")
    for i in range(5):
        print(tagger.make())

    print()

    tagger = Tagger()
    seen = set()
    tag = tagger.make()
    while tag not in seen:
        seen.add(tag)
        tag = tagger.make()
    assert len(seen) == tagger.size()
    print("Space size matches.")

    print()

    tagger = Tagger(10)
    print("Numeric 10")
    print(f"# possible tags: {tagger.size():,}")
    for i in range(5):
        print(tagger.make())

    print()

    tagger = Tagger("aaa")
    print("Letters 3")
    print(f"# possible tags: {tagger.size():,}")
    for i in range(5):
        print(tagger.make())

    print()


if __name__ == "__main__":
    main()
