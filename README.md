# Exception Handling Bugs in Python
---
This repository includes the source code and data for our paper "Exception Handling Bugs in Python: An Empirical Study of Root Causes, Fix Patterns, and Anti-Patterns".

## Datasets

#### Dataset with the bugs, root causes, fixes:
`dataset/bugs/dataset_exception_bugs.csv`

#### Dataset with the fixes and the respective anti-patterns:
`dataset/bugs/dataset_exception_fixes_anti_patterns.csv`

#### Output of our parser tool across all projects:
`dataset/output_parser/`

#### Projects:
`projects_py.csv`

### 2.1.1 Delta of Anti-Patterns in Fixes
Net change in anti-pattern occurrences between buggy and fixed versions:
`dataset/analysis/delta_ap_report.csv`

### 2.1.2 Exception Miner Validation
Positive and negative samples independently labelled by two authors to validate the Exception Miner tool:
`dataset/vals/miner_eh_mechanisms/`

### 2.1.3 EH Anti-Pattern Miner Validation
Positive and negative samples independently labelled by two authors to validate the EH Anti-Pattern Miner tool:
`dataset/vals/miner_eh_anti_patterns/`

### 2.1.4 Domain Analysis
Root cause counts per application domain, and the full bug dataset annotated with domain:
`dataset/analysis/domain_rootcause_counts.csv`
`dataset/bugs/dataset_exception_bugs_with_domain.csv`

### 2.1.5 Taxonomy Studies
Comparison of our EH bug taxonomy against prior studies:
`dataset/reports/eh_bug_taxonomy_comparison.xlsm`

### 2.1.6 Impact Analysis
Impact categories with descriptions, symptom mappings, top root causes, and real-world examples:
`dataset/analysis/impact_analysis_with_examples.csv`

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
