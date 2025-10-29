import pandas as pd
import numpy as np
import os
import platform
from datetime import datetime

def pick_file():
    system = platform.system().lower()
    if "android" in system or "linux" in system:  # covers Pydroid/Jvdroid
        base_paths = ["/storage/emulated/0", "/sdcard", "/mnt/sdcard", os.getcwd()]
        csv_files = []
        for base in base_paths:
            for root, _, files in os.walk(base):
                for file in files:
                    if file.endswith(".csv"):
                        csv_files.append(os.path.join(root, file))
            if csv_files:
                break
        if not csv_files:
            print("No CSV files found in accessible storage.")
            exit()
        print("\nAvailable CSV files:\n")
        for i, f in enumerate(csv_files):
            print(f"[{i}] {f}")
        idx = int(input("\nSelect file index: ").strip())
        return csv_files[idx]
    else:
        file_path = input("Enter CSV file path (or drag file here): ").strip().replace('"','')
        return file_path

def analyze_file(file_path, autoclean=True):
    df = pd.read_csv(file_path)
    file_name = os.path.basename(file_path)
    file_size_kb = round(os.path.getsize(file_path) / 1024, 2)
    total_rows, total_cols = df.shape

    missing_cols = df.columns[df.isnull().any()].tolist()
    duplicate_rows = df[df.duplicated()]
    duplicate_indices = duplicate_rows.index.tolist()
    duplicate_count = len(duplicate_rows)

    mixed_types = {}
    for col in df.columns:
        types = df[col].map(type).nunique()
        if types > 1:
            mixed_types[col] = [t.__name__ for t in df[col].map(type).unique()]

    outlier_cols = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
        outliers = df[(df[col] < lower) | (df[col] > upper)][col]
        if not outliers.empty:
            outlier_cols[col] = len(outliers)

    unique_rows = len(df.drop_duplicates())
    worthy_ratio = round((unique_rows / total_rows) * 100, 2)

    cleaned_df = df.drop_duplicates().dropna()
    cleaned_file_name = f"{os.path.splitext(file_name)[0]}_cleaned.csv"
    if autoclean:
        cleaned_df.to_csv(cleaned_file_name, index=False)

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
        f"Outliers Detected          :  {outlier_cols if outlier_cols else 'None'}",
        "──────────────────────────────────────────────",
        "Effective Data (after cleaning) :",
        f"   Unique rows retained    :  {unique_rows}",
        f"   Worthy data ratio       :  {worthy_ratio} %",
        "──────────────────────────────────────────────",
        f"Report file saved as       :  {report_file}",
        f"Cleaned dataset saved as   :  {cleaned_file_name if autoclean else 'Skipped'}",
        "──────────────────────────────────────────────",
    ]

    with open(report_file, "w") as f:
        f.write("\n".join(report_lines))

    print("\n".join(report_lines))
    return report_file

if __name__ == "__main__":
    file_to_use = pick_file()
    analyze_file(file_to_use, autoclean=True)

