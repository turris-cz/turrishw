# Common shell implementation of switch config
set -e

if [ "$1" = "list" ]; then
	[ $# -eq 1 ]
	list
elif [ "$1" = "dev" ]; then
	[ "$2" = "switch0" ]
	if [ "$3" = "show" ]; then
		show_all
	else
		[ "$3" = "port" -a "$5" = "show" -a $# -eq 5 ]
		show_port "$4"
	fi
else
	exit 1
fi
