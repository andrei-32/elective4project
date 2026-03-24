"""
Script to commit and push logs/pipeline_errors.log to GitHub.
Run this after the pipeline to ensure error logs are versioned.
"""
import subprocess
from pathlib import Path
import sys

LOG_PATH = Path("logs/pipeline_errors.log")

def main():
    if not LOG_PATH.exists():
        print(f"Log file {LOG_PATH} does not exist.")
        return 0
    try:
        # Stage the log file
        subprocess.run(["git", "add", str(LOG_PATH)], check=True)
        # Commit with a standard message
        subprocess.run([
            "git", "commit", "-m", "Update pipeline error log [auto]"
        ], check=True)
        # Push to the current branch
        subprocess.run(["git", "push"], check=True)
        print("Log file committed and pushed.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Failed to push logs: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())