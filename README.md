![CI](https://github.com/Kupoman/prototype-mercury/workflows/CI/badge.svg)

![screenshot](images/screenshot.png)

# Mercury

An open-source monster raising and combat game

## Pre-built Binaries

Pre-built binaries are available [on Itch.io](https://mogurijin.itch.io/mercury).
To use these, download the appropriate version for your platform and extract the archive.
Then run the `mercury` binary (`mercury.exe` on Windows).

## Development

### Dependencies

* Python 3.7
* Python packages in `requirements.txt`
* Blender 2.8+ (preferably on the system PATH)

### Getting started

* Clone the repo
* Setup a virtual environment (optional, but recommended)
* Install dependencies: `pip install -r requirements.txt`
* Run the game: `pman run` or `python main.py`

## Configuration

Configuration is currently done by adding and modifying a `config/user.prc`.
This file is loaded after all over config so it will override the config in the other `config/*.prc` files.

## Using Pyenv

The current release of cefpython3 [dynamically links against libpython](https://github.com/cztomczak/cefpython/issues/554) on Linux. By default, [Pyenv does not build a shared library for Python](https://github.com/pyenv/pyenv/issues/65). So, in short, when present with this error message while using Pyenv:

```
Traceback (most recent call last):
  File "main.py", line 7, in <module>
    import cefpanda
  File ".../lib/python3.7/site-packages/cefpanda/__init__.py", line 8, in <module>
    from cefpython3 import cefpython
  File ".../lib/python3.7/site-packages/cefpython3/__init__.py", line 62, in <module>
    from . import cefpython_py37 as cefpython
ImportError: libpython3.7m.so.1.0: cannot open shared object file: No such file or directory
```
re-install Python 3.7 while telling Pyenv to build with shared libraris:
```bash
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.7.7
```

## License

* Anything mentioned in [CREDITS.md](CREDITS.md) have licenses as specified in the file
* Any remaining code is [Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)
* Any remaining assets are [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
