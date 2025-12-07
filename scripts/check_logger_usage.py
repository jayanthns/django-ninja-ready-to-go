#!/usr/bin/env python3
import os
import re
import sys

# Configuration
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "tests",
    "docs",
}
LOGGER_PATTERN = re.compile(r"logging\.getLogger\(")
IGNORE_COMMENT = "# no-check-logger"


def check_file(filepath):
    """
    Check if a file contains logger usage that should be avoided.
    Returns a list of errors found in the file.
    """
    errors = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if LOGGER_PATTERN.search(line):
                    if IGNORE_COMMENT not in line:
                        # Filter out logger_helper.py itself as it needs to use logging.getLogger
                        if "common/logger_helper.py" in filepath:
                            continue

                        errors.append(
                            f"{filepath}:{i}: Found 'logging.getLogger'. "
                            f"Please use 'common.logger_helper.get_logger_with_trace' or similar."
                            f" If this is intentional, append '{IGNORE_COMMENT}' to the line."
                        )
    except Exception:
        # Ignore encoding errors or non-text files
        pass
    return errors


def main():
    """
    Walk through the project directory and check files.
    """
    project_root = os.getcwd()
    found_errors = []

    for root, dirs, files in os.walk(project_root):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                file_errors = check_file(filepath)
                found_errors.extend(file_errors)

    if found_errors:
        print("Logger Check Failures:")
        for error in found_errors:
            print(error)
        sys.exit(1)

    print("Logger check passed!")
    sys.exit(0)


if __name__ == "__main__":
    main()
