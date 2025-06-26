import pandas as pd
from rapidfuzz import fuzz

# 1. Load your cleaned entities
df = pd.read_csv("dmitriev_entities_cleaned.csv")
unique_norms = df['norm'].unique().tolist()

# 2. Fuzzy‐cluster normalized names
SCORE_CUTOFF = 90  # tweak between 80–95 for more or less aggressive merging
clusters = {}      # will map each norm -> its canonical rep
reps = []          # list of current canonical reps

for name in unique_norms:
    for rep in reps:
        if fuzz.token_sort_ratio(name, rep) >= SCORE_CUTOFF:
            clusters[name] = rep
            break
    else:
        # no rep matched → this name becomes a new rep
        reps.append(name)
        clusters[name] = name

# 3. Assign each row to its canonical cluster
df['norm_canonical'] = df['norm'].map(clusters)

# 4. Collapse to one row per cluster (i.e., one representative entity)
df_clustered = df.drop_duplicates(subset=['norm_canonical']).copy()
df_clustered = df_clustered.rename(columns={'norm_canonical':'canonical_norm'})

# 5. Save clustered results
df_clustered.to_csv("dmitriev_entities_clustered.csv", index=False)

# 6. Summary
print(f"Unique norms before clustering: {len(unique_norms)}")
print(f"Canonical clusters formed: {len(reps)}")
print("Sample canonical representatives:")
print(reps[:10])
