#!/usr/bin/env python3
import subprocess
import json
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cmd(cmds, cwd=None) -> bytes:
    try:
        result = subprocess.run(
            cmds,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            cwd=cwd,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing git command: {cmds}")
        print(f"Error output: {e.stderr.strip()}")
        sys.exit(1)


def is_digit_in_ascii(c: int) -> bool:
    return ord("0") <= c <= ord("9")


def decode_git_ls_tree_path(content: bytes) -> str:
    escaped_array = []

    if content.startswith(b'"'):
        if not content.endswith(b'"'):
            raise RuntimeError(
                f"Invalid git ls-tree output: path ill-quoted: {content}"
            )
        content = content[1:-1]

    idx, end = 0, len(content)
    while idx < end:
        c = content[idx]
        if c != ord(b"\\"):
            escaped_array.append(c)
            idx += 1
            continue

        # now c is '\', check escaping
        idx += 1
        if idx >= end:
            raise RuntimeError(
                f"Invalid git ls-tree output: path ill-escaped, ending with hangling backslash: {content}"
            )
        escaped_alpha = content[idx]
        # check octal esaped character
        if is_digit_in_ascii(escaped_alpha):
            value_literal = content[idx : idx + 3]
            if idx + 3 > end or not all(is_digit_in_ascii(c) for c in value_literal):
                raise RuntimeError(
                    f"Invalid git ls-tree output: path ill-escaped, wrong octal escape sequence: {content}"
                )
            value = int(value_literal, 8)
            escaped_array.append(value)
            idx += 3
            continue
        # check 'normal' C-liked escaped character
        try:
            value_bytes = eval(rf'b"\{chr(escaped_alpha)}"')
            assert isinstance(value_bytes, bytes) and len(value_bytes) == 1
        except SyntaxWarning or SyntaxError or AssertionError:
            raise RuntimeError(
                f"Invalid git ls-tree output: path ill-escaped, wrong escaped character: {content}"
            )
        escaped_array.append(ord(value_bytes))
        idx += 1

    assert idx == end
    return bytes(escaped_array).decode("utf-8")


def main():
    # 构建 commit-graph 以加速 git log
    cmd(["git", "commit-graph", "write", "--reachable"])

    # 准备存储文件信息的列表, path -> {size (bolb-size), time (commit-date), hash (commit-hash)}
    files_data: dict[str, dict] = {}

    # 获取文件列表和大小
    ls_tree_output = cmd(
        ["git", "ls-tree", "-r", "HEAD", "--format=%(objectsize)%x00%(path)"]
    )
    for line in ls_tree_output.splitlines():
        size, path_raw = line.split(b"\0")
        # print(path, len(path))
        path = decode_git_ls_tree_path(path_raw)
        # print(path_str, len(path_str))
        files_data[path] = {"size": int(size)}

    # 获取提交时间和哈希
    files_path = list(files_data.keys())
    for file_path in files_path:
        time_hash = cmd(
            ["git", "log", "-1", "--format=%cd%x00%H", "--date=unix", "--", file_path]
        )
        timestamp, commit_hash = time_hash.split(b"\0")

        files_data[file_path]["time"] = int(timestamp)
        files_data[file_path]["hash"] = commit_hash.decode("ascii")

    # 输出到指定的文件夹并保存为 JSON 格式
    output_folder = ".hoa"
    output_file = "worktree.json"
    os.makedirs(output_folder, exist_ok=True)
    with open(os.path.join(output_folder, output_file), "w", encoding="utf-8") as f:
        json.dump(files_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Worktree info saved to {os.path.join(output_folder, output_file)}")


if __name__ == "__main__":
    main()
