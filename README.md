![CI](https://github.com/Kupoman/prototype-mercury/workflows/CI/badge.svg)

# Mercury

An open-source monster raising and combat game

## Dependencies

* Python 3.7
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

## License

* Anything mentioned in `credits.txt` have licenses as specified in the file
* Any remaining code is [Apache-2.0](https://choosealicense.com/licenses/apache-2.0/)
* Any remaining assets are [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
