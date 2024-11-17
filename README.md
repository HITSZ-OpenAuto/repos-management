# 仓库管理脚本

环境：

- Linux
- Git
- [GitHub CLI](https://cli.github.com/)
- Python 3

## 创建 Personal Access Token

在 GitHub 网页版的 `Settings` -> `Developer settings` -> `Personal access tokens` 中创建一个 GitHub Personal Access Token，权限至少包含 `repo` 和 `workflow`。将其保存到 `.env` 文件中：

```bash
PERSONAL_ACCESS_TOKEN=<your_token_here>
```

## [repos_list.txt](./repos_list.txt)

HOA 仓库列表，**行尾序列为 LF，请在 Linux 环境下读取**。

## [approve-pr.sh](./approve-pr.sh)

批量批准 [`repos_list.txt`](./repos_list.txt) 下所有仓库的最新 PR。

一般用于更新仓库的 workflow 等。

## [add_workflow.sh](./add_workflow.sh)

批量为 [`repos_list.txt`](./repos_list.txt) 下所有仓库添加/覆写 workflow 文件。

如果要覆写，请将更新的内容写到 `read -r -d '' WORKFLOW_CONTENT << 'EOF'` 后面。
