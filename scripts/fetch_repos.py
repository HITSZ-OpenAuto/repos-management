import os
import requests
from dotenv import load_dotenv

# Load the personal access token from the .env file
load_dotenv()
PERSONAL_ACCESS_TOKEN = os.getenv("PERSONAL_ACCESS_TOKEN")
ORG_NAME = os.getenv("ORG_NAME")


def get_repos(org_name, access_token):
    url = f"https://api.github.com/orgs/{org_name}/repos"
    headers = {"Authorization": f"token {access_token}"}
    repos = []

    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # exclude repo named 'HITSZ-OpenAuto' .github and 'hoa-moe'
        data = [
            repo
            for repo in data
            if repo["name"] != "HITSZ-OpenAuto"
            and repo["name"] != ".github"
            and not repo["name"].startswith("hoa-")
            and repo["name"] != "aextra"
            and not repo["name"].startswith("repos-")
            and not repo["name"].startswith("dev-")
        ]
        repos.extend(repo["name"] for repo in data)
        url = response.links.get("next", {}).get("url")

    return repos


def main():
    repos = get_repos(ORG_NAME, PERSONAL_ACCESS_TOKEN)
    with open("repos_list.txt", "w") as f:
        for repo in repos:
            f.write(f"{repo}\n")


if __name__ == "__main__":
    main()
