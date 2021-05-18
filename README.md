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
* Python3 (>=3.7) required for run
* testing:
  * pytest
  * tox
  * flake8

Tests
-----
Tests are defined in `tests` directory and are using pytest framework.
Tox is utilized for more flexible test execution.

To run tests you should run in project's root directory run following command:
```
tox -e py37
```

To run linter check, use following command:
```
tox -e lint
```

Developers specific notes
-------------------------
There are few in code unspoken weirdnesses across the code. This section should
explain why they are used and what they mean.

### `TURRISHW_FILE_ROOT` constant
All absolute paths should start with `TURRISHW_FILE_ROOT` constant. That is because of
tests. `TURRISHW_FILE_ROOT` defaults to "/", but it is changed during tests.
