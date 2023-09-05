import os
import subprocess
import sys


def run_main_with_arguments(arguments: list) -> tuple:
    main_file_path = os.path.join(
        os.path.dirname(__file__), "..", "src/tds", "__main__.py"
    )
    main_file_path = os.path.abspath(main_file_path)

    print(f"__main__.py file path: {main_file_path}")

    process = subprocess.Popen(
        [sys.executable, main_file_path] + arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    exit_code = process.returncode

    return stdout.decode(), stderr.decode(), exit_code


def test_help():
    run_main_with_arguments(["--help"])
