import pandas as pd
from rapidfuzz import process, fuzz
import re
from collections import defaultdict

# Install rapidfuzz if not already installed
# !pip install rapidfuzz

def normalize_text(text):
    """Normalize text for fuzzy matching"""
    text = str(text).lower()
    text = re.sub(r'\s+', ' ', text)  # collapse whitespace
    text = text.strip()
    # Remove common punctuation that might interfere
    text = re.sub(r'[().,;:!?"]', '', text)
    return text

def remove_russian_stopwords(text):
    """Remove common Russian stopwords and titles"""
    stopwords = {
        'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'при', 'за', 'под', 'над',
        'между', 'через', 'без', 'против', 'вместо', 'кроме', 'среди', 'внутри',
        'господин', 'госпожа', 'г', 'гн', 'др', 'проф', 'профессор'
    }
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)

def create_entity_variants_map(entities, threshold=85):
    """Create mapping from entity variants to canonical forms using fuzzy matching"""
    
    # Calculate frequency of each entity
    entity_freq = entities.value_counts().to_dict()
    
    # Sort entities by frequency (most frequent first)
    unique_entities = sorted(entities.unique(), key=lambda x: entity_freq.get(x, 0), reverse=True)
    
    # Normalize entities for matching
    normalized_entities = {entity: normalize_text(remove_russian_stopwords(entity)) 
                          for entity in unique_entities}
    
    # Mapping from original entity to canonical entity
    entity_canonical_map = {}
    
    for entity in unique_entities:
        if entity in entity_canonical_map:
            continue
            
        # This entity becomes canonical for itself
        entity_canonical_map[entity] = entity
        normalized_current = normalized_entities[entity]
        
        # Find similar entities
        remaining_entities = [e for e in unique_entities if e not in entity_canonical_map]
        
        if remaining_entities:
            matches = process.extract(
                normalized_current, 
                [normalized_entities[e] for e in remaining_entities],
                scorer=fuzz.token_sort_ratio,
                limit=None
            )
            
            for match_norm, score, _ in matches:
                if score >= threshold:
                    # Find original entity corresponding to this normalized match
                    original_entity = next(e for e in remaining_entities 
                                         if normalized_entities[e] == match_norm)
                    entity_canonical_map[original_entity] = entity
    
    return entity_canonical_map

def clean_ner_dataset(input_file, output_file, min_occurrences=5, fuzzy_threshold=85):
    """Main function to clean the NER dataset"""
    
    print("Loading dataset...")
    df = pd.read_csv(input_file)
    print(f"Initial dataset size: {len(df):,} rows")
    print(f"Unique entities: {df['Entity'].nunique():,}")
    
    # Remove obviously problematic entities
    print("\nRemoving problematic entities...")
    
    # Filter out very short entities, numbers, and obvious noise
    df = df[df['Entity'].str.len() >= 2]
    df = df[~df['Entity'].str.match(r'^\d+$')]  # Remove pure numbers
    df = df[~df['Entity'].str.contains(r'^[A-Za-z0-9\-_]+$')]  # Remove technical strings
    
    # Remove entities that are clearly formatting artifacts
    noise_patterns = [
        r'sunsans-regular', r'arial', r'helvetica', r'times', r'courier',
        r'^\w{1,2}$',  # Very short entities
        r'^\d+[a-z]*$',  # Numbers with letters
    ]
    
    for pattern in noise_patterns:
        df = df[~df['Entity'].str.contains(pattern, case=False, na=False)]
    
    print(f"After noise removal: {len(df):,} rows")
    
    # Create entity variants mapping for each entity type separately
    print("\nCreating entity mappings with fuzzy matching...")
    
    all_mappings = {}
    
    for entity_type in df['Entity_Type'].unique():
        print(f"Processing {entity_type} entities...")
        type_entities = df[df['Entity_Type'] == entity_type]['Entity']
        type_mapping = create_entity_variants_map(type_entities, fuzzy_threshold)
        all_mappings.update(type_mapping)
    
    # Apply canonical mapping
    df['Entity_canonical'] = df['Entity'].map(all_mappings)
    
    # Calculate occurrences for canonical entities
    print("\nCalculating entity occurrences...")
    entity_counts = df.groupby(['Entity_canonical', 'Entity_Type']).size().reset_index(name='Occurrences')
    
    # Filter entities with minimum occurrences
    entities_to_keep = entity_counts[entity_counts['Occurrences'] >= min_occurrences]
    print(f"Entities with >= {min_occurrences} occurrences: {len(entities_to_keep):,}")
    
    # Create set of entities to keep for faster lookup
    keep_entities = set(zip(entities_to_keep['Entity_canonical'], entities_to_keep['Entity_Type']))
    
    # Filter dataframe
    df_clean = df[df[['Entity_canonical', 'Entity_Type']].apply(tuple, axis=1).isin(keep_entities)].copy()
    
    # Add occurrences column
    df_clean = df_clean.merge(
        entity_counts[['Entity_canonical', 'Entity_Type', 'Occurrences']], 
        on=['Entity_canonical', 'Entity_Type'], 
        how='left'
    )
    
    # Reorder columns
    columns_order = ['Article_ID', 'Date', 'Source', 'Entity_canonical', 'Entity_Type', 
                    'Occurrences', 'Context_Text']
    df_clean = df_clean[columns_order]
    
    # Rename for clarity
    df_clean.rename(columns={'Entity_canonical': 'Entity'}, inplace=True)
    
    # Sort by occurrences descending
    df_clean = df_clean.sort_values('Occurrences', ascending=False)
    df_clean.reset_index(drop=True, inplace=True)
    
    # Save cleaned dataset
    df_clean.to_csv(output_file, index=False)
    
    # Print summary statistics
    print(f"\n=== CLEANING SUMMARY ===")
    print(f"Original dataset: {len(df):,} rows")
    print(f"Cleaned dataset: {len(df_clean):,} rows")
    print(f"Reduction: {((len(df) - len(df_clean)) / len(df) * 100):.1f}%")
    print(f"Unique entities before: {df['Entity'].nunique():,}")
    print(f"Unique entities after: {df_clean['Entity'].nunique():,}")
    
    print(f"\nEntity type distribution:")
    print(df_clean['Entity_Type'].value_counts())
    
    print(f"\nTop 15 most frequent entities:")
    top_entities = df_clean.groupby('Entity')['Occurrences'].first().sort_values(ascending=False).head(15)
    for entity, count in top_entities.items():
        print(f"{entity}: {count:,}")
    
    print(f"\nCleaned dataset saved to: {output_file}")
    
    return df_clean

# Example usage
if __name__ == "__main__":
    # Run the cleaning process
    cleaned_df = clean_ner_dataset(
        input_file='ner_entity_dataset.csv',
        output_file='ner_entity_dataset_cleaned.csv',
        min_occurrences=5,
        fuzzy_threshold=85
    )
    
    # Additional analysis
    print(f"\n=== SAMPLE MERGED ENTITIES ===")
    
    # Show some examples of merged entities (if you want to verify the merging)
    # This would require keeping track of the original->canonical mapping
    # You can add this functionality if needed
