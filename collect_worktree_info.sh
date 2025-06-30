#!/bin/bash

set -e
set -o pipefail

main () {
    local files=$(mktemp /tmp/XXXXXX.files)
    local times=$(mktemp /tmp/XXXXXX.times)
    local sizes=$(mktemp /tmp/XXXXXX.sizes)
    local hashs=$(mktemp /tmp/XXXXXX.hashs)

    # build commit-graph first to accelerate git-log
    git commit-graph write --reachable

    # TODO: merge two git-log into one command for performance
    git ls-tree --name-only -r HEAD | xargs -I{} printf "{}\n" > $files
    cat $files | xargs -n 1 git log -1 --format="%cd" --date=unix -- > $times
    cat $files | xargs -n 1 git log -1 --format="%H" -- > $hashs
    cat $files | xargs -n 1 git ls-files --format="%(objectsize)" -- > $sizes

    # Check wc -l matches
    local num_files=$(cat $files | wc -l)
    local num_times=$(cat $times | wc -l)
    local num_sizes=$(cat $sizes | wc -l)
    local num_hashs=$(cat $hashs | wc -l)
    if   [ "$num_files" != "$num_times" ] \
      || [ "$num_files" != "$num_sizes" ] \
      || [ "$num_files" != "$num_hashs" ]; then
        echo 'Error: `wc -l` mismatch'
        exit 1
    fi

    # Split three lists into heads and last line
    head -n -1 $files > $files.head
    head -n -1 $times > $times.head
    head -n -1 $sizes > $sizes.head
    head -n -1 $hashs > $hashs.head
    local last_file=$(tail -n 1 $files)
    local last_time=$(tail -n 1 $times)
    local last_size=$(tail -n 1 $sizes)
    local last_hash=$(tail -n 1 $hashs)

    echo "["
    # if len of $files.head is not zero
    if [ -n "$files.head" ]; then
        paste $files.head $times.head $sizes.head $hashs.head | xargs -n 4 printf '{"path": "%s", "time": %s, "size": %s, "commit": "%s"},\n'
    fi
    printf '{"path": "%s", "time": %s, "size": %s, "commit": "%s"}\n' "$last_file" "$last_time" "$last_size" "$last_hash"
    echo "]"

    rm $files $times $sizes
}

main
