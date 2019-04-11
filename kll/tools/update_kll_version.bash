#!/usr/bin/env bash
# Jacob Alexander 2019
# Simple script that updates the KLL = <version> to the version specified

# Example:
# update_kll_version.bash 0.5.7.8 <files>

if [ "$#" -lt 2 ]; then
	echo "Usage: $0 [version] [files..]"
	exit 1
fi

# Try gnu sed first (for macOS)
SED=gsed
which $SED &> /dev/null
if [ $? -eq 1 ]; then
	SED=sed
fi

version=$1
shift

# Iterate over files replacing KLL = <version> if found
for file in $@; do
	printf "${file} "
	grep '^KLL = .*;$' $file
	if [ $? -eq 0 ]; then
		$SED -i "s/^KLL = .*;$/KLL = ${version};/g" $file
	fi
done

