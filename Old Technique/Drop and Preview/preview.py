import pandas as pd
# Replace with your actual CSV file path if needed
file_path = 'cleaned_articles_combined.csv'

# Load the CSV dataset
df = pd.read_csv(file_path)

# Show column names, data types, and non-null counts
print("\n--- DataFrame Info ---")
df.info()

# Show the first 5 rows
print("\n--- First 5 Rows ---")
print(df.head())
