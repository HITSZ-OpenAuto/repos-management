<div align="center">

# repos-management

Tooling for managing course repositories in **HITSZ-OpenAuto**.

[English](README.md) | [中文](README.zh-CN.md)

</div>

---

## What this repo does

This repository provides:

- A **single CLI** entrypoint for common operations:
  - Convert `readme.toml` ⇄ `README.md`
  - Bulk-trigger course repositories GitHub Actions workflows
  - Fetch and maintain the organization repositories list (`repos_list.txt`)
- The **reusable GitHub Actions workflow** used by course repositories to generate/update their worktrees.

The preferred way to use this repo is:

```bash
python3 -m repos_management --help
```

---

## Requirements

- Python **3.11+**
- Optional (recommended): [GitHub CLI](https://cli.github.com/) (`gh`)

---

## Quickstart

### 1) Convert TOML → README

```bash
python3 -m repos_management rdme toml2md --input path/to/readme.toml --overwrite
```

### 2) Convert README → TOML

```bash
python3 -m repos_management rdme md2toml --input path/to/README.md --overwrite
```

### 3) Trigger all course repositories workflows

```bash
python3 -m repos_management workflow trigger --delay 2
```

Dry-run:

```bash
python3 -m repos_management workflow trigger --dry-run
```

---

## Authentication

### `workflow trigger`

- Uses `GITHUB_TOKEN` if set.
- Otherwise falls back to `gh auth token`.

The token must be able to dispatch workflows (typical scopes: `repo`, `workflow`).

### `repos fetch`

- Uses `PERSONAL_ACCESS_TOKEN` from env or `.env`.
- You can also pass `--token` explicitly.

Typical scopes: `read:org`, `repo`.

---

## CLI reference

### `rdme toml2md`

Convert `readme.toml` → `README.md`.

```bash
python3 -m repos_management rdme toml2md --input <file-or-dir> [--output <file>] [--overwrite]
```

- If `--input` is a directory, it scans `**/readme.toml` and writes `README.md` next to each file.

### `rdme md2toml`

Convert `README.md` → `readme.toml`.

```bash
python3 -m repos_management rdme md2toml --input <file-or-dir> [--output <file>] [--overwrite] [--verbose]
```

- If `--input` is a directory, it scans `**/README.md` and writes `readme.toml` next to each file.

### `workflow trigger`

Trigger each course repo workflow file (default: `trigger-workflow.yml`) via `workflow_dispatch`.

```bash
python3 -m repos_management workflow trigger \
  --org HITSZ-OpenAuto \
  --repos-file repos_list.txt \
  --workflow-file trigger-workflow.yml \
  --ref main \
  --delay 2
```

### `repos fetch`

Fetch repositories under an org and write `repos_list.txt`.

```bash
python3 -m repos_management repos fetch --org HITSZ-OpenAuto
```

---

## Lecturers TOML schema (breaking change)

Only the **new** lecturers schema is supported:

```toml
[lecturers]

[[lecturers.intro]]
content = "..."  # optional
# author is optional
# author = { name = "", link = "", date = "" }

[[lecturers.items]]
name = "郑宜峰"

[[lecturers.items.reviews]]
content = "挺好的老师，交流时感觉很亲切。"
# author is optional
# author = { name = "xxx", link = "xxx", date = "xxx" }

[[lecturers.summary]]
content = "..."  # optional
```

Legacy TOML `[[lecturers]]` / `[[lecturers.reviews]]` is **not supported** and will raise an error.

---

## How course repositories CI works (high-level)

A typical course repository contains:

- `.github/workflows/trigger-workflow.yml`

This workflow calls the reusable workflow in this repo:

```yaml
uses: HITSZ-OpenAuto/repos-management/.github/workflows/reusable_worktree_generate.yml@main
```

To update all course repositories after `repos-management` changes are merged to `main`, run:

```bash
python3 -m repos_management workflow trigger
```

---

## Maintenance scripts

Some power tools remain in `./scripts/` (use with care):

- `approve_pr.sh`, `close_pr.sh`
- `delete_dir.sh`, `batch_delete.sh`
- `generate_worktree_info.py`
- `rdme_autogen.py` (used by course repositories CI to orchestrate conversion)
