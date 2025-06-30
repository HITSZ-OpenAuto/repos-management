# 仓库管理脚本

环境：

- Linux
- Git
- [GitHub CLI](https://cli.github.com/)
- Python 3（推荐 3.9 及以上）

## 创建 Personal Access Token

在 GitHub 网页版的 `Settings` -> `Developer settings` -> `Personal access tokens` 中创建一个 GitHub Personal Access Token，权限至少包含 `repo` 和 `workflow`。将其保存到 `.env` 文件中：

```bash
PERSONAL_ACCESS_TOKEN=<your_token_here>
```

## [fetch_repos.py](./fetch_repos.py)

获取所有仓库名（排除 'HITSZ-OpenAuto'、'.github' 与 'hoa-moe'）。

## [repos_list.txt](./repos_list.txt)

组织下所有仓库的列表，**注意行尾序列应该为 LF**。

## [approve_pr.sh](./approve-pr.sh)

批量批准 [`repos_list.txt`](./repos_list.txt) 下所有仓库的最新 PR。

一般用于更新仓库的 workflow 等。

## [add_workflow.sh](./add_workflow.sh)

批量为 [`repos_list.txt`](./repos_list.txt) 下所有仓库添加/覆写 workflow 文件。

如果要覆写，请将更新的内容写到 `read -r -d '' WORKFLOW_CONTENT << 'EOF'` 后面。

## [pull_or_clone.py](./pull_or_clone.py)

对于所有仓库，若本地有对应仓库文件夹，则拉取主分支；否则克隆仓库。可以通过 bypass_list 列表指定排除的仓库。

## [collect_worktree_info.sh](./collect_worktree_info.sh)

收集仓库的文件信息（包括文件名、大小、修改时间等），保存为 .json 格式的文件。

## [add_licenses.py](./add_licenses.py)

批量为 [`repos_list.txt`](./repos_list.txt) 下所有仓库添加许可证文件。

## [add_secrets.py](./add_secrets.py)

批量为 [`repos_list.txt`](./repos_list.txt) 下所有仓库添加 Secrets。
