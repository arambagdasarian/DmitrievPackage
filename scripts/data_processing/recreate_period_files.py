"""
Recreate Period CSV Files with All Columns

Splits final_nodes_edges.csv into period-specific files with ALL columns included.
"""

import pandas as pd
from datetime import datetime


def parse_date_flexible(date_str):
    """Parse dates with multiple format support"""
    if pd.isna(date_str):
        return pd.NaT
    date_str = str(date_str).strip()
    formats = ['%d.%m.%Y %H:%M', '%d.%m.%Y', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%d/%m/%Y %H:%M']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return pd.NaT


def get_period(date):
    """Assign period based on date"""
    if pd.isna(date):
        return None
    if date < pd.to_datetime('2014-01-01'):
        return 'pre_crimea'
    elif date < pd.to_datetime('2017-02-01'):
        return 'post_crimea'
    elif date < pd.to_datetime('2022-02-24'):
        return 'covid'
    else:
        return 'war'


def recreate_period_files(input_file='data/periods/final_nodes_edges.csv'):
    """
    Recreate period CSV files with ALL columns from final_nodes_edges.csv
    
    Period definitions:
    - Pre-Crimea: 2010-01-01 to 2013-10-31
    - Post-Crimea: 2014-01-01 to 2017-01-31
    - COVID: 2020-01-01 to 2022-01-31
    - War: 2022-02-01 to 2025-06-29
    """
    
    print("="*70)
    print("RECREATING PERIOD CSV FILES WITH ALL COLUMNS")
    print("="*70)
    print(f"\nLoading {input_file}...")
    
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df):,} rows")
    print(f"Columns: {df.columns.tolist()}")
    
    # Parse dates and assign periods
    print("\nParsing dates and assigning periods...")
    df['Date_Parsed'] = df['Date'].apply(parse_date_flexible)
    df['Period'] = df['Date_Parsed'].apply(get_period)
    
    # Count valid dates
    valid_dates = df['Date_Parsed'].notna().sum()
    print(f"Valid dates: {valid_dates:,} ({valid_dates/len(df)*100:.1f}%)")
    
    # Filter for valid periods only
    df_valid = df[df['Period'].notna()].copy()
    print(f"Rows with valid periods: {len(df_valid):,}")
    
    # Drop the temporary Date_Parsed column
    df_valid = df_valid.drop('Date_Parsed', axis=1)
    
    # Split and save by period
    periods = {
        'pre_crimea': 'Pre-Crimea (2010-01-01 to 2013-10-31)',
        'post_crimea': 'Post-Crimea (2014-01-01 to 2017-01-31)',
        'covid': 'COVID (2020-01-01 to 2022-01-31)',
        'war': 'War (2022-02-01 to 2025-06-29)'
    }
    
    print("\n" + "="*70)
    print("SPLITTING DATA BY PERIOD")
    print("="*70)
    
    for period_key, period_name in periods.items():
        period_df = df_valid[df_valid['Period'] == period_key].copy()
        
        # Drop the Period column before saving
        period_df = period_df.drop('Period', axis=1)
        
        output_file = f'data/periods/{period_key}.csv'
        period_df.to_csv(output_file, index=False)
        
        print(f"\n{period_name}:")
        print(f"  Rows: {len(period_df):,}")
        print(f"  Columns: {len(period_df.columns)}")
        print(f"  Unique entities: {period_df['Entity'].nunique():,}")
        print(f"  Date range: {period_df['Date'].min()} to {period_df['Date'].max()}")
        print(f"  ✅ Saved: {output_file}")
    
    print("\n" + "="*70)
    print("✅ ALL PERIOD FILES RECREATED WITH ALL COLUMNS")
    print("="*70)
    
    # Verify columns in saved files
    print("\nVerifying saved files have all columns:")
    for period_key in periods.keys():
        df_check = pd.read_csv(f'data/periods/{period_key}.csv', nrows=1)
        print(f"  {period_key}.csv: {len(df_check.columns)} columns")
        # Check for key columns
        has_sector = 'Sector' in df_check.columns
        has_state_private = 'State/Private' in df_check.columns
        has_actor_type = 'Actor Type' in df_check.columns
        print(f"    Sector: {'✓' if has_sector else '✗'}, State/Private: {'✓' if has_state_private else '✗'}, Actor Type: {'✓' if has_actor_type else '✗'}")


if __name__ == "__main__":
    recreate_period_files()
