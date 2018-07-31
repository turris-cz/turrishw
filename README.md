TurrisHW
========
This is Python library and program for detecting Turris router specific hardware
configuration. This detects only current hardware setup.

Most of the library is written to be as general as possible but there are some
parts that are hard coded depending on board as there is no way to detect some
required informations.

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

### `_all` function/method
Every module in TurrisHW has `_all(res)` function. That is used for complete state
dumping. If complete state is requested (by calling `get_all()`) then this
function is called on every module (that has to be ensured in `__init__.py` that
is not automatic). This functions should iterate over its own definitions and set
them to `res` dictionary that is passed as argument.

If applicable also objects implement `_all` method which is used by that module
specific `_all` function. That is convention in TurrisHW code but its
implementation is not required in compare to `_all` function.

### Paths defined with `__P_` prefix
All absolute paths are defined in TurrisHW as module wide constants with prefix
`__P_`. That is because of tests. There should be no absolute path specified in
code without it being defined as module-wide variable with this prefix. Also there
should be no variable that is not absolute with with this prefix!
