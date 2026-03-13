from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEFAULT_REPOS_LIST = REPO_ROOT / "repos_list.txt"


def _run_python_script(script_name: str, args: list[str]) -> int:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    cmd = [sys.executable, str(script_path), *args]
    return subprocess.call(cmd)


def _get_github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token

    # Fallback to gh auth token (if available)
    try:
        out = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except Exception:
        out = ""

    if not out:
        raise SystemExit(
            "Missing GITHUB_TOKEN and could not retrieve token from `gh auth token`."
        )
    return out


def cmd_rdme_toml2md(ns: argparse.Namespace) -> int:
    args: list[str] = ["--input", ns.input]
    if ns.output:
        args += ["--output", ns.output]
    if ns.overwrite:
        args += ["--overwrite"]
    return _run_python_script("convert_toml_to_readme.py", args)


def cmd_rdme_md2toml(ns: argparse.Namespace) -> int:
    args: list[str] = ["--input", ns.input]
    if ns.output:
        args += ["--output", ns.output]
    if ns.overwrite:
        args += ["--overwrite"]
    if ns.verbose:
        args += ["--verbose"]
    return _run_python_script("readme_to_toml.py", args)


def cmd_repos_fetch(ns: argparse.Namespace) -> int:
    # Fetch repos list via existing script to keep behavior identical.
    # The script reads PERSONAL_ACCESS_TOKEN and ORG_NAME (dotenv supported).
    # We allow overriding ORG_NAME via CLI.
    if ns.org:
        os.environ["ORG_NAME"] = ns.org
    if ns.token:
        os.environ["PERSONAL_ACCESS_TOKEN"] = ns.token

    # Script writes repos_list.txt to repo root.
    return _run_python_script("fetch_repos.py", [])


def cmd_workflow_trigger(ns: argparse.Namespace) -> int:
    org = ns.org
    repos_file = Path(ns.repos_file)
    workflow_file = ns.workflow_file
    ref = ns.ref

    if not repos_file.is_file():
        raise SystemExit(f"repos file not found: {repos_file}")

    token = _get_github_token()

    total = 0
    success = 0
    failed = 0
    skipped = 0

    import requests  # dependency already present in pyproject

    with repos_file.open("r", encoding="utf-8") as f:
        for raw in f:
            repo = raw.strip()
            if not repo or repo.startswith("#"):
                continue
            if repo == "course-template":
                skipped += 1
                continue

            total += 1
            url = f"https://api.github.com/repos/{org}/{repo}/actions/workflows/{workflow_file}/dispatches"
            if ns.dry_run:
                print(f"[DRY-RUN] POST {url} (ref={ref})")
                continue

            print(f"[{total}] Triggering {repo}... ", end="", flush=True)
            r = requests.post(
                url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {token}",
                },
                json={"ref": ref},
                timeout=30,
            )

            if r.status_code == 204:
                print("OK (204)")
                success += 1
            else:
                print(f"FAILED (HTTP {r.status_code})")
                failed += 1

            time.sleep(ns.delay)

    print("")
    print("=== Summary ===")
    print(f"Total:   {total}")
    print(f"Success: {success}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")

    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m repos_management",
        description="HITSZ-OpenAuto repository management CLI",
    )

    sp = p.add_subparsers(dest="group", required=True)

    # rdme
    rdme = sp.add_parser("rdme", help="README/TOML conversion")
    rdme_sp = rdme.add_subparsers(dest="command", required=True)

    toml2md = rdme_sp.add_parser("toml2md", help="Convert readme.toml -> README.md")
    toml2md.add_argument(
        "--input", "-i", required=True, help="Input TOML file or directory"
    )
    toml2md.add_argument("--output", "-o", help="Output path (single-file mode only)")
    toml2md.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing README"
    )
    toml2md.set_defaults(func=cmd_rdme_toml2md)

    md2toml = rdme_sp.add_parser("md2toml", help="Convert README.md -> readme.toml")
    md2toml.add_argument(
        "--input", "-i", required=True, help="Input README file or directory"
    )
    md2toml.add_argument(
        "--output", "-o", help="Output TOML path (single-file mode only)"
    )
    md2toml.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing TOML"
    )
    md2toml.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    md2toml.set_defaults(func=cmd_rdme_md2toml)

    # repos
    repos = sp.add_parser("repos", help="Repository list management")
    repos_sp = repos.add_subparsers(dest="command", required=True)

    fetch = repos_sp.add_parser("fetch", help="Fetch org repos into repos_list.txt")
    fetch.add_argument(
        "--org", default=None, help="GitHub org name (default from ORG_NAME env/.env)"
    )
    fetch.add_argument(
        "--token",
        default=None,
        help="PAT (default from PERSONAL_ACCESS_TOKEN env/.env)",
    )
    fetch.set_defaults(func=cmd_repos_fetch)

    # workflow
    wf = sp.add_parser("workflow", help="Workflows across course repos")
    wf_sp = wf.add_subparsers(dest="command", required=True)

    trigger = wf_sp.add_parser(
        "trigger", help="Trigger workflow_dispatch in all course repos"
    )
    trigger.add_argument("--org", default="HITSZ-OpenAuto", help="GitHub org")
    trigger.add_argument(
        "--repos-file",
        default=str(DEFAULT_REPOS_LIST),
        help="Repos list file (default: repos_list.txt)",
    )
    trigger.add_argument(
        "--workflow-file", default="trigger-workflow.yml", help="Workflow file name"
    )
    trigger.add_argument("--ref", default="main", help="Git ref for dispatch")
    trigger.add_argument(
        "--delay", type=float, default=2.0, help="Delay between calls (seconds)"
    )
    trigger.add_argument(
        "--dry-run", action="store_true", help="Print requests without executing"
    )
    trigger.set_defaults(func=cmd_workflow_trigger)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    func = getattr(ns, "func", None)
    if func is None:
        parser.print_help()
        return 2
    return int(func(ns))


if __name__ == "__main__":
    raise SystemExit(main())
