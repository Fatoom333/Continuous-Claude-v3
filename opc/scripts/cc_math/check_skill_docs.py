#!/usr/bin/env python3
"""Run every cc_math command documented in skill markdown files and report the ones that fail.

USAGE:
    python check_skill_docs.py <skills_dir> [<skills_dir> ...] [--jobs 8] [--verbose]

A command is any `<script>.py <subcommand> ...` found inside backticks or a fenced
code block. Concrete commands run via `uv run --script` against the scripts next to
this file. Templates (containing `<name>` placeholders or `...`) are not run, but
their subcommand and every `--flag` must exist in the script's --help.
"""

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = {p.name for p in HERE.glob("*.py")}
CMD_RE = re.compile(r'([a-z_0-9]+\.py)"?\s+([a-z_0-9]+)(.*)')
PLACEHOLDER_RE = re.compile(r"<[A-Za-z_][A-Za-z0-9_]*>|\.\.\.")
DATA_FENCES = {"json", "yaml", "text", "txt", "output"}
# Examples may write files (plots); keep them out of the repo
WORKDIR = tempfile.mkdtemp(prefix="skill-docs-")
_help_cache: dict = {}


def uv_run(script: str, args: list, timeout: int = 90) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "--quiet", "--script", str(HERE / script), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
        cwd=WORKDIR,
    )


def subcommand_help(script: str, sub: str):
    if (script, sub) not in _help_cache:
        proc = uv_run(script, [sub, "--help"])
        _help_cache[(script, sub)] = proc.stdout if proc.returncode == 0 else None
    return _help_cache[(script, sub)]


def check_template(cmd: str):
    parts = cmd.split()
    script, sub = parts[0].strip('"'), parts[1]
    if script not in SCRIPTS:
        return "FAIL", f"no such script: {script}"
    help_text = subcommand_help(script, sub)
    if help_text is None:
        return "FAIL", f"no such subcommand: {sub}"
    bad = [f for f in re.findall(r"(?<!\S)(--[a-z][a-z0-9_-]*)", cmd) if f not in help_text]
    return ("FAIL", f"unknown flags: {' '.join(bad)}") if bad else ("TMPL", "")


def extract(md: Path):
    in_fence, skip_fence = False, False
    lines = md.read_text(encoding="utf-8").splitlines()
    pending, start = "", 0
    for lineno, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            skip_fence = in_fence and line.strip()[3:].strip().lower() in DATA_FENCES
            continue
        if skip_fence:
            continue
        if in_fence and line.rstrip().endswith("\\"):
            pending, start = pending + line.rstrip()[:-1] + " ", start or lineno
            continue
        if pending:
            line, lineno, pending, start = pending + line.strip(), start, "", 0
        if in_fence and line.strip().startswith("uv run") and " python -c " in line:
            yield md, lineno, line.strip(), "raw"
            continue
        spans = [line] if in_fence else re.findall(r"`([^`]+)`", line)
        for span in spans:
            span = span.rstrip("\\").strip()
            m = CMD_RE.search(span)
            if not m:
                continue
            cmd = m.group(1) + " " + m.group(2) + m.group(3)
            # A bare `script.py sub` is a reference, checked like a template
            is_template = PLACEHOLDER_RE.search(span) or not m.group(3).strip()
            yield md, lineno, cmd, "template" if is_template else "run"


def run(item):
    md, lineno, cmd, mode = item
    if mode == "template":
        return (item, *check_template(cmd))
    if mode == "raw":
        try:
            proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, cwd=WORKDIR,
                                  encoding="utf-8", errors="replace", timeout=180)
        except subprocess.TimeoutExpired:
            return item, "FAIL", "timeout after 180s"
        out = (proc.stderr or proc.stdout or "").strip().splitlines()
        if proc.returncode != 0:
            return item, "FAIL", out[-1] if out else f"exit {proc.returncode}"
        return item, "OK", (proc.stdout or "").strip()[:120]
    try:
        parts = shlex.split(cmd, comments=True, posix=True)
    except ValueError as e:
        return item, "FAIL", f"unparseable: {e}"
    script = parts[0]
    if script not in SCRIPTS:
        return item, "FAIL", f"no such script: {script}"
    try:
        proc = uv_run(script, parts[1:])
    except subprocess.TimeoutExpired:
        return item, "FAIL", "timeout after 90s"
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        return item, "FAIL", (err or out).splitlines()[-1] if (err or out) else f"exit {proc.returncode}"
    try:
        data = json.loads(out)
        if isinstance(data, dict) and data.get("error"):
            return item, "FAIL", f"error: {data['error']}"
    except json.JSONDecodeError:
        pass
    return item, "OK", out[:120].replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    items = [it for d in args.dirs for md in sorted(Path(d).rglob("*.md")) for it in extract(md)]
    with ThreadPoolExecutor(args.jobs) as pool:
        results = list(pool.map(run, items))
    shutil.rmtree(WORKDIR, ignore_errors=True)

    counts = {"OK": 0, "TMPL": 0, "FAIL": 0}
    for (md, lineno, cmd, _), status, detail in results:
        counts[status] += 1
        if status == "FAIL" or args.verbose:
            print(f"{status:4} {md}:{lineno}\n     {cmd}\n     -> {detail}")
    print(f"\nOK {counts['OK']}  TEMPLATE-OK {counts['TMPL']}  FAIL {counts['FAIL']}")
    sys.exit(1 if counts["FAIL"] else 0)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    main()
