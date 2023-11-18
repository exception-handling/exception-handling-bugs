An Empirical Study on Exception Handling Practices in Python Open-Source Projects
---
This repository includes the source code and data for our paper "An Empirical Study on Exception Handling Practices in Python Open-Source Projects".

## Requirements

- Python 3.6+

## Build
To reproduce the results, follow the instructions below.

1. Run `pip install -r requirements.txt` 
2. Run `python3 miner.py`  

## Unit tests
To run the unit tests, follow the instructions below.

1. Run `python3 -m unittest`

## Coverage report  
To generate the coverage report, follow the instructions below.

1. Run `coverage run -m unittest`
2. Run `coverage report --omit *test_*,*__init__*`
