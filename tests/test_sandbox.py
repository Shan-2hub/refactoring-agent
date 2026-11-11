import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tools.sandbox_tool import check_python_code

def test_valid_python_code():
    result = check_python_code.invoke({
        "source_code": "def add(a, b):\n    return a + b\n",
        "filename": "calculator.py"
    })

    assert "SYNTAX: PASS" in result
    assert "BLACK: PASS" in result
    assert "FLAKE8: PASS" in result


def test_invalid_python_syntax():
    result = check_python_code.invoke({
        "source_code": "def add(:\n    return 10",
        "filename": "invalid.py"
    })

    assert "SYNTAX: FAIL" in result


def test_invalid_filename():
    result = check_python_code.invoke({
        "source_code": "print('hello')",
        "filename": "../malicious.py"
    })

    assert "Invalid Python filename" in result


def test_large_source_code():
    result = check_python_code.invoke({
        "source_code": " " * 100001,
        "filename": "large.py"
    })

    assert "exceeds the 100 KB limit" in result
