# Description: Clone all repositories EXCEPT [HITSZ-OpenAuto] in the organization HITSZ-OpenAuto to your local machine.

import requests
import os

# Replace with your personal access token and organization name
ACCESS_TOKEN = '<your-access-token>'
ORG_NAME = 'HITSZ-OpenAuto'

def clone_repos(org_name, access_token):
    url = f'https://api.github.com/orgs/{org_name}/repos'
    headers = {'Authorization': f'token {access_token}'}
    repos = []
    
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        repos.extend(repo['name'] for repo in data)
        url = response.links.get('next', {}).get('url')
    
    return repos

if __name__ == '__main__':
    repos = clone_repos(ORG_NAME, ACCESS_TOKEN)
    with open('repos_list.txt', 'w') as f:
        for repo in repos:
            if repo != 'HITSZ-OpenAuto': # Skip HITSZ-OpenAuto, the archived repo
                os.system(f'git clone https://github.com/{ORG_NAME}/{repo}.git')
    