import time
import sys

from spinner import Spinner


if __name__ == "__main__":
    jobs = [
        ("Alpha", 2.5),
        ("Beta", 1.5),
        ("Gamma", 3.0),
        ("Delta", 2.0),
    ]

    def _demo_job(name: str, duration: float):
        time.sleep(duration)
        return f"{name} finished"

    job_specs = [
        {"label": name, "fn": _demo_job, "args": (name, dur)} for name, dur in jobs
    ]

    for run in range(1, 3):
        try:
            results = Spinner.run_jobs(job_specs, max_workers=3)
            print(f"Run {run}:")
            for label, result in results.items():
                print(f"  {label}: {result}")
        except Exception as exc:
            sys.stderr.write(f"Job failed: {exc}\n")
