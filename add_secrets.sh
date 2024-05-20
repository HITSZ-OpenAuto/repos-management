#!/bin/zsh

# Read .env file
PAT=$(cat .env)

# Read the list of repositories from the file
REPOS=$(cat repos_list.txt)

# Loop through the repositories and add the secret
for REPO in $REPOS; do
  echo "Adding secret to $REPO"
  gh secret set PERSONAL_ACCESS_TOKEN -b"$PAT" -R "HITSZ-OpenAuto/$REPO"
done
