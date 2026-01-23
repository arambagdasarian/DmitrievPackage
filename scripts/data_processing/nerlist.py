import pandas as pd
import numpy as np

def compare_and_filter_entities(csv_file, xlsx_file, output_matched_file, output_unmatched_file):
    """
    Compare entities between CSV and Excel files, create filtered datasets
    """
    
    print("Loading datasets...")
    
    # Load the CSV file
    try:
        df_csv = pd.read_csv(csv_file)
        print(f"Loaded CSV file: {len(df_csv):,} rows")
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return
    
    # Load the Excel file
    try:
        df_xlsx = pd.read_excel(xlsx_file)
        print(f"Loaded Excel file: {len(df_xlsx):,} rows")
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return
    
    # Check if 'Entity' column exists in both files
    if 'Entity' not in df_csv.columns:
        print("Error: 'Entity' column not found in CSV file")
        return
    
    if 'Entity' not in df_xlsx.columns:
        print("Error: 'Entity' column not found in Excel file")
        return
    
    # Get unique entities from both datasets
    csv_entities = set(df_csv['Entity'].dropna().unique())
    xlsx_entities = set(df_xlsx['Entity'].dropna().unique())
    
    print(f"Unique entities in CSV: {len(csv_entities):,}")
    print(f"Unique entities in Excel: {len(xlsx_entities):,}")
    
    # Find matching entities
    matched_entities = csv_entities.intersection(xlsx_entities)
    print(f"Matching entities: {len(matched_entities):,}")
    
    # Find unmatched entities from Excel file
    unmatched_entities = xlsx_entities - csv_entities
    print(f"Unmatched entities from Excel: {len(unmatched_entities):,}")
    
    # Filter CSV data to include only matching entities
    df_matched = df_csv[df_csv['Entity'].isin(matched_entities)].copy()
    
    # Create DataFrame for unmatched entities from Excel
    df_unmatched = df_xlsx[df_xlsx['Entity'].isin(unmatched_entities)].copy()
    
    # Save filtered datasets
    print(f"\nSaving matched entities to {output_matched_file}...")
    df_matched.to_csv(output_matched_file, index=False)
    
    print(f"Saving unmatched entities to {output_unmatched_file}...")
    df_unmatched.to_csv(output_unmatched_file, index=False)
    
    # Print summary statistics
    print(f"\n=== COMPARISON SUMMARY ===")
    print(f"Original CSV rows: {len(df_csv):,}")
    print(f"Matched entities CSV rows: {len(df_matched):,}")
    print(f"Reduction: {((len(df_csv) - len(df_matched)) / len(df_csv) * 100):.1f}%")
    
    print(f"\nOriginal Excel rows: {len(df_xlsx):,}")
    print(f"Unmatched entities Excel rows: {len(df_unmatched):,}")
    
    # Show examples of matched entities
    if len(matched_entities) > 0:
        print(f"\nTop 10 matched entities:")
        if 'Occurrences' in df_matched.columns:
            top_matched = df_matched.groupby('Entity')['Occurrences'].first().sort_values(ascending=False).head(10)
            for entity, count in top_matched.items():
                print(f"  {entity}: {count:,} occurrences")
        else:
            sample_matched = list(matched_entities)[:10]
            for entity in sample_matched:
                print(f"  {entity}")
    
    # Show examples of unmatched entities
    if len(unmatched_entities) > 0:
        print(f"\nTop 10 unmatched entities from Excel:")
        sample_unmatched = list(unmatched_entities)[:10]
        for entity in sample_unmatched:
            print(f"  {entity}")
    
    return df_matched, df_unmatched

# Run the comparison
if __name__ == "__main__":
    # File paths
    csv_file = 'ner_entity_dataset_superclean.csv'
    xlsx_file = 'merged_dataset.xlsx'
    output_matched_file = 'matched_entities_filtered.csv'
    output_unmatched_file = 'unmatched_entities_from_excel.csv'
    
    # Perform comparison and filtering
    matched_df, unmatched_df = compare_and_filter_entities(
        csv_file, 
        xlsx_file, 
        output_matched_file, 
        output_unmatched_file
    )
    
    print(f"\nProcess completed successfully!")
    print(f"Matched entities saved to: {output_matched_file}")
    print(f"Unmatched entities saved to: {output_unmatched_file}")
