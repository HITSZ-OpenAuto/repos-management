import os
import subprocess
from github import Github

# 替换为你的 GitHub 访问令牌
GITHUB_TOKEN = "your_token"
# 替换为目标组织名
ORGANIZATION_NAME = "HITSZ-OpenAuto"
# 替换为目标文件夹路径
TARGET_FOLDER = "./"
# 替换为你的代理地址
os.environ["HTTP_PROXY"] = "http://your_proxy:port"
os.environ["HTTPS_PROXY"] = "http://your_proxy:port"

# 跳过的仓库
bypass_list = ["HITSZ-OpenAuto", "hoa-moe"]


def clone_or_update_repo(repo_url, target_path):
    """克隆或更新仓库，并显示进度，如果有错误则停止"""
    if os.path.exists(target_path):
        if os.path.isdir(os.path.join(target_path, ".git")):
            print(f"Updating repository: {repo_url}")
            result = subprocess.run(["git", "-C", target_path, "pull"], check=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
        else:
            raise Exception(f"Invalid Git directory: {target_path}")
    else:
        print(f"Cloning repository: {repo_url}")
        result = subprocess.run(["git", "clone", repo_url, target_path], check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)


def main():
    # 初始化 GitHub 客户端
    g = Github(GITHUB_TOKEN)

    # 获取组织
    org = g.get_organization(ORGANIZATION_NAME)

    # 确保目标文件夹存在
    os.makedirs(TARGET_FOLDER, exist_ok=True)

    # 获取所有仓库
    for repo in org.get_repos():
        repo_name = repo.name
        if repo_name in bypass_list:
            print("Skipping {}".format(repo_name))
            continue
        repo_url = repo.ssh_url
        target_path = os.path.join(TARGET_FOLDER, repo_name)

        try:
            clone_or_update_repo(repo_url, target_path)
        except subprocess.CalledProcessError as e:
            print(f"Failed to process repository {repo_name}: {e}")
            raise
        except Exception as e:
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    main()
