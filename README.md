# Project Repository
Link: [https://github.com/Yash-More1224/2024114004](https://github.com/Yash-More1224/2024114004)

## How to run the code

From the project root, run:

- **Whitebox code:**
  `python whitebox/code/main.py`

- **Integration CLI:**
  `python integration/code/main.py`


## How to run the tests

From the project root, run:

- **Whitebox tests:**
  `python -m pytest whitebox/tests/ -v`

- **Integration tests:**
  `python -m pytest integration/tests/ -v`

## Static analysis (Whitebox)

From the project root, run:

- `pylint whitebox/code/moneypoly`

## Blackbox API container setup

Before running blackbox tests, from the project root run:

- `docker load -i blackbox/quickcart_image_x86.tar`
- `docker run -d --name quickcart -p 8080:8080 quickcart` (creates a new container)
- if you already have the container, just run: `docker start quickcart`
- **Blackbox tests:**
  `python -m pytest blackbox/tests/test_quickcart.py -q`
