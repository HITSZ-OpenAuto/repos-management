<div align="center">

# repos-management

用于管理 **HITSZ-OpenAuto** 组织下课程仓库的工具集。

[中文](README.zh-CN.md) | [English](README.md)

</div>

---

## 本仓库做什么

本仓库提供：

- 一个统一的 **Python CLI** 入口，用于常用操作：
  - `readme.toml` ⇄ `README.md` 双向转换
  - 批量触发课程仓库 GitHub Actions workflows
  - 获取/维护组织仓库列表（`repos_list.txt`）
- 课程仓库用于生成/更新 worktree 的 **reusable GitHub Actions workflow**。

推荐使用方式：

```bash
python3 -m repos_management --help
```

---

## 环境要求

- Python **3.11+**
- 可选（推荐）：[GitHub CLI](https://cli.github.com/)（`gh`）

---

## 快速开始

### 1) TOML → README

```bash
python3 -m repos_management rdme toml2md --input path/to/readme.toml --overwrite
```

### 2) README → TOML

```bash
python3 -m repos_management rdme md2toml --input path/to/README.md --overwrite
```

### 3) 批量触发所有课程仓库 workflow

```bash
python3 -m repos_management workflow trigger --delay 2
```

只预览不执行：

```bash
python3 -m repos_management workflow trigger --dry-run
```

---

## 认证（Token）

### `workflow trigger`

- 优先使用环境变量 `GITHUB_TOKEN`
- 若未设置，则尝试使用 `gh auth token`

token 需要能够 dispatch workflow（常见 scope：`repo`, `workflow`）。

### `repos fetch`

- 默认读取环境变量/`.env` 中的 `PERSONAL_ACCESS_TOKEN`
- 也可通过 `--token` 显式传入

常见 scope：`read:org`, `repo`。

---

## CLI 参考

### `rdme toml2md`

将 `readme.toml` 转换为 `README.md`。

```bash
python3 -m repos_management rdme toml2md --input <文件或目录> [--output <文件>] [--overwrite]
```

- 若 `--input` 是目录，会扫描 `**/readme.toml`，并在同目录生成 `README.md`

### `rdme md2toml`

将 `README.md` 转换为 `readme.toml`。

```bash
python3 -m repos_management rdme md2toml --input <文件或目录> [--output <文件>] [--overwrite] [--verbose]
```

- 若 `--input` 是目录，会扫描 `**/README.md`，并在同目录生成 `readme.toml`

### `workflow trigger`

对每个课程仓库的 workflow（默认：`trigger-workflow.yml`）发起 `workflow_dispatch`：

```bash
python3 -m repos_management workflow trigger \
  --org HITSZ-OpenAuto \
  --repos-file repos_list.txt \
  --workflow-file trigger-workflow.yml \
  --ref main \
  --delay 2
```

### `repos fetch`

拉取组织下仓库列表并写入 `repos_list.txt`。

```bash
python3 -m repos_management repos fetch --org HITSZ-OpenAuto
```

---

## lecturers TOML 结构（破坏性变更）

仅支持 **新版** lecturers 结构：

```toml
[lecturers]

[[lecturers.intro]]
content = "..."  # 可选
# author 可选
# author = { name = "", link = "", date = "" }

[[lecturers.items]]
name = "郑宜峰"

[[lecturers.items.reviews]]
content = "挺好的老师，交流时感觉很亲切。"
# author 可选
# author = { name = "xxx", link = "xxx", date = "xxx" }

[[lecturers.summary]]
content = "..."  # 可选
```

旧版 `[[lecturers]]` / `[[lecturers.reviews]]` **不再支持**，会直接报错。

---

## 课程仓库 CI 工作方式（概览）

典型课程仓库包含：

- `.github/workflows/trigger-workflow.yml`

它会调用本仓库的 reusable workflow：

```yaml
uses: HITSZ-OpenAuto/repos-management/.github/workflows/reusable_worktree_generate.yml@main
```

当 `repos-management` 的改动合并到 `main` 后，如需让所有课程仓库更新，可运行：

```bash
python3 -m repos_management workflow trigger
```

---

## 维护脚本

强力工具保留在 `./scripts/` 下，**不保证是稳定 CLI 接口**（默认不纳入 `python3 -m repos_management` 的子命令）。

| 脚本 | 用途 | 依赖 | 风险 |
|---|---|---|---|
| `rdme_autogen.py` | 课程仓库 CI 中的执行器：从本仓库下载转换器并执行双向同步逻辑。 | 课程仓库内 `git`；可选 `taplo` | 低 |
| `generate_worktree_info.py` | 生成 worktree 元数据 JSON 并推送到 `worktree` 分支（组织自动化会用）。 | `git` + 需要 push 权限 | 中 |
| `approve_pr.sh` | 批量 **approve + squash merge + 删除分支**：对每个仓库标题包含 `[automated-generated-pr]` 的最新 PR 执行。 | 已登录 `gh`；需要管理员合并权限 | 高 |
| `close_pr.sh` | 批量关闭标题包含 `[automated-generated-pr]` 的 PR 并删除分支。 | 已登录 `gh` | 高 |
| `delete_dir.sh` | **无需 clone** 即删除仓库内目录（GraphQL `createCommitOnBranch`）并创建 PR。 | `gh`, `jq` | 高 |
| `batch_delete.sh` | 读取 `repos_list.txt` 批量调用 `delete_dir.sh`（带超时和汇总）。 | `bash`, `timeout` + `delete_dir.sh` 依赖 | 高 |

### 示例

批准并合并所有自动化 PR：

```bash
bash scripts/approve_pr.sh
```

批量删除各课程仓库的 `.hoa/` 目录（创建 PR）：

```bash
bash scripts/batch_delete.sh HITSZ-OpenAuto main .hoa
```

> 注意：这些脚本会对大量仓库生效，建议先挑少量仓库测试或先读脚本确认参数。
