import ast
import re
import subprocess
import sys
import tempfile

from pathlib import Path

from langchain_core.tools import tool


@tool
def check_python_code(source_code: str, filename: str = "review.py") -> str:
    """
    Validate Python syntax and check code formatting and quality
    using AST, Black, and Flake8.
    """

    # Validate filename
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.py", filename):
        return "ERROR: Invalid Python filename."

    # Limit source size
    if len(source_code) > 100_000:
        return "ERROR: Source code exceeds the 100 KB limit."

    results = []

    # 1. Python syntax validation
    try:
        ast.parse(source_code)
        results.append("SYNTAX: PASS")
    except SyntaxError as error:
        return (
            f"SYNTAX: FAIL\n"
            f"Line: {error.lineno}\n"
            f"Error: {error.msg}"
        )

    with tempfile.TemporaryDirectory() as temp_dir:

        file_path = Path(temp_dir) / filename
        file_path.write_text(source_code, encoding="utf-8")

        # 2. Black formatting check
        try:
            black_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "black",
                    "--check",
                    "--diff",
                    filename
                ],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=temp_dir
            )

            if black_result.returncode == 0:
                results.append("BLACK: PASS")
            else:
                results.append(
                    "BLACK: FAIL\n"
                    + black_result.stdout
                    + black_result.stderr
                )

        except subprocess.TimeoutExpired:
            results.append("BLACK: TIMEOUT")

        # 3. Flake8 quality check
        try:
            flake8_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "flake8",
                    filename
                ],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=temp_dir
            )

            if flake8_result.returncode == 0:
                results.append("FLAKE8: PASS")
            else:
                results.append(
                    "FLAKE8: FAIL\n"
                    + flake8_result.stdout
                    + flake8_result.stderr
                )

        except subprocess.TimeoutExpired:
            results.append("FLAKE8: TIMEOUT")

    return "\n\n".join(results)
