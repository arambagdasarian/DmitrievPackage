"""
Extract INTEGRUM Media Outlets from final_nodes_edges.csv

This script analyzes all media sources in the dataset and provides:
- Total number of articles per outlet
- Date range (first and last article dates)
- Year coverage for each outlet
- Total entity mentions per outlet
"""

import pandas as pd
import os
from datetime import datetime


def parse_date_flexible(date_str):
    """Parse dates with multiple format support"""
    if pd.isna(date_str):
        return pd.NaT
    
    date_str = str(date_str).strip()
    
    # Try different formats
    formats = [
        '%d.%m.%Y %H:%M',
        '%d.%m.%Y',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d/%m/%Y %H:%M'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return pd.NaT


def extract_media_outlets(input_file='data/periods/final_nodes_edges.csv', 
                          output_dir='final visuals'):
    """
    Extract all INTEGRUM media outlets with their statistics
    
    Parameters:
    -----------
    input_file : str
        Path to final_nodes_edges.csv
    output_dir : str
        Directory to save output files
    """
    
    print("=" * 80)
    print("INTEGRUM Media Outlets Extraction")
    print("=" * 80)
    
    # Load the dataset
    print(f"\nLoading {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df):,} rows")
    
    # Convert dates
    print("\nConverting dates (handling multiple formats)...")
    df['Date'] = df['Date'].apply(parse_date_flexible)
    df['Year'] = df['Date'].dt.year
    
    # Remove rows with invalid dates
    valid_dates = df['Date'].notna()
    print(f"Valid dates: {valid_dates.sum():,} out of {len(df):,} rows ({valid_dates.sum()/len(df)*100:.1f}%)")
    
    # Group by Source to get statistics
    print("\nAnalyzing media outlets...")
    source_data = []
    
    for source, group in df[valid_dates].groupby('Source'):
        # Get unique article IDs
        unique_articles = group['Article_ID'].nunique()
        
        # Get date range
        dates = group['Date'].dropna()
        if len(dates) > 0:
            min_date = dates.min()
            max_date = dates.max()
            min_year = int(min_date.year)
            max_year = int(max_date.year)
            year_range = f"{min_year}-{max_year}" if min_year != max_year else str(min_year)
            
            # Get all years (sorted)
            years = sorted(group['Year'].dropna().unique().astype(int).tolist())
            years_str = ', '.join(map(str, years))
            
            # Calculate total mentions
            total_mentions = len(group)
            
            source_data.append({
                'Media_Outlet': source,
                'Total_Articles': unique_articles,
                'First_Article_Date': min_date.strftime('%Y-%m-%d'),
                'Last_Article_Date': max_date.strftime('%Y-%m-%d'),
                'Year_Range': year_range,
                'Years': years_str,
                'Total_Mentions': total_mentions
            })
    
    # Create DataFrame and sort by number of articles
    df_outlets = pd.DataFrame(source_data)
    df_outlets = df_outlets.sort_values('Total_Articles', ascending=False)
    
    print(f"\nFound {len(df_outlets):,} unique media outlets")
    print(f"\nTop 10 outlets by article count:")
    print(df_outlets[['Media_Outlet', 'Total_Articles', 'Year_Range']].head(10).to_string(index=False))
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to CSV
    output_file_csv = os.path.join(output_dir, "integrum_media_outlets.csv")
    df_outlets.to_csv(output_file_csv, index=False, encoding='utf-8-sig')
    print(f"\n✓ Saved CSV to: {output_file_csv}")
    
    # Create a more readable text version
    output_file_txt = os.path.join(output_dir, "integrum_media_outlets.txt")
    with open(output_file_txt, 'w', encoding='utf-8') as f:
        f.write("INTEGRUM Media Outlets Dataset\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Total Media Outlets: {len(df_outlets):,}\n")
        f.write(f"Total Articles: {df_outlets['Total_Articles'].sum():,}\n")
        f.write(f"Total Entity Mentions: {df_outlets['Total_Mentions'].sum():,}\n\n")
        f.write("=" * 100 + "\n\n")
        
        for idx, row in df_outlets.iterrows():
            f.write(f"{idx + 1}. {row['Media_Outlet']}\n")
            f.write(f"   Articles: {row['Total_Articles']:,}\n")
            f.write(f"   Date Range: {row['First_Article_Date']} to {row['Last_Article_Date']}\n")
            f.write(f"   Years: {row['Year_Range']} ({row['Years']})\n")
            f.write(f"   Total Mentions: {row['Total_Mentions']:,}\n")
            f.write("\n")
    
    print(f"✓ Saved text version to: {output_file_txt}")
    
    # Create summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"Total Media Outlets: {len(df_outlets):,}")
    print(f"Total Articles: {df_outlets['Total_Articles'].sum():,}")
    print(f"Total Entity Mentions: {df_outlets['Total_Mentions'].sum():,}")
    
    # Year coverage statistics
    print(f"\nYear Coverage (number of outlets active per year):")
    year_counts = {}
    for years_str in df_outlets['Years']:
        for year in years_str.split(', '):
            try:
                year = int(year.strip())
                year_counts[year] = year_counts.get(year, 0) + 1
            except:
                continue
    
    for year in sorted(year_counts.keys()):
        print(f"  {year}: {year_counts[year]:,} outlets")
    
    print("\n" + "="*80)
    print("✓ Extraction complete!")
    print("="*80)
    
    return df_outlets


if __name__ == "__main__":
    df_outlets = extract_media_outlets()
    print(f"\nOutput files saved in 'final visuals' folder")
