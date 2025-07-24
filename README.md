TurrisHW
========
This is Python library and program for detecting Turris router specific hardware
configuration. This detects only current hardware setup.

This library only maps hardware level of Turris router. To access additional
information about router you can use other Python libraries. These are suggested
libraries for specific use cases:
* Network: pyroute2

Dependencies
------------
* Python3 (>=3.10) required for run
* testing:
  * pytest
  * pre-commit
  * ruff

Tests
-----
Tests are defined in `tests` directory and are using pytest framework.
Tox is utilized for more flexible test execution.

To run tests you should run in project's root directory run following command:
```
pytest
```

To run linter check, use following command:
```
pre-commit run --hook-stage push --all-files
```

Developers specific notes
=========================
There are few in code unspoken weirdnesses across the code. This section should
explain why they are used and what they mean.

### `TURRISHW_FILE_ROOT` constant
All absolute paths should start with `TURRISHW_FILE_ROOT` constant. That is because of
tests. `TURRISHW_FILE_ROOT` defaults to "/", but it is changed during tests.

Add testing data router configurations
--------------------------------------

You may use [clone_root.sh](tests/test_roots/clone_root.sh) shell script in order to prepare testing data.

```console
$ ./clone_root.sh --help
Usage: ./clone_root.sh [OPTION].. ADDR PATH
Clone relevant files and directories from router for testing.

ADDR:
  Address of router (or SSH identifier).
PATH:
  Directory to copy root to.
Options:
  -h, --help
    Print this help text
```


The script copies `syspath` from your device and makes a local copy, so you may use it with tests for specific hardware configurations.

You may need to ``copy-ssh-id root@<your_router_IP>`` for script to work properly.

Do not forget to obsfucate real MAC addresses of your hardware and

```console
cd <direcotry_of_sys>
tar -czf ../<configuration_of_router>.tar.gz /sys /proc
cd ..
```

Add the configuration as parameter (without ext.) to the `test_get_interfaces` [test](tests/test_general.py)
