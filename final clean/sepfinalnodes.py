import pandas as pd

def split_dataset_by_periods(csv_file_path):
    # Load your nodes dataset
    df = pd.read_csv(csv_file_path)
    
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Define period boundaries
    periods = {
        'pre_crimea': (pd.to_datetime("2010-01-01"), pd.to_datetime("2013-10-31")),
        'post_crimea': (pd.to_datetime("2013-11-01"), pd.to_datetime("2019-12-31")),
        'covid': (pd.to_datetime("2020-01-01"), pd.to_datetime("2022-01-31")),
        'war': (pd.to_datetime("2022-02-01"), pd.to_datetime("2025-06-29"))
    }
    
    # Split and save each period
    for period_name, (start_date, end_date) in periods.items():
        period_data = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        period_data.to_csv(f"{period_name}.csv", index=False)
        print(f"{period_name}: {len(period_data)} nodes saved")

# Usage
split_dataset_by_periods("final_nodes.csv")
