import pandas as pd

# Load the CSV file
df = pd.read_csv('ner_analysis.csv')

# Pick 10 random rows
sampled_df = df.sample(10)

# Set display options for better readability
pd.set_option('display.max_columns', None)         # Show all columns
pd.set_option('display.width', 120)                # Set terminal display width
pd.set_option('display.max_colwidth', 30)          # Limit column width (truncate long text)

# Print the sample
print(sampled_df)
