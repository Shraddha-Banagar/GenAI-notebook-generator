"""Static validation and safety analysis for generated notebooks.

U4 + U5 live here. The validator is intentionally conservative: every code cell
is parsed with :mod:`ast`, dangerous imports/calls are rejected, shell magics are
allow-listed, and a small set of TF1/legacy-Keras patterns fail the build.
"""

from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass
from typing import Iterable

# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    cell_index: int | None = None
    section: str | None = None
    line: int | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


# ---------------------------------------------------------------------------
# U5: malicious-code detection
# ---------------------------------------------------------------------------

FORBIDDEN_IMPORTS = {
    "subprocess",
    "socket",
    "ctypes",
    "pty",
    "multiprocessing",
    "marshal",
    "pickle",
    "dill",
    "shelve",
    "telnetlib",
    "ftplib",
    "smtplib",
    "paramiko",
    "importlib",
    "runpy",
    "webbrowser",
    "requests",
    "urllib",
    "urllib2",
    "http.client",
}

# Full dotted call names that must never appear in generated code.
FORBIDDEN_CALLS = {
    "os.system",
    "os.popen",
    "os.spawnl",
    "os.spawnle",
    "os.spawnlp",
    "os.spawnlpe",
    "os.spawnv",
    "os.spawnve",
    "os.spawnvp",
    "os.spawnvpe",
    "os.execv",
    "os.execve",
    "os.execl",
    "os.execle",
    "os.execlp",
    "os.execlpe",
    "os.fork",
    "os.forkpty",
    "os.kill",
    "os.killpg",
    "os.remove",
    "os.unlink",
    "os.rmdir",
    "os.removedirs",
    "os.chmod",
    "os.chown",
    "os.setuid",
    "os.setgid",
    "os.putenv",
    "shutil.rmtree",
    "shutil.move",
    "shutil.copy",
    "shutil.copytree",
    "builtins.eval",
    "builtins.exec",
    "builtins.compile",
    "builtins.__import__",
    "importlib.import_module",
}

FORBIDDEN_BARE_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "breakpoint",
    "exit",
    "quit",
}

DANGEROUS_DUNDERS = {
    "__globals__",
    "__builtins__",
    "__subclasses__",
    "__code__",
    "__loader__",
    "__import__",
    "__mro__",
    "f_globals",
    "f_locals",
    "gi_frame",
    "cr_frame",
}

# Shell / magic commands are allowed only from this tiny allow-list.
_ALLOWED_PACKAGES = {
    "transformers",
    "pillow",
    "sentencepiece",
    "accelerate",
    "safetensors",
    "tf-keras",
    "tensorflow",
    "tensorflow-gpu",
    "numpy",
    "matplotlib",
}

_PIP_RE = re.compile(
    r"^(?:(?:python|python3)\s+-m\s+)?pip(?:3)?\s+"
    r"(?:-q|--quiet)?\s*install\s+"
    r"(?P<packages>.+)$",
    re.IGNORECASE,
)
_ALLOWED_MAGICS = {
    "%matplotlib inline",
    "%matplotlib notebook",
    "%config inlinebackend.figure_format = 'retina'",
    "%config inlinebackend.figure_format = \"retina\"",
    "%load_ext autoreload",
    "%autoreload 2",
}


def _strip_version_spec(package: str) -> str:
    return re.split(r"[<>=!~\[\];\s]", package.strip().strip("\"'"), maxsplit=1)[0].lower()


def _check_shell_command(command: str, cell_index: int | None, section: str | None) -> list[Finding]:
    findings: list[Finding] = []
    if command in _ALLOWED_MAGICS:
        return findings

    candidate = command[1:].strip() if command.startswith(("!", "%pip ")) else command
    pip_match = _PIP_RE.match(candidate)
    if pip_match:
        packages = [
            part
            for part in re.split(r"\s+", pip_match.group("packages").strip())
            if part and not part.startswith("-")
        ]
        unknown = [pkg for pkg in packages if _strip_version_spec(pkg) not in _ALLOWED_PACKAGES]
        if unknown:
            findings.append(
                Finding(
                    SEVERITY_ERROR,
                    "safety.shell_packages",
                    f"Shell install contains non-allow-listed package(s): {', '.join(unknown)}",
                    cell_index,
                    section,
                )
            )
        return findings

    findings.append(
        Finding(
            SEVERITY_ERROR,
            "safety.shell_command",
            f"Shell/magic command is not allow-listed: {command[:120]}",
            cell_index,
            section,
        )
    )
    return findings


def _prepare_python(source: str) -> tuple[str, list[str]]:
    """Replace IPython magics/shell escapes with ``pass`` and collect commands."""

    magic_prefixes = (
        "%matplotlib",
        "%config",
        "%load_ext",
        "%autoreload",
        "%pip",
        "%%",
    )
    commands: list[str] = []
    python_lines: list[str] = []
    for raw_line in source.splitlines():
        stripped = raw_line.lstrip()
        is_shell = stripped.startswith("!") and not stripped.startswith("!=")
        is_magic = stripped.startswith(magic_prefixes)
        if is_shell or is_magic:
            commands.append(stripped.rstrip())
            indent = raw_line[: len(raw_line) - len(stripped)]
            python_lines.append(f"{indent}pass")
        else:
            python_lines.append(raw_line)
    return "\n".join(python_lines), commands


def _dotted_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    current: ast.AST | None = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def analyze_ast(
    source: str,
    cell_index: int | None = None,
    section: str | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    python_source, commands = _prepare_python(source)

    for command in commands:
        findings.extend(_check_shell_command(command, cell_index, section))

    try:
        tree = ast.parse(python_source, filename=f"<cell {cell_index}>")
    except SyntaxError as exc:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "syntax.invalid_python",
                f"Python syntax error: {exc.msg}",
                cell_index,
                section,
                exc.lineno,
            )
        )
        return findings

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if alias.name in FORBIDDEN_IMPORTS or root in FORBIDDEN_IMPORTS:
                    findings.append(
                        Finding(
                            SEVERITY_ERROR,
                            "safety.forbidden_import",
                            f"Import of '{alias.name}' is blocked by the safety policy.",
                            cell_index,
                            section,
                            getattr(node, "lineno", None),
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0]
            if module in FORBIDDEN_IMPORTS or root in FORBIDDEN_IMPORTS:
                findings.append(
                    Finding(
                        SEVERITY_ERROR,
                        "safety.forbidden_import",
                        f"Import from '{module}' is blocked by the safety policy.",
                        cell_index,
                        section,
                        getattr(node, "lineno", None),
                    )
                )
            if module == "os":
                for alias in node.names:
                    if alias.name in {"system", "popen", "fork", "kill", "remove", "unlink"}:
                        findings.append(
                            Finding(
                                SEVERITY_ERROR,
                                "safety.forbidden_import",
                                f"'from os import {alias.name}' is blocked by the safety policy.",
                                cell_index,
                                section,
                                getattr(node, "lineno", None),
                            )
                        )
        elif isinstance(node, ast.Call):
            dotted = _dotted_name(node.func)
            if dotted in FORBIDDEN_CALLS or (
                dotted and any(dotted.startswith(prefix + ".") for prefix in FORBIDDEN_IMPORTS if "." in prefix)
            ):
                findings.append(
                    Finding(
                        SEVERITY_ERROR,
                        "safety.forbidden_call",
                        f"Call to '{dotted}' is blocked by the safety policy.",
                        cell_index,
                        section,
                        getattr(node, "lineno", None),
                    )
                )
            elif isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BARE_CALLS:
                findings.append(
                    Finding(
                        SEVERITY_ERROR,
                        "safety.forbidden_call",
                        f"Call to '{node.func.id}()' is blocked by the safety policy.",
                        cell_index,
                        section,
                        getattr(node, "lineno", None),
                    )
                )
            elif dotted == "getattr" and len(node.args) >= 2:
                attr = node.args[1]
                if isinstance(attr, ast.Constant) and isinstance(attr.value, str):
                    risky = {
                        "system",
                        "popen",
                        "fork",
                        "execv",
                        "spawnv",
                        "remove",
                        "unlink",
                        "rmtree",
                    }
                    if (
                        attr.value in DANGEROUS_DUNDERS
                        or attr.value.startswith("__")
                        or attr.value in risky
                    ):
                        findings.append(
                            Finding(
                                SEVERITY_ERROR,
                                "safety.dunder_access",
                                f"getattr() access to '{attr.value}' is blocked.",
                                cell_index,
                                section,
                                getattr(node, "lineno", None),
                            )
                        )

        if isinstance(node, ast.Attribute) and node.attr in DANGEROUS_DUNDERS:
            findings.append(
                Finding(
                    SEVERITY_ERROR,
                    "safety.dunder_access",
                    f"Access to '{node.attr}' is blocked (sandbox-escape pattern).",
                    cell_index,
                    section,
                    getattr(node, "lineno", None),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# U4: TF2 / Keras compatibility checks
# ---------------------------------------------------------------------------

_TF2_RULES: list[tuple[re.Pattern[str], str, str, str]] = [
    (re.compile(r"\btf\.compat\.v1\b"), SEVERITY_ERROR, "tf1.compat_v1", "TF1 compat mode is not allowed."),
    (re.compile(r"\btf\.Session\b"), SEVERITY_ERROR, "tf1.session", "tf.Session is TF1-only; use eager execution."),
    (re.compile(r"\btf\.placeholder\b"), SEVERITY_ERROR, "tf1.placeholder", "tf.placeholder is TF1-only; use tf.keras.Input."),
    (re.compile(r"\btf\.contrib\b"), SEVERITY_ERROR, "tf1.contrib", "tf.contrib was removed in TF2."),
    (re.compile(r"\btensorflow\.python\b"), SEVERITY_ERROR, "tf2.private_api", "Private tensorflow.python APIs are not allowed."),
    (re.compile(r"\.fit_generator\s*\("), SEVERITY_ERROR, "tf2.fit_generator", "fit_generator is removed; use model.fit()."),
    (re.compile(r"\.predict_generator\s*\("), SEVERITY_ERROR, "tf2.predict_generator", "predict_generator is removed; use model.predict()."),
    (re.compile(r"^\s*(?:import\s+keras\b|from\s+keras\b)", re.MULTILINE), SEVERITY_ERROR, "tf2.standalone_keras", "Import Keras via tensorflow.keras / tf.keras, not the standalone 'keras' package."),
    (re.compile(r"\btf\.keras\.backend\.set_session\b"), SEVERITY_ERROR, "tf2.set_session", "tf.keras.backend.set_session is TF1-era."),
    (re.compile(r"\bkeras\.utils\.multi_gpu_model\b"), SEVERITY_WARNING, "tf2.legacy_util", "multi_gpu_model is deprecated; use MirroredStrategy."),
    (re.compile(r"\bmodel\.fit\s*\([^)]*steps_per_epoch\s*=", re.DOTALL), SEVERITY_WARNING, "tf2.steps_per_epoch", "steps_per_epoch with a tf.data.Dataset is unnecessary unless using repeat()."),
]


def analyze_tf2(
    source: str,
    cell_index: int | None = None,
    section: str | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        for pattern, severity, code, message in _TF2_RULES:
            if pattern.search(line):
                findings.append(
                    Finding(severity, code, message, cell_index, section, line_number)
                )
    return findings


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def validate_code(
    source: str,
    cell_index: int | None = None,
    section: str | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(analyze_ast(source, cell_index, section))
    findings.extend(analyze_tf2(source, cell_index, section))
    return findings


def validate_code_sources(
    sources: Iterable[str],
    section: str = "llm",
) -> dict[str, object]:
    """Validate a set of LLM-produced code strings before injection."""

    source_list = list(sources)
    findings: list[Finding] = []
    for index, source in enumerate(source_list):
        findings.extend(validate_code(source, cell_index=index, section=section))
    return _build_report(findings, stats={"code_cells": len(source_list)})


def validate_notebook(notebook: dict[str, object]) -> dict[str, object]:
    findings: list[Finding] = []
    cells = notebook.get("cells", [])
    if not isinstance(cells, list):
        cells = []

    code_cells = 0
    python_lines = 0
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            continue
        cell_type = cell.get("cell_type")
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        if not isinstance(source, str):
            source = ""
        if cell_type == "code":
            code_cells += 1
            python_lines += len(source.splitlines())
            section = None
            metadata = cell.get("metadata") or {}
            if isinstance(metadata, dict):
                section = metadata.get("genai_section")
            findings.extend(validate_code(source, index, section))

    # Structural checks
    if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "structure.invalid_notebook",
                "Notebook must be nbformat 4 and contain a cells array.",
            )
        )

    # U5: the license cell is mandatory at the top.
    first_source = ""
    if cells and isinstance(cells[0], dict):
        first = cells[0].get("source", "")
        first_source = "".join(first) if isinstance(first, list) else str(first)
    if cells and (cells[0].get("cell_type") != "markdown" or "Dataset license" not in first_source):
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "license.missing",
                "The first cell must be a Markdown cell containing the dataset license.",
            )
        )

    text = _notebook_text(cells)
    metadata = notebook.get("metadata") if isinstance(notebook.get("metadata"), dict) else {}
    genai_meta = metadata.get("genai") if isinstance(metadata, dict) else {}
    model_kind = genai_meta.get("model_kind") if isinstance(genai_meta, dict) else None
    if model_kind != "text" and "Salesforce/blip-image-captioning-base" not in text:
        findings.append(
            Finding(
                SEVERITY_WARNING,
                "blip.missing",
                "No BLIP image-captioning cell was found (expected for image models).",
            )
        )

    report = _build_report(
        findings,
        stats={
            "cells": len(cells),
            "code_cells": code_cells,
            "python_lines": python_lines,
        },
    )
    report["checks"]["structure"] = (
        "failed"
        if any(f.code == "structure.invalid_notebook" for f in findings)
        else "passed"
    )
    report["checks"]["license"] = (
        "failed" if any(f.code == "license.missing" for f in findings) else "passed"
    )
    return report


def _notebook_text(cells: list[object]) -> str:
    parts: list[str] = []
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        source = cell.get("source", "")
        parts.append("".join(source) if isinstance(source, list) else str(source))
    return "\n".join(parts)


def _build_report(
    findings: list[Finding],
    stats: dict[str, int] | None = None,
) -> dict[str, object]:
    errors = [f for f in findings if f.severity == SEVERITY_ERROR]
    warnings = [f for f in findings if f.severity == SEVERITY_WARNING]

    def check_status(*codes_prefixes: str) -> str:
        relevant = [
            f
            for f in findings
            if any(f.code.startswith(prefix) for prefix in codes_prefixes)
        ]
        if any(f.severity == SEVERITY_ERROR for f in relevant):
            return "failed"
        return "passed"

    return {
        "passed": not errors,
        "checks": {
            "syntax": check_status("syntax."),
            "safety": check_status("safety."),
            "tf2": check_status("tf1.", "tf2."),
        },
        "errors": [f.to_dict() for f in errors],
        "warnings": [f.to_dict() for f in warnings],
        "stats": stats or {},
    }
