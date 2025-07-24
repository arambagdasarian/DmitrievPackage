import pandas as pd

# Load your cleaned dataset
df = pd.read_csv('ner_entity_dataset_final_clean.csv')

# Count unique entities with occurrences <= 50
entities_up_to_50 = df[df['Occurrences'] <= 50]['Entity'].nunique()

print(f"Number of unique entities with ≤50 occurrences: {entities_up_to_50:,}")

# Get total number of entities for comparison
total_entities = df['Entity'].nunique()
percentage = (entities_up_to_50 / total_entities) * 100

print(f"Total entities in dataset: {total_entities:,}")
print(f"Percentage of entities with ≤50 occurrences: {percentage:.1f}%")


# Create occurrence ranges for better analysis
def get_occurrence_breakdown(df):
    ranges = [
        (1, 5, "1-5 occurrences"),
        (6, 10, "6-10 occurrences"), 
        (11, 20, "11-20 occurrences"),
        (21, 30, "21-30 occurrences"),
        (31, 40, "31-40 occurrences"),
        (41, 50, "41-50 occurrences"),
        (51, 100, "51-100 occurrences"),
        (101, float('inf'), "100+ occurrences")
    ]
    
    breakdown = []
    for min_occ, max_occ, label in ranges:
        if max_occ == float('inf'):
            count = df[df['Occurrences'] >= min_occ]['Entity'].nunique()
        else:
            count = df[(df['Occurrences'] >= min_occ) & (df['Occurrences'] <= max_occ)]['Entity'].nunique()
        breakdown.append({'Range': label, 'Count': count})
    
    return pd.DataFrame(breakdown)

# Get breakdown
breakdown_df = get_occurrence_breakdown(df)
print("\nOccurrence Range Breakdown:")
print(breakdown_df.to_string(index=False))

# Calculate cumulative counts
cumulative_up_to_50 = sum(breakdown_df[breakdown_df['Range'].str.contains('1-5|6-10|11-20|21-30|31-40|41-50')]['Count'])
print(f"\nCumulative entities with ≤50 occurrences: {cumulative_up_to_50:,}")
