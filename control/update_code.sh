#!/bin/bash

function get_branch() {
    git branch | grep '^\*' | sed 's/* //'
}

function abort () {
    echo $1
    echo -e "Aborting."
    exit 1
}

function check_for_changes() {
    branch=$(get_branch)

    if [[ $branch != 'master' ]]
    then
           abort "$1 not on master."
    fi

    changes=$(git diff HEAD)
    if [[ $changes != '' ]]
    then
       abort "$1 has uncommitted changes:\n $changes"
    fi
}

function update_repo() {
    git fetch --prune || abort "Fetch failed. This can happen if you do not have ForwardAgent enabled on your SSH connection."
    git checkout master
    git reset --hard origin/master
    git submodule update --init --recursive
}

repos="$HOME/commcare-cloud"

# if environments points to a separate Git repo, update that as well
if [ -n "$COMMCARE_CLOUD_ENVIRONMENTS" ] && \
   [ ! "$COMMCARE_CLOUD_ENVIRONMENTS" -ef "$HOME/commcare-cloud/environments" ] && \
   [ -d "$(dirname $COMMCARE_CLOUD_ENVIRONMENTS)/.git" ]
then
  repos="${repos} $(dirname $COMMCARE_CLOUD_ENVIRONMENTS)"
fi

for repo in $repos
do
    cd $repo
    pwd
    check_for_changes $repo
    update_repo
done
