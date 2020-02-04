#!/bin/sh
set -ex

ADDR=
PTH=

while [ $# -gt 0 ]; do
	case "$1" in
		-h|--help)
			echo "Usage: $0 [OPTION].. ADDR PATH"
			echo "Clone relevant files and directories from router for testing."
			echo
			echo "ADDR:"
			echo "  Address of router (or SSH identifier)."
			echo "PATH:"
			echo "  Directory to copy root to."
			echo "Options:"
			echo "  -h, --help"
			echo "    Print this help text"
			exit 0
			;;
		*)
			if [ -z "$ADDR" ]; then
				ADDR="$1"
			elif [ -z "$PTH" ]; then
				PTH="$1"
			else
				echo "Unknown argument: $1"
				exit 1
			fi
			;;
	esac
	shift
done

mkdir -p "$PTH"

ssh $ADDR tar -czf sys.tar.gz /sys || true # This is expected to fail
scp $ADDR:sys.tar.gz ./
tar --delay-directory-restore -xzf sys.tar.gz -C "$PTH"
ssh $ADDR rm sys.tar.gz
rm sys.tar.gz
chmod -R +r "$PTH" # Make all files readable because otherwise it makes no sense to have them

mkdir -p "$PTH/proc"
ssh $ADDR cat /proc/meminfo > "$PTH/proc/meminfo"
