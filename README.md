# 仓库管理脚本

环境：
- Linux
- Git
- [GitHub CLI](https://cli.github.com/)
- Python 3

## [repos_list.txt](./repos_list.txt)

HOA 仓库列表，**行尾序列为 LF，请在 Linux 环境下读取**。

## [approve-pr.sh](./approve-pr.sh)

批量批准 [`repos_list.txt`](./repos_list.txt) 下所有仓库的最新 PR。

一般用于更新仓库的 workflow 等。

需要在 Linux bash / zsh 中运行。
