#!/usr/bin/env python3
"""RDME bidirectional TOML <-> README automation runner.

This script is designed to be executed inside *course repos* via a reusable
workflow. Course repos usually do not contain the generator scripts, so this
runner downloads the canonical converters from the central `repos-management`
repository and executes them.

Bidirectional sync logic:
- Detect which file changed via ``git diff HEAD~1 --name-only``
- TOML changed (or both changed) → forward: TOML → README  (TOML is source of truth)
- Only README changed           → reverse: README → TOML, then forward to normalise
- Neither (manual trigger)      → forward only
- readme.toml missing           → no-op

It also manages an idempotent WARNING block at the top of README.md:
- on success (main branch): clears the warning block
- on failure (main branch): ensures a warning block exists

Exit code:
- 0: success (or toml missing -> no-op)
- 1: formatting and/or generation failed
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

WARNING_START = "<!-- RDME_TOML_AUTOGEN_WARNING_START -->"
WARNING_END = "<!-- RDME_TOML_AUTOGEN_WARNING_END -->"

_BASE_RAW = (
    "https://raw.githubusercontent.com/HITSZ-OpenAuto/repos-management/main/scripts"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _append_github_output(key: str, value: str) -> None:
    out = os.getenv("GITHUB_OUTPUT")
    if not out:
        return
    Path(out).write_text("", encoding="utf-8") if not Path(out).exists() else None
    with Path(out).open("a", encoding="utf-8", newline="\n") as f:
        f.write(f"{key}={value}\n")


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _build_block(message: str) -> str:
    msg = (
        message or ""
    ).strip() or "TOML 自动化格式化/生成 README 失败，请检查 readme.toml。"
    lines = [
        WARNING_START,
        "> [!WARNING]",
        f"> {msg}",
        WARNING_END,
        "",
        "",
    ]
    return "\n".join(lines)


def _strip_block(text: str) -> str:
    if WARNING_START not in text:
        return text
    start = text.find(WARNING_START)
    end = text.find(WARNING_END)
    if end == -1:
        return text
    end = end + len(WARNING_END)

    after = text[end:]
    while after.startswith("\n"):
        after = after[1:]
    before = text[:start]
    if before.endswith("\n"):
        before = before[:-1]

    out = (before + "\n" + after) if before else after
    return out.lstrip("\n")


def _ensure_block_at_top(text: str, message: str) -> str:
    text = _strip_block(text)
    block = _build_block(message)
    if not text.strip():
        return block
    return block + text.lstrip("\n")


def _update_warning(readme_path: Path, *, set_warning: bool, message: str = "") -> None:
    text = ""
    if readme_path.exists():
        text = _normalize_newlines(readme_path.read_text(encoding="utf-8"))

    new_text = (
        _ensure_block_at_top(text, message) if set_warning else _strip_block(text)
    )
    if new_text != text:
        readme_path.write_text(new_text, encoding="utf-8", newline="\n")


def _download(url: str, dest: Path) -> None:
    # Support local file paths for testing: copy instead of HTTP download.
    if url.startswith("/") or url.startswith("file://"):
        import shutil as _shutil

        src = url.removeprefix("file://")
        _shutil.copy2(src, dest)
        return
    req = urllib.request.Request(url, headers={"User-Agent": "rdme-autogen"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        dest.write_bytes(resp.read())


def _run(cmd: list[str], *, cwd: Path) -> tuple[bool, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    ok = proc.returncode == 0
    out = (
        (proc.stdout or "")
        + ("\n" if proc.stdout and proc.stderr else "")
        + (proc.stderr or "")
    )
    return ok, out.strip()


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------


def _detect_direction(repo_root: Path, toml_name: str, readme_name: str) -> str:
    """Detect which file was modified in the latest commit.

    Returns one of: ``"toml"``, ``"readme"``, ``"both"``, ``"none"``.
    Falls back to ``"toml"`` (forward) on any error.
    """
    try:
        ok, out = _run(["git", "diff", "HEAD~1", "--name-only"], cwd=repo_root)
        if not ok:
            return "toml"
        changed = {line.strip() for line in out.strip().splitlines() if line.strip()}
        t = toml_name in changed
        r = readme_name in changed
        if t and r:
            return "both"
        if t:
            return "toml"
        if r:
            return "readme"
        return "none"
    except Exception:
        return "toml"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description="RDME bidirectional autogen runner")
    p.add_argument("--toml", default="readme.toml")
    p.add_argument("--readme", default="README.md")
    p.add_argument(
        "--converter-url",
        default=f"{_BASE_RAW}/convert_toml_to_readme.py",
    )
    p.add_argument(
        "--reverse-converter-url",
        default=f"{_BASE_RAW}/readme_to_toml.py",
    )
    args = p.parse_args()

    repo_root = Path.cwd()
    toml_path = repo_root / args.toml
    readme_path = repo_root / args.readme

    is_main = os.getenv("GITHUB_REF") == "refs/heads/main"

    toml_exists = toml_path.exists()
    readme_exists = readme_path.exists()
    _append_github_output("toml_exists", "true" if toml_exists else "false")

    if not toml_exists and not readme_exists:
        print(f"[rdme] no-op: neither {args.toml} nor {args.readme} found")
        return 0

    # --- Detect sync direction -------------------------------------------
    direction = _detect_direction(repo_root, args.toml, args.readme)
    print(f"[rdme] detected change direction: {direction}")

    # --- Migration check: README without HTML comment markers -----------
    #   If README exists but lacks <!-- TOML-META: -->, it was generated by
    #   the old (pre-bidirectional) converter.  Force forward (TOML → README)
    #   to inject the markers, regardless of which file changed.
    needs_migration = False
    if readme_exists and toml_exists:
        try:
            readme_text = readme_path.read_text(encoding="utf-8")
            if "<!-- TOML-META:" not in readme_text:
                needs_migration = True
                print(
                    "[rdme] README lacks TOML-META marker → forcing forward pass for migration"
                )
        except Exception:
            pass

    # Decision matrix:
    #   toml / both / none / workflow_dispatch → forward (TOML wins)
    #   readme (only README changed)          → reverse then forward
    #   needs_migration                       → forward only (skip reverse even if README changed)
    need_reverse = (
        direction == "readme" and toml_exists and readme_exists and not needs_migration
    )

    if not toml_exists and readme_exists:
        # Edge case: TOML doesn't exist yet but README does → reverse to bootstrap TOML
        need_reverse = True
        print("[rdme] readme.toml missing; will bootstrap from README.md")

    # --- Format TOML with taplo (skip when doing reverse first) ----------
    fmt_ok = True
    fmt_log = ""
    if not need_reverse:
        if shutil.which("taplo") is not None:
            fmt_ok, fmt_log = _run(["taplo", "fmt", str(toml_path)], cwd=repo_root)
        else:
            print("[rdme] taplo not found; skip formatting")

    # --- Download scripts ------------------------------------------------
    gen_ok = False
    gen_log = ""
    rev_ok = True
    rev_log = ""

    with tempfile.TemporaryDirectory(prefix="rdme-autogen-") as tmp:
        tmp_dir = Path(tmp)
        conv = tmp_dir / "convert_toml_to_readme.py"
        rev_conv = tmp_dir / "readme_to_toml.py"

        # Download forward converter (always needed)
        try:
            _download(args.converter_url, conv)
        except Exception as e:
            gen_ok = False
            gen_log = f"download converter failed: {e}"
            # Cannot proceed without forward converter
            ok = False
            _report_failure(
                is_main, readme_path, fmt_ok, fmt_log, gen_ok, gen_log, rev_ok, rev_log
            )
            return 0 if ok else 1

        # Download reverse converter (only when needed)
        if need_reverse:
            try:
                _download(args.reverse_converter_url, rev_conv)
            except Exception as e:
                rev_ok = False
                rev_log = f"download reverse converter failed: {e}"
                need_reverse = False  # fall back to forward only

        # --- Run reverse: README → TOML ---------------------------------
        if need_reverse and rev_ok:
            print("[rdme] running reverse: README.md → readme.toml")
            rev_ok, rev_log = _run(
                [
                    sys.executable,
                    str(rev_conv),
                    "--input",
                    str(readme_path.resolve()),
                    "--output",
                    str(toml_path.resolve()),
                    "--overwrite",
                ],
                cwd=repo_root,
            )
            if rev_ok:
                print("[rdme] reverse OK")
                # Format the newly generated TOML
                if shutil.which("taplo") is not None:
                    fmt_ok, fmt_log = _run(
                        ["taplo", "fmt", str(toml_path)], cwd=repo_root
                    )
            else:
                print("[rdme] reverse FAILED")
                if rev_log:
                    print(rev_log)

        # --- Run forward: TOML → README ---------------------------------
        print("[rdme] running forward: readme.toml → README.md")
        gen_ok, gen_log = _run(
            [
                sys.executable,
                str(conv),
                "--input",
                str(toml_path.resolve()),
                "--overwrite",
            ],
            cwd=tmp_dir,
        )

    ok = fmt_ok and gen_ok and rev_ok
    _report_failure(
        is_main, readme_path, fmt_ok, fmt_log, gen_ok, gen_log, rev_ok, rev_log
    )
    _append_github_output("direction", direction)
    _append_github_output("need_reverse", "true" if need_reverse else "false")
    return 0 if ok else 1


def _report_failure(
    is_main: bool,
    readme_path: Path,
    fmt_ok: bool,
    fmt_log: str,
    gen_ok: bool,
    gen_log: str,
    rev_ok: bool,
    rev_log: str,
) -> None:
    """Print error logs and manage WARNING block."""
    ok = fmt_ok and gen_ok and rev_ok

    if is_main:
        if ok:
            _update_warning(readme_path, set_warning=False)
        else:
            msg = "TOML 自动化格式化/生成 README 失败：请检查 readme.toml，并查看 Actions 日志。"
            _update_warning(readme_path, set_warning=True, message=msg)

    if not fmt_ok:
        print("[rdme] taplo fmt failed")
        if fmt_log:
            print(fmt_log)
    if not gen_ok:
        print("[rdme] generate README failed")
        if gen_log:
            print(gen_log)
    if not rev_ok:
        print("[rdme] reverse convert failed")
        if rev_log:
            print(rev_log)


if __name__ == "__main__":
    raise SystemExit(main())
