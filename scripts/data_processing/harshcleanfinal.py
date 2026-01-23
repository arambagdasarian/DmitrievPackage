import pandas as pd

def create_final_nodes_dataset():
    """
    Loads NER and Merged datasets, filters NER data based on entities in the Merged dataset,
    joins Jurisdiction information, recalculates occurrences, and saves the final result.
    """
    print("Starting the process...")

    try:
        # Step 1: Load the datasets
        print("Loading ner_entity_dataset_superclean.csv...")
        df_ner = pd.read_csv('ner_entity_dataset_superclean.csv')
        print(f"Loaded {len(df_ner)} rows from NER dataset.")

        print("Loading merged_dataset.xlsx...")
        df_merged = pd.read_excel('merged_dataset.xlsx')
        print(f"Loaded {len(df_merged)} rows from Merged dataset.")

    except FileNotFoundError as e:
        print(f"Error: Could not find a required file. {e}")
        return
    except Exception as e:
        print(f"An error occurred while loading files: {e}")
        return

    # --- Data Processing Steps ---

    # Step 2: Filter NER data based on entities in the merged dataset
    print("\nFiltering NER data...")
    entities_to_keep = set(df_merged['Entity'].unique())
    original_ner_rows = len(df_ner)
    df_filtered_ner = df_ner[df_ner['Entity'].isin(entities_to_keep)].copy()
    print(f"Filtered NER data from {original_ner_rows} to {len(df_filtered_ner)} rows.")

    # Step 3: Join the jurisdiction information
    print("Joining jurisdiction information...")
    # Create a clean mapping of Entity to Jurisdiction to avoid duplicate rows during merge
    jurisdiction_map = df_merged[['Entity', 'Jurisdiction']].drop_duplicates(subset=['Entity'])
    
    # Merge the filtered NER data with the jurisdiction map
    df_final = pd.merge(df_filtered_ner, jurisdiction_map, on='Entity', how='left')
    print("Jurisdiction information has been merged.")

    # Step 4: Recalculate the occurrence count for each entity
    print("Recalculating occurrence counts...")
    # This will count how many times each entity appears in the final dataset and
    # assign that count to every row for that entity.
    df_final['Occurrences'] = df_final.groupby('Entity')['Entity'].transform('size')
    print("Occurrence counts have been recalculated.")

    # Step 5: Ensure the final output has only the specified columns in the correct order
    print("Finalizing columns...")
    final_columns = [
        'Article_ID',
        'Date',
        'Source',
        'Entity',
        'Entity_Type',
        'Occurrences',
        'Jurisdiction',
        'Context_Text'
    ]
    
    # Check if all required columns exist
    missing_columns = [col for col in final_columns if col not in df_final.columns]
    if missing_columns:
        print(f"Error: The following required columns are missing after processing: {missing_columns}")
        return

    df_final = df_final[final_columns]
    print("Columns reordered and selected.")

    # Step 6: Save the final dataset
    output_filename = 'final_nodes.csv'
    try:
        df_final.to_csv(output_filename, index=False)
        print(f"\nProcess complete. Final dataset saved as '{output_filename}'.")
        print(f"The final dataset contains {len(df_final)} rows and {len(df_final.columns)} columns.")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")

if __name__ == "__main__":
    create_final_nodes_dataset()
