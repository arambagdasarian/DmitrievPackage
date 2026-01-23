import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the dataset
file_path = 'ner_analysis.csv'
df = pd.read_csv(file_path)
df['weight'] = df['weight'].astype(float)

sns.set(style='whitegrid')

# 1. Bar chart: Entities sorted by highest occurrence count
plt.figure(figsize=(10, 6))
sorted_by_count = df.sort_values(by='occurrence_count', ascending=False)
sns.barplot(x='occurrence_count', y='entity', data=sorted_by_count, palette='viridis')
plt.title('Entities Sorted by Occurrence Count')
plt.xlabel('Occurrence Count')
plt.ylabel('Entity')
plt.tight_layout()
plt.savefig('entities_sorted_by_count.png')
plt.close()

# 2. Pie chart: Distribution of entity types by total occurrence count
plt.figure(figsize=(8, 8))
grouped_by_type = df.groupby('type').agg({'occurrence_count': 'sum'}).reset_index()
plt.pie(grouped_by_type['occurrence_count'], labels=grouped_by_type['type'],
        autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
plt.title('Distribution of Entity Types by Occurrence Count')
plt.savefig('entity_type_distribution.png')
plt.close()

# 3. Scatter plot: Weighted importance (occurrence_count * weight) of entities
plt.figure(figsize=(10, 6))
df['weighted_importance'] = df['occurrence_count'] * df['weight']
sns.scatterplot(x='weighted_importance', y='entity', hue='type', data=df, s=100, palette='deep')
plt.title('Entities by Weighted Importance')
plt.xlabel('Weighted Importance')
plt.ylabel('Entity')
plt.legend(title='Entity Type')
plt.tight_layout()
plt.savefig('entities_weighted_importance.png')
plt.close()
