import pandas as pd

# List of file names to clean
filenames = [
    "matched_entities_covid.csv",
    "matched_entities_post_crimea.csv",
    "matched_entities_pre_crimea.csv",
    "matched_entities_war.csv"
]

# Function to remove duplicates based on Article_ID and Entity
def clean_duplicates(file):
    df = pd.read_csv(file)
    df_cleaned = df.drop_duplicates(subset=['Article_ID', 'Entity'])
    cleaned_filename = file.replace(".csv", "_cleaned.csv")
    df_cleaned.to_csv(cleaned_filename, index=False)
    print(f"✅ Cleaned and saved: {cleaned_filename}")

# Run the cleaning for each file
for file in filenames:
    clean_duplicates(file)
