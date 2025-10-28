import pandas as pd
import numpy as np
import os
from datetime import datetime

def analyze_file(file_path, autoclean=True):
    # Load dataset
    df = pd.read_csv(file_path)
    file_name = os.path.basename(file_path)
    file_size_kb = round(os.path.getsize(file_path) / 1024, 2)

    total_rows, total_cols = df.shape

    # Detect missing values
    missing_cols = df.columns[df.isnull().any()].tolist()

    # Detect duplicates
    duplicate_rows = df[df.duplicated()]
    duplicate_indices = duplicate_rows.index.tolist()
    duplicate_count = len(duplicate_rows)

    # Detect mixed data types
    mixed_types = {}
    for col in df.columns:
        types = df[col].map(type).nunique()
        if types > 1:
            mixed_types[col] = df[col].map(type).unique()

    # Detect outliers (IQR method)
    outlier_cols = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
        if not outliers.empty:
            outlier_cols[col] = len(outliers)

    # Compute worthy data ratio
    unique_rows = len(df.drop_duplicates())
    worthy_ratio = round((unique_rows / total_rows) * 100, 2)

    # Auto-clean (optional)
    cleaned_df = df.drop_duplicates()
    cleaned_df = cleaned_df.dropna()
    cleaned_file_name = f"{os.path.splitext(file_name)[0]}_cleaned.csv"
    if autoclean:
        cleaned_df.to_csv(cleaned_file_name, index=False)

    # Report generation
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"clean_report_{os.path.splitext(file_name)[0]}_{timestamp}.txt"

    report_lines = [
        "──────────────────────────────────────────────",
        "   MICRO DATA CLEANER – ANALYSIS REPORT",
        "──────────────────────────────────────────────",
        f"File scanned              :  {file_name}",
        f"File size (KB)            :  {file_size_kb}",
        f"Total rows                :  {total_rows}",
        f"Total columns             :  {total_cols}",
        "──────────────────────────────────────────────",
        f"Missing Values            :  {len(missing_cols)} columns → {missing_cols if missing_cols else 'None'}",
        f"Duplicate Entries          :  {duplicate_count} rows found at indices {duplicate_indices[:10]}{'...' if duplicate_count > 10 else ''}",
        f"Mixed Data Types           :  {mixed_types if mixed_types else 'None'}",
        f"Outliers Detected          :  { {k:v for k,v in outlier_cols.items()} if outlier_cols else 'None'}",
        "──────────────────────────────────────────────",
        "Effective Data (after cleaning) :",
        f"   Unique rows retained    :  {unique_rows}",
        f"   Worthy data ratio       :  {worthy_ratio} %",
        "──────────────────────────────────────────────",
        f"Report file saved as       :  {report_file}",
        f"Cleaned dataset saved as   :  {cleaned_file_name if autoclean else 'Skipped'}",
        "──────────────────────────────────────────────",
    ]

    # Save report
    with open(report_file, "w") as f:
        f.write("\n".join(report_lines))

    # Print report
    print("\n".join(report_lines))
    return report_file

# Example direct run
if __name__ == "__main__":
    input_file = input("Enter path of CSV file: ").strip()
    analyze_file(input_file, autoclean=True)
