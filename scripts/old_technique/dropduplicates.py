import pandas as pd

# Load your data
df = pd.read_csv('output.csv')

# Option 1: Keep only the first occurrence of each URL
df_unique = df.drop_duplicates(subset='url', keep='first')

# Option 2: Remove all rows that have duplicated URLs (no instance kept)
# df_unique = df[~df['url'].duplicated(keep=False)]

# (Optional) Write the deduplicated DataFrame back to CSV
df_unique.to_csv('output_unique.csv', index=False)
