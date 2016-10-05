#!/bin/bash
# Runs appcfg.py update after prompting for the application name and version,
# reading defaults from app.yaml and the ouput of git describe --tags.
#
# Assumes this is run from the project root directory.
#
# Any arguments are passed to appcfg.py e.g.
# ./deploy.sh --oauth2

set -eu

pushd "$(dirname "$0")"

APPLICATION=$(grep -E '^application:' app.yaml | sed 's/application: *//')
VERSION=$(git describe --tags | tr '[:upper:].' '[:lower:]-')

read -r -p "Application (default '$APPLICATION'): " user_application
read -r -p "Version (default '$VERSION'): " user_version

if [[ ! "$user_application" ]]; then
    user_application="$APPLICATION"
fi

if [[ ! "$user_version" ]]; then
    user_version="$VERSION"
fi

if [[ ! ("$user_version" && "$user_application") ]] ; then
    echo "Please specify an application name and version for deployment."
    exit 1
fi

echo "Deploying '$user_application' version '$user_version'."

npm run build
npm run uglify
appcfg.py --application "$user_application" --version "$user_version" $@ update .

popd
