import pandas as pd

def update_entities():
    # Load the dataset
    df = pd.read_csv('ner_entity_dataset_superclean.csv')
    
    # Define entity replacements
    entity_replacements = {
        'Волож': 'Аркадий Волож',
        'Гонконгской бирже': 'Гонконгская биржа',
        'Консорциум': 'Консорциум инвесторов'
    }
    
    # Apply replacements to Entity column
    df['Entity'] = df['Entity'].replace(entity_replacements)
    
    # Save back to CSV
    df.to_csv('ner_entity_dataset_superclean.csv', index=False)
    
    print("Entity replacements completed:")
    for old, new in entity_replacements.items():
        print(f"  '{old}' → '{new}'")

if __name__ == "__main__":
    update_entities()
