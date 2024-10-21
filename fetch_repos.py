import requests

# Replace with your personal access token and organization name
ACCESS_TOKEN = "your_PAT_token"
ORG_NAME = 'HITSZ-OpenAuto'

def get_repos(org_name, access_token):
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

def main():
    repos = get_repos(ORG_NAME, ACCESS_TOKEN)
    with open('repos_list.txt', 'w') as f:
        for repo in repos:
            f.write(f'{repo}\n')

if __name__ == '__main__':
    main()
