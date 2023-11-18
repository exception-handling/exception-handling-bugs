Exception Handling Bugs in Python
---
This repository includes the source code and data for our paper "Slithering Through Exception Handling Bugs in Python:
Understanding Symptoms, Root Causes, Fixes and Anti-patterns".

## Datasets

#### Dataset with the bugs, root causes, fixes and anti-patterns:
`datasets\bugs\dataset_exception_bugs.csv`
#### Output of our parser tool across all projects:
`datasets\bugs\output_parser\`
#### Projects:
`projects_py.csv` 

## Requirements

- Python 3.6+

## Build
To reproduce the results from our parser, follow the instructions below.

1. Run `pip install -r requirements.txt` 
2. Run `python3 miner.py`  

## Unit tests
To run the unit tests, follow the instructions below.

1. Run `python3 -m unittest`

## Coverage report  
To generate the coverage report, follow the instructions below.

1. Run `coverage run -m unittest`
2. Run `coverage report --omit *test_*,*__init__*`
