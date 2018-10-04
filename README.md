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
* Python2 or Python3 required for run
* pytest for testing

Tests
-----
Tests are defined in `tests` directory and are using pytest framework.

To run tests you should run in project's root directory run following command:
```
python -m pytest tests
```

Developers specific notes
-------------------------
There are few in code unspoken weirdnesses across the code. This section should
explain why they are used and what they mean.

### `__P_ROOT__` constant
All absolute paths should start with `__P_ROOT__` constant. That is because of
tests. `__P_ROOT__` defaults to "/", but it is changed during tests.
