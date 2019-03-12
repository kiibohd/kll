#!/usr/bin/env bash
# Jacob Alexander 2019
# Simple script that updates the KLL = <version> to the version specified

# Example:
# update_kll_version.bash 0.5.7.8 <files>

if [ "$#" -lt 2 ]; then
	echo "Usage: $0 [version] [files..]"
	exit 1
fi

version=$1
shift

# Iterate over files replacing KLL = <version> if found
for file in $@; do
	printf "${file} "
	grep '^KLL = .*;$' $file
	if [ $? -eq 0 ]; then
		sed -i "s/^KLL = .*;$/KLL = ${version};/g" $file
	fi
done

