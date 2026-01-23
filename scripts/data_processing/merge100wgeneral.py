import pandas as pd
from datetime import datetime

def merge_entity_datasets():
    """
    Add data from ner_entity_dataset_TOP_100.csv to ner_entity_dataset_superclean.csv
    and save the combined result to ner_entity_dataset_superclean.csv
    """
    
    print("🔄 MERGING ENTITY DATASETS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Define file paths
    main_file = 'ner_entity_dataset_superclean.csv'
    additional_file = 'ner_entity_dataset_TOP_100.csv'
    
    try:
        # Load the main dataset
        print(f"📂 Loading main dataset: {main_file}")
        df_main = pd.read_csv(main_file)
        print(f"✓ Loaded {main_file}: {len(df_main):,} rows, {df_main['Entity'].nunique()} unique entities")
        print(f"   Columns: {list(df_main.columns)}")
        
        # Load the additional dataset
        print(f"\n📂 Loading additional dataset: {additional_file}")
        df_additional = pd.read_csv(additional_file)
        print(f"✓ Loaded {additional_file}: {len(df_additional):,} rows, {df_additional['Entity'].nunique()} unique entities")
        print(f"   Columns: {list(df_additional.columns)}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading files: {e}")
        return None
    
    # Verify that columns match
    if list(df_main.columns) != list(df_additional.columns):
        print("⚠️  WARNING: Column structures don't match exactly")
        print(f"   Main file columns: {list(df_main.columns)}")
        print(f"   Additional file columns: {list(df_additional.columns)}")
        
        # Find common columns
        common_columns = list(set(df_main.columns) & set(df_additional.columns))
        print(f"   Common columns: {common_columns}")
        
        if not common_columns:
            print("❌ Error: No common columns found")
            return None
        
        # Use only common columns
        df_main = df_main[common_columns]
        df_additional = df_additional[common_columns]
        print(f"✓ Proceeding with common columns only")
    
    # Show overlap analysis before merging
    print(f"\n📊 OVERLAP ANALYSIS:")
    main_entities = set(df_main['Entity'].unique())
    additional_entities = set(df_additional['Entity'].unique())
    
    overlap_entities = main_entities & additional_entities
    new_entities = additional_entities - main_entities
    
    print(f"   Entities in main dataset: {len(main_entities)}")
    print(f"   Entities in additional dataset: {len(additional_entities)}")
    print(f"   Overlapping entities: {len(overlap_entities)}")
    print(f"   New entities from additional dataset: {len(new_entities)}")
    
    if overlap_entities:
        print(f"\n🔍 TOP 10 OVERLAPPING ENTITIES:")
        # Count mentions for overlapping entities
        overlap_counts = df_additional[df_additional['Entity'].isin(overlap_entities)]['Entity'].value_counts().head(10)
        for i, (entity, count) in enumerate(overlap_counts.items(), 1):
            print(f"   {i:>2}. {entity}: +{count} new mentions")
    
    if new_entities:
        print(f"\n🆕 SAMPLE NEW ENTITIES (up to 10):")
        for i, entity in enumerate(list(new_entities)[:10], 1):
            count = len(df_additional[df_additional['Entity'] == entity])
            print(f"   {i:>2}. {entity}: {count} mentions")
        if len(new_entities) > 10:
            print(f"   ... and {len(new_entities) - 10} more new entities")
    
    # Combine the datasets
    print(f"\n🔗 COMBINING DATASETS:")
    df_combined = pd.concat([df_main, df_additional], ignore_index=True)
    print(f"✓ Combined dataset created: {len(df_combined):,} rows")
    
    # Remove exact duplicates if any
    initial_rows = len(df_combined)
    df_combined = df_combined.drop_duplicates()
    duplicates_removed = initial_rows - len(df_combined)
    
    if duplicates_removed > 0:
        print(f"✓ Removed {duplicates_removed:,} exact duplicate rows")
    else:
        print(f"✓ No exact duplicates found")
    
    # Sort the combined dataset for better organization
    if 'Date' in df_combined.columns:
        df_combined = df_combined.sort_values(['Entity', 'Date'], na_position='last')
    else:
        df_combined = df_combined.sort_values('Entity')
    
    # Save the combined dataset
    try:
        print(f"\n💾 SAVING COMBINED DATASET:")
        df_combined.to_csv(main_file, index=False)
        print(f"✓ Successfully saved to: {main_file}")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return None
    
    # Final statistics
    print(f"\n{'='*60}")
    print(f"MERGE OPERATION SUMMARY")
    print(f"{'='*60}")
    print(f"📈 FINAL STATISTICS:")
    print(f"   Total rows: {len(df_combined):,}")
    print(f"   Unique entities: {df_combined['Entity'].nunique()}")
    print(f"   Rows added: {len(df_additional):,}")
    print(f"   New entities added: {len(new_entities)}")
    print(f"   Additional mentions for existing entities: {len(df_additional[df_additional['Entity'].isin(overlap_entities)])}")
    
    # Show top entities in final dataset
    print(f"\n📊 TOP 10 ENTITIES IN MERGED DATASET:")
    top_entities = df_combined['Entity'].value_counts().head(10)
    for i, (entity, count) in enumerate(top_entities.items(), 1):
        print(f"   {i:>2}. {entity}: {count} mentions")
    
    # Show data sources if available
    if 'Source' in df_combined.columns:
        print(f"\n📰 TOP SOURCES IN MERGED DATASET:")
        top_sources = df_combined['Source'].value_counts().head(5)
        for source, count in top_sources.items():
            print(f"   {source}: {count} mentions")
    
    # Show date range if available
    if 'Date' in df_combined.columns:
        try:
            df_combined['Date'] = pd.to_datetime(df_combined['Date'], errors='coerce')
            valid_dates = df_combined['Date'].dropna()
            if len(valid_dates) > 0:
                print(f"\n📅 DATE RANGE:")
                print(f"   Earliest: {valid_dates.min().strftime('%Y-%m-%d')}")
                print(f"   Latest: {valid_dates.max().strftime('%Y-%m-%d')}")
                print(f"   Valid dates: {len(valid_dates):,} of {len(df_combined):,} rows")
        except:
            print(f"\n📅 Could not analyze date range")
    
    return df_combined


def verify_merge_result(filename='ner_entity_dataset_superclean.csv'):
    """
    Verify the merge operation was successful by analyzing the final dataset.
    """
    try:
        df = pd.read_csv(filename)
        
        print(f"\n🔍 VERIFICATION OF MERGED DATASET:")
        print(f"{'='*50}")
        print(f"   File: {filename}")
        print(f"   Total rows: {len(df):,}")
        print(f"   Unique entities: {df['Entity'].nunique()}")
        print(f"   Columns: {list(df.columns)}")
        
        # Check for any obvious issues
        print(f"\n🔧 DATA QUALITY CHECK:")
        
        # Check for missing values
        missing_data = df.isnull().sum()
        if missing_data.any():
            print(f"   Missing values found:")
            for col, count in missing_data[missing_data > 0].items():
                print(f"     {col}: {count} missing values")
        else:
            print(f"   ✓ No missing values found")
        
        # Check entity column specifically
        if 'Entity' in df.columns:
            empty_entities = df['Entity'].isin(['', ' ', None]).sum()
            if empty_entities > 0:
                print(f"   ⚠️ Warning: {empty_entities} rows with empty entities")
            else:
                print(f"   ✓ All rows have valid entity names")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying merged dataset: {e}")
        return False


# Main execution
if __name__ == "__main__":
    print("🚀 ENTITY DATASET MERGE OPERATION")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Perform the merge
    result_df = merge_entity_datasets()
    
    if result_df is not None:
        # Verify the result
        verification_success = verify_merge_result()
        
        if verification_success:
            print(f"\n✅ MERGE OPERATION COMPLETED SUCCESSFULLY!")
            print(f"✓ Data from ner_entity_dataset_TOP_100.csv has been added to ner_entity_dataset_superclean.csv")
            print(f"✓ Combined dataset saved as: ner_entity_dataset_superclean.csv")
        else:
            print(f"\n⚠️ MERGE COMPLETED BUT VERIFICATION FAILED")
            print(f"Please check the output file manually")
    else:
        print(f"\n❌ MERGE OPERATION FAILED")
        print(f"Please check the error messages above and ensure both files exist")
    
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
