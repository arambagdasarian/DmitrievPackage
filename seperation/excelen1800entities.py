import pandas as pd

df = pd.read_csv('ner_entity_dataset_superclean_50plus.csv')

entity_df = df[['Entity', 'Occurrences']].drop_duplicates(subset=['Entity'])

entity_df = entity_df.sort_values('Occurrences', ascending=False).drop_duplicates('Entity')

entity_df = entity_df.sort_values('Occurrences', ascending=False).reset_index(drop=True)

entity_df.to_excel('unique_entities_with_occurrences.xlsx', index=False)
