# Common shell implementation of switch config
set -e

if [ "$1" == "list" ]; then
	if [ $# -eq 1 ]; then
		exit 1
	fi
	list
elif [ "$1" == "dev" ]; then
	if [ "$2" != "switch0" ]; then
		exit 1
	fi
	if [ "$3" == "show" ]; then
		show_all
	else
		if [ "$3" != "port" -o "$5" != "show" -o $# -ne 5 ]; then
			exit 1
		fi
		show_port "$4"
	fi
else
	exit 1
fi
