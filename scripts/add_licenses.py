import requests
import base64

# GitHub API base URL
base_url = "https://api.github.com"

# Your GitHub username and personal access token
username = "your_username"
token = "your_token"

# Organization name
org_name = "your org"

# URL of the license file
license_url = "https://raw.githubusercontent.com/GIST-CSBL/DeepConv-DTI/master/CC-BY-NC-SA-4.0"

# Repositories to exclude
repos_to_exclude = [".github", "hoa.moe"]

# Function to create a branch
def create_branch(repo_name, branch_name, base_commit, license_content):
    url = f"{base_url}/repos/{org_name}/{repo_name}/git/refs"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": f"refs/heads/{branch_name}",
        "sha": base_commit
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Branch {branch_name} created in {repo_name}")
        # Add license to the branch
        url = f"{base_url}/repos/{org_name}/{repo_name}/contents/LICENSE"
        content_encoded = base64.b64encode(license_content.encode()).decode()
        data = {
            "message": "Add LICENSE",
            "content": content_encoded,
            "branch": branch_name
        }
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"LICENSE added to {repo_name}")
        else:
            print(f"Failed to add LICENSE to {repo_name}: {response.text}")
        return True
    else:
        print(f"Failed to create branch {branch_name} in {repo_name}: {response.text}")
        return False

# Function to create a pull request
def create_pull_request(repo_name, branch_name, title, body):
    url = f"{base_url}/repos/{org_name}/{repo_name}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "head": branch_name,
        "base": "main",
        "body": body
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Pull request created for {repo_name}")
        return True
    else:
        print(f"Failed to create pull request for {repo_name}: {response.text}")
        return False

# Function to add or update license in a repository
def add_license_to_repo(repo_name, license_content, branch):
    url = f"{base_url}/repos/{org_name}/{repo_name}/contents/LICENSE"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    # Check if LICENSE already exists in the repository
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f"LICENSE already exists in {repo_name}. Skipping.")
        return

    # Retrieve the SHA of the base commit
    base_commit_url = f"{base_url}/repos/{org_name}/{repo_name}/branches/main"
    response = requests.get(base_commit_url, headers=headers)
    if response.status_code == 200:
        base_commit_sha = response.json()["commit"]["sha"]
    else:
        print(f"Failed to retrieve base commit SHA for {repo_name}: {response.text}")
        return

    # Check if the repository is protected
    protection_url = f"{base_url}/repos/{org_name}/{repo_name}/branches/main/protection"
    response = requests.get(protection_url, headers=headers)
    if response.status_code == 200:
        repo_is_protected = True
    else:
        repo_is_protected = False

    # If the repository is protected, create a branch and a pull request
    if repo_is_protected:
        branch_name = "add-license"
        title = "Add LICENSE"
        body = "This pull request adds a LICENSE file to the repository."
        create_branch(repo_name, branch_name, base_commit_sha, license_content)
        url += f"?ref={branch_name}"
        create_pull_request(repo_name, branch_name, title, body)
    else:
        # Encode the content in Base64
        content_encoded = base64.b64encode(license_content.encode()).decode()
        data = {
            "message": "Add LICENSE",
            "content": content_encoded,
            "branch": branch
        }
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"LICENSE added to {repo_name}")
        else:
            print(f"Failed to add LICENSE to {repo_name}: {response.text}")

# Function to get license content from URL
def get_license_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch license content from {url}: {response.text}")
        return None

# Function to get list of repositories in the organization
def get_org_repos():
    url = f"{base_url}/orgs/{org_name}/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repos = [repo["name"] for repo in response.json()]
        # Exclude repositories
        repos = [repo for repo in repos if repo not in repos_to_exclude]
        return repos
    else:
        print(f"Failed to fetch repositories: {response.text}")
        return []

# Main function
def main():
    license_content = get_license_content(license_url)
    if license_content:
        repos = get_org_repos()
        if repos:
            for repo in repos:
                add_license_to_repo(repo, license_content, branch="main")

if __name__ == "__main__":
    main()
