# pmgc2v2
# Micro Data Cleaner

Micro Data Cleaner

Micro Data Cleaner is a lightweight Python utility designed to automatically analyze and clean CSV datasets. It identifies and reports common data quality issues such as missing values, duplicate rows, mixed data types, and statistical outliers. The script also generates a structured text-based analysis report and optionally produces a cleaned CSV file.

Key Features

Cross-platform file picker (supports Android, Linux, Windows)

Automatic detection of missing, duplicate, mixed-type, and outlier data

Intelligent CSV encoding fallback (utf-8 → latin-1)

Generates detailed terminal and text reports

Optional auto-cleaning with output CSV export

No external dependencies beyond pandas and numpy


Usage

python micro_data_cleaner.py

The script will:

1. Prompt to select or specify a .csv file.


2. Analyze the dataset and summarize its quality metrics.


3. Save a cleaned version of the data and a report file in the same directory.
