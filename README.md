![Run tests](https://github.com/Kupoman/prototype-mercury/workflows/Run%20tests/badge.svg)

# Mercury

An open-source monster raising and combat game

## Dependencies

* Python packages in `requirements.txt`
* Blender 2.8+ (preferably on the system PATH)

## Getting started

* Clone the repo
* Setup a virtual environment (optional, but recommended)
* Install dependencies: `pip install -r requirements.txt`
* Run the game: `pman run` or `python main.py`

## Configuration

Configuration is currently done by adding and modifying a `config/user.prc`.
This file is loaded after all over config so it will override the config in the other `config/*.prc` files.
