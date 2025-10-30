import pandas as pd
import numpy as np
import os
import platform
from datetime import datetime
from pathlib import Path

def pick_file():
    """Select CSV file based on platform."""
    system = platform.system().lower()
    
    if "android" in system or "linux" in system:
        base_paths = ["/storage/emulated/0", "/sdcard", "/mnt/sdcard", os.getcwd()]
        csv_files = []
        
        for base in base_paths:
            if not os.path.exists(base):
                continue
            try:
                for root, _, files in os.walk(base):
                    for file in files:
                        if file.lower().endswith(".csv"):
                            csv_files.append(os.path.join(root, file))
                if csv_files:
                    break
            except (PermissionError, OSError) as e:
                print(f"Warning: Cannot access {base}: {e}")
                continue
        
        if not csv_files:
            print("No CSV files found in accessible storage.")
            return None
        
        print("\nAvailable CSV files:\n")
        for i, f in enumerate(csv_files):
            print(f"[{i}] {f}")
        
        while True:
            try:
                idx = int(input("\nSelect file index: ").strip())
                if 0 <= idx < len(csv_files):
                    return csv_files[idx]
                print(f"Please enter a number between 0 and {len(csv_files) - 1}")
            except (ValueError, KeyboardInterrupt):
                print("\nInvalid input. Please enter a valid number.")
                return None
    else:
        file_path = input("Enter CSV file path (or drag file here): ").strip().replace('"', '').replace("'", '')
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return None
        return file_path

def analyze_file(file_path, autoclean=True, output_dir=None):
    """Analyze CSV file for data quality issues and optionally clean it."""
    
    if not file_path or not os.path.exists(file_path):
        print(f"Error: Invalid file path: {file_path}")
        return None
    
    try:
        # Read CSV with error handling
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='latin-1')
            print("Warning: File read using latin-1 encoding")
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return None
    except pd.errors.EmptyDataError:
        print("Error: CSV file is empty")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None
    
    # Basic file info
    file_name = os.path.basename(file_path)
    file_size_kb = round(os.path.getsize(file_path) / 1024, 2)
    total_rows, total_cols = df.shape
    
    if total_rows == 0:
        print("Error: CSV file contains no data rows")
        return None
    
    # Missing values analysis
    missing_cols = df.columns[df.isnull().any()].tolist()
    missing_counts = {col: df[col].isnull().sum() for col in missing_cols}
    
    # Duplicate analysis
    duplicate_mask = df.duplicated()
    duplicate_rows = df[duplicate_mask]
    duplicate_indices = duplicate_rows.index.tolist()
    duplicate_count = len(duplicate_rows)
    
    # Mixed data types detection
    mixed_types = {}
    for col in df.columns:
        non_null = df[col].dropna()
        if len(non_null) > 0:
            types = non_null.map(type).unique()
            if len(types) > 1:
                mixed_types[col] = [t.__name__ for t in types]
    
    # Outlier detection
    outlier_cols = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        non_null = df[col].dropna()
        if len(non_null) > 0:
            Q1 = non_null.quantile(0.25)
            Q3 = non_null.quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:  # Avoid division issues
                lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
                outliers = df[(df[col] < lower) | (df[col] > upper)][col]
                if not outliers.empty:
                    outlier_cols[col] = len(outliers)
    
    # Data quality metrics
    unique_rows = len(df.drop_duplicates())
    worthy_ratio = round((unique_rows / total_rows) * 100, 2) if total_rows > 0 else 0
    
    # Clean data
    cleaned_df = df.drop_duplicates().dropna()
    cleaned_rows = len(cleaned_df)
    
    # Set output directory
    if output_dir is None:
        output_dir = os.path.dirname(file_path) or os.getcwd()
    
    # Save cleaned file
    base_name = Path(file_name).stem
    cleaned_file_name = f"{base_name}_cleaned.csv"
    cleaned_file_path = os.path.join(output_dir, cleaned_file_name)
    
    if autoclean and cleaned_rows > 0:
        try:
            cleaned_df.to_csv(cleaned_file_path, index=False)
        except Exception as e:
            print(f"Warning: Could not save cleaned file: {e}")
            cleaned_file_path = "Not saved (error occurred)"
    elif cleaned_rows == 0:
        cleaned_file_path = "Not saved (no data after cleaning)"
    else:
        cleaned_file_path = "Skipped"
    
    # Generate report
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"clean_report_{base_name}_{timestamp}.txt"
    report_path = os.path.join(output_dir, report_file)
    
    # Format missing values info
    missing_info = "None"
    if missing_cols:
        missing_info = f"{len(missing_cols)} columns\n"
        for col in missing_cols[:5]:  # Show first 5
            missing_info += f"      → {col}: {missing_counts[col]} missing\n"
        if len(missing_cols) > 5:
            missing_info += f"      ... and {len(missing_cols) - 5} more"
        missing_info = missing_info.rstrip('\n')
    
    # Format duplicate info
    dup_info = f"{duplicate_count} rows"
    if duplicate_count > 0:
        dup_indices_str = str(duplicate_indices[:10])[1:-1]  # Remove brackets
        if duplicate_count > 10:
            dup_info += f" (indices: {dup_indices_str}...)"
        else:
            dup_info += f" (indices: {dup_indices_str})"
    
    # Format mixed types info
    mixed_info = "None"
    if mixed_types:
        mixed_info = "\n"
        for col, types in list(mixed_types.items())[:5]:
            mixed_info += f"      → {col}: {types}\n"
        if len(mixed_types) > 5:
            mixed_info += f"      ... and {len(mixed_types) - 5} more"
        mixed_info = mixed_info.rstrip('\n')
    
    # Format outliers info
    outlier_info = "None"
    if outlier_cols:
        outlier_info = "\n"
        for col, count in list(outlier_cols.items())[:5]:
            outlier_info += f"      → {col}: {count} outliers\n"
        if len(outlier_cols) > 5:
            outlier_info += f"      ... and {len(outlier_cols) - 5} more"
        outlier_info = outlier_info.rstrip('\n')
    
    report_lines = [
        "──────────────────────────────────────────────",
        "   MICRO DATA CLEANER – ANALYSIS REPORT",
        "──────────────────────────────────────────────",
        f"File scanned              :  {file_name}",
        f"File size (KB)            :  {file_size_kb}",
        f"Total rows                :  {total_rows}",
        f"Total columns             :  {total_cols}",
        "──────────────────────────────────────────────",
        f"Missing Values            :  {missing_info}",
        f"Duplicate Entries         :  {dup_info}",
        f"Mixed Data Types          :  {mixed_info}",
        f"Outliers Detected         :  {outlier_info}",
        "──────────────────────────────────────────────",
        "Effective Data (after cleaning):",
        f"   Unique rows retained   :  {unique_rows}",
        f"   Rows after cleaning    :  {cleaned_rows}",
        f"   Worthy data ratio      :  {worthy_ratio}%",
        "──────────────────────────────────────────────",
        f"Report saved as           :  {report_path}",
        f"Cleaned dataset           :  {cleaned_file_path}",
        "──────────────────────────────────────────────",
    ]
    
    # Save report
    try:
        with open(report_path, "w", encoding='utf-8') as f:
            f.write("\n".join(report_lines))
    except Exception as e:
        print(f"Warning: Could not save report file: {e}")
    
    print("\n".join(report_lines))
    return report_path

if __name__ == "__main__":
    try:
        file_to_use = pick_file()
        if file_to_use:
            analyze_file(file_to_use, autoclean=True)
        else:
            print("No file selected. Exiting.")
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()import pandas as pd
import numpy as np
import os
import platform
from datetime import datetime
from pathlib import Path

def pick_file():
    """Select CSV file based on platform."""
    system = platform.system().lower()
    
    if "android" in system or "linux" in system:
        base_paths = ["/storage/emulated/0", "/sdcard", "/mnt/sdcard", os.getcwd()]
        csv_files = []
        
        for base in base_paths:
            if not os.path.exists(base):
                continue
            try:
                for root, _, files in os.walk(base):
                    for file in files:
                        if file.lower().endswith(".csv"):
                            csv_files.append(os.path.join(root, file))
                if csv_files:
                    break
            except (PermissionError, OSError) as e:
                print(f"Warning: Cannot access {base}: {e}")
                continue
        
        if not csv_files:
            print("No CSV files found in accessible storage.")
            return None
        
        print("\nAvailable CSV files:\n")
        for i, f in enumerate(csv_files):
            print(f"[{i}] {f}")
        
        while True:
            try:
                idx = int(input("\nSelect file index: ").strip())
                if 0 <= idx < len(csv_files):
                    return csv_files[idx]
                print(f"Please enter a number between 0 and {len(csv_files) - 1}")
            except (ValueError, KeyboardInterrupt):
                print("\nInvalid input. Please enter a valid number.")
                return None
    else:
        file_path = input("Enter CSV file path (or drag file here): ").strip().replace('"', '').replace("'", '')
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return None
        return file_path

def analyze_file(file_path, autoclean=True, output_dir=None):
    """Analyze CSV file for data quality issues and optionally clean it."""
    
    if not file_path or not os.path.exists(file_path):
        print(f"Error: Invalid file path: {file_path}")
        return None
    
    try:
        # Read CSV with error handling
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='latin-1')
            print("Warning: File read using latin-1 encoding")
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return None
    except pd.errors.EmptyDataError:
        print("Error: CSV file is empty")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None
    
    # Basic file info
    file_name = os.path.basename(file_path)
    file_size_kb = round(os.path.getsize(file_path) / 1024, 2)
    total_rows, total_cols = df.shape
    
    if total_rows == 0:
        print("Error: CSV file contains no data rows")
        return None
    
    # Missing values analysis
    missing_cols = df.columns[df.isnull().any()].tolist()
    missing_counts = {col: df[col].isnull().sum() for col in missing_cols}
    
    # Duplicate analysis
    duplicate_mask = df.duplicated()
    duplicate_rows = df[duplicate_mask]
    duplicate_indices = duplicate_rows.index.tolist()
    duplicate_count = len(duplicate_rows)
    
    # Mixed data types detection
    mixed_types = {}
    for col in df.columns:
        non_null = df[col].dropna()
        if len(non_null) > 0:
            types = non_null.map(type).unique()
            if len(types) > 1:
                mixed_types[col] = [t.__name__ for t in types]
    
    # Outlier detection
    outlier_cols = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        non_null = df[col].dropna()
        if len(non_null) > 0:
            Q1 = non_null.quantile(0.25)
            Q3 = non_null.quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:  # Avoid division issues
                lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
                outliers = df[(df[col] < lower) | (df[col] > upper)][col]
                if not outliers.empty:
                    outlier_cols[col] = len(outliers)
    
    # Data quality metrics
    unique_rows = len(df.drop_duplicates())
    worthy_ratio = round((unique_rows / total_rows) * 100, 2) if total_rows > 0 else 0
    
    # Clean data
    cleaned_df = df.drop_duplicates().dropna()
    cleaned_rows = len(cleaned_df)
    
    # Set output directory
    if output_dir is None:
        output_dir = os.path.dirname(file_path) or os.getcwd()
    
    # Save cleaned file
    base_name = Path(file_name).stem
    cleaned_file_name = f"{base_name}_cleaned.csv"
    cleaned_file_path = os.path.join(output_dir, cleaned_file_name)
    
    if autoclean and cleaned_rows > 0:
        try:
            cleaned_df.to_csv(cleaned_file_path, index=False)
        except Exception as e:
            print(f"Warning: Could not save cleaned file: {e}")
            cleaned_file_path = "Not saved (error occurred)"
    elif cleaned_rows == 0:
        cleaned_file_path = "Not saved (no data after cleaning)"
    else:
        cleaned_file_path = "Skipped"
    
    # Generate report
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"clean_report_{base_name}_{timestamp}.txt"
    report_path = os.path.join(output_dir, report_file)
    
    # Format missing values info
    missing_info = "None"
    if missing_cols:
        missing_info = f"{len(missing_cols)} columns\n"
        for col in missing_cols[:5]:  # Show first 5
            missing_info += f"      → {col}: {missing_counts[col]} missing\n"
        if len(missing_cols) > 5:
            missing_info += f"      ... and {len(missing_cols) - 5} more"
        missing_info = missing_info.rstrip('\n')
    
    # Format duplicate info
    dup_info = f"{duplicate_count} rows"
    if duplicate_count > 0:
        dup_indices_str = str(duplicate_indices[:10])[1:-1]  # Remove brackets
        if duplicate_count > 10:
            dup_info += f" (indices: {dup_indices_str}...)"
        else:
            dup_info += f" (indices: {dup_indices_str})"
    
    # Format mixed types info
    mixed_info = "None"
    if mixed_types:
        mixed_info = "\n"
        for col, types in list(mixed_types.items())[:5]:
            mixed_info += f"      → {col}: {types}\n"
        if len(mixed_types) > 5:
            mixed_info += f"      ... and {len(mixed_types) - 5} more"
        mixed_info = mixed_info.rstrip('\n')
    
    # Format outliers info
    outlier_info = "None"
    if outlier_cols:
        outlier_info = "\n"
        for col, count in list(outlier_cols.items())[:5]:
            outlier_info += f"      → {col}: {count} outliers\n"
        if len(outlier_cols) > 5:
            outlier_info += f"      ... and {len(outlier_cols) - 5} more"
        outlier_info = outlier_info.rstrip('\n')
    
    report_lines = [
        "──────────────────────────────────────────────",
        "   MICRO DATA CLEANER – ANALYSIS REPORT",
        "──────────────────────────────────────────────",
        f"File scanned              :  {file_name}",
        f"File size (KB)            :  {file_size_kb}",
        f"Total rows                :  {total_rows}",
        f"Total columns             :  {total_cols}",
        "──────────────────────────────────────────────",
        f"Missing Values            :  {missing_info}",
        f"Duplicate Entries         :  {dup_info}",
        f"Mixed Data Types          :  {mixed_info}",
        f"Outliers Detected         :  {outlier_info}",
        "──────────────────────────────────────────────",
        "Effective Data (after cleaning):",
        f"   Unique rows retained   :  {unique_rows}",
        f"   Rows after cleaning    :  {cleaned_rows}",
        f"   Worthy data ratio      :  {worthy_ratio}%",
        "──────────────────────────────────────────────",
        f"Report saved as           :  {report_path}",
        f"Cleaned dataset           :  {cleaned_file_path}",
        "──────────────────────────────────────────────",
    ]
    
    # Save report
    try:
        with open(report_path, "w", encoding='utf-8') as f:
            f.write("\n".join(report_lines))
    except Exception as e:
        print(f"Warning: Could not save report file: {e}")
    
    print("\n".join(report_lines))
    return report_path

if __name__ == "__main__":
    try:
        file_to_use = pick_file()
        if file_to_use:
            analyze_file(file_to_use, autoclean=True)
        else:
            print("No file selected. Exiting.")
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()    return report_file

if __name__ == "__main__":
    file_to_use = pick_file()
    analyze_file(file_to_use, autoclean=True)

