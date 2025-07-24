import pandas as pd
from datetime import datetime

# Load the dataset
df = pd.read_csv('matched_entities_filtered.csv')

print(f"Original dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"Sample dates: {df['Date'].head()}")

# Function to parse dates with multiple format attempts
def parse_date_flexible(date_str):
    """Parse date with multiple format attempts"""
    if pd.isna(date_str):
        return pd.NaT
    
    date_str = str(date_str).strip()
    
    # List of possible date formats to try
    formats = [
        '%d.%m.%Y %H:%M',      # 05.06.2021 18:22
        '%d.%m.%Y  %H:%M',     # 12.01.2018  16:57 (double space)
        '%d.%m.%Y',            # 05.06.2021
        '%Y-%m-%d %H:%M:%S',   # 2021-06-05 18:22:00
        '%Y-%m-%d %H:%M',      # 2021-06-05 18:22
        '%Y-%m-%d',            # 2021-06-05
        '%d/%m/%Y %H:%M',      # 05/06/2021 18:22
        '%d/%m/%Y',            # 05/06/2021
        '%d-%m-%Y %H:%M',      # 05-06-2021 18:22
        '%d-%m-%Y',            # 05-06-2021
    ]
    
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            continue
    
    # If all formats fail, try pandas' flexible parsing
    try:
        return pd.to_datetime(date_str, dayfirst=True)
    except:
        return pd.NaT

# Apply flexible date parsing
print("Parsing dates with flexible format detection...")
df['Date'] = df['Date'].apply(parse_date_flexible)

# Check parsing results
parsed_count = df['Date'].notna().sum()
failed_count = df['Date'].isna().sum()

print(f"Successfully parsed dates: {parsed_count:,} ({parsed_count/len(df)*100:.1f}%)")
print(f"Failed to parse dates: {failed_count:,} ({failed_count/len(df)*100:.1f}%)")

# If there are still parsing failures, investigate
if failed_count > 0:
    print("\nSample failed dates:")
    failed_dates = df[df['Date'].isna()]['Date'].head(10)
    for i, date in enumerate(failed_dates):
        print(f"  {i+1}: '{date}'")

# Define date ranges for each period
periods = {
    'Pre-Crimea': ('2010-01-01', '2013-10-31'),
    'Post-Crimea': ('2013-11-01', '2019-12-31'),
    'Covid': ('2020-01-01', '2022-01-31'),
    'War': ('2022-02-01', '2025-06-29')
}

# Create and save datasets for each period
total_distributed = 0
for period_name, (start_date, end_date) in periods.items():
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # Filter data for the current period (only include rows with valid dates)
    period_df = df[(df['Date'] >= start_dt) & (df['Date'] <= end_dt) & df['Date'].notna()].copy()
    
    # Save to CSV
    output_filename = f'matched_entities_{period_name.lower().replace("-", "_").replace("/", "_")}.csv'
    period_df.to_csv(output_filename, index=False)
    
    print(f"\n{period_name}: {len(period_df):,} rows ({start_date} to {end_date})")
    print(f"  Saved to: {output_filename}")
    
    # Show date range in the filtered data
    if len(period_df) > 0:
        print(f"  Actual date range: {period_df['Date'].min()} to {period_df['Date'].max()}")
    else:
        print("  No data in this period")
    
    total_distributed += len(period_df)

# Handle rows with unparseable dates separately
unparseable_df = df[df['Date'].isna()].copy()
if len(unparseable_df) > 0:
    unparseable_df.to_csv('matched_entities_unparseable_dates.csv', index=False)
    print(f"\nUnparseable dates: {len(unparseable_df):,} rows")
    print("  Saved to: matched_entities_unparseable_dates.csv")

# Summary statistics
print("\n=== SUMMARY ===")
print(f"Total original rows: {len(df):,}")
print(f"Rows with valid dates: {parsed_count:,}")
print(f"Rows distributed to periods: {total_distributed:,}")
print(f"Rows with unparseable dates: {failed_count:,}")
print(f"Date range in dataset: {df['Date'].min()} to {df['Date'].max()}")

# Show distribution across periods
print(f"\nDistribution across periods:")
for period_name, (start_date, end_date) in periods.items():
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    count = len(df[(df['Date'] >= start_dt) & (df['Date'] <= end_dt) & df['Date'].notna()])
    print(f"{period_name}: {count:,} rows ({count/len(df)*100:.1f}%)")

print(f"\nTotal accounted for: {total_distributed + failed_count:,} rows")
