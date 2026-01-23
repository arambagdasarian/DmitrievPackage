import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# Set style for better visualization
plt.style.use('default')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['axes.grid'] = True
sns.set_palette("Set2")

# Read the CSV file
df = pd.read_csv('final_nodes.csv')

# Convert dates to datetime
df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y %H:%M', errors='coerce')

# Fix entity type misclassifications
print("Fixing entity type misclassifications...")
# Organizations incorrectly marked as PER
org_keywords = ['банк', 'фонд', 'центр', 'министерство', 'корпорация', 'компания', 'group', 'fund', 'bank', 'corporation', 'center']
for keyword in org_keywords:
    mask = (df['Entity'].str.contains(keyword, case=False, na=False)) & (df['Entity_Type'] == 'PER')
    df.loc[mask, 'Entity_Type'] = 'ORG'
    if mask.sum() > 0:
        print(f"Fixed {mask.sum()} records with '{keyword}' from PER to ORG")

# Combine duplicate entities with different Entity_Types (like Gamaleya Center)
print("Combining entities with mixed classifications...")
entity_corrections = {}
for entity in df['Entity'].unique():
    entity_data = df[df['Entity'] == entity]
    entity_types = entity_data['Entity_Type'].value_counts()
    
    # If entity appears as both PER and ORG, choose the most frequent one
    if len(entity_types) > 1:
        most_common_type = entity_types.index[0]
        df.loc[df['Entity'] == entity, 'Entity_Type'] = most_common_type
        print(f"Standardized '{entity[:50]}...' as {most_common_type}")

print("Data cleaning completed.")

# Define time periods
def get_period(date):
    if pd.isnull(date):
        return None
    if date < pd.to_datetime('2014-01-01'):
        return 'pre_crimea'
    elif date < pd.to_datetime('2017-02-01'):
        return 'post_crimea'
    elif date < pd.to_datetime('2022-02-24'):
        return 'covid'
    else:
        return 'war'

# Add period column
df['period'] = df['Date'].apply(get_period)

# Remove rows with invalid dates
df = df.dropna(subset=['period'])

# Print data overview
print("\nData Overview:")
print(f"Total number of records: {len(df)}")
print("\nEntity Types in data:")
print(df['Entity_Type'].value_counts())
print("\nTime periods found in data:")
print(df['period'].value_counts().sort_index())

def calculate_period_scores(period_data):
    """Calculate scores for all entities in a given period."""
    scores = defaultdict(lambda: {'occurrences': 0, 'articles': set(), 'sources': set()})
    
    # Collect data for each entity
    for _, row in period_data.iterrows():
        entity = row['Entity']
        scores[entity]['occurrences'] += row['Occurrences']
        scores[entity]['articles'].add(row['Article_ID'])
        scores[entity]['sources'].add(row['Source'])
        scores[entity]['type'] = row['Entity_Type']  # Store entity type
    
    # Calculate composite scores
    composite_scores = {}
    max_occurrences = max(s['occurrences'] for s in scores.values())
    max_articles = max(len(s['articles']) for s in scores.values())
    max_sources = max(len(s['sources']) for s in scores.values())
    
    for entity, data in scores.items():
        # Normalize metrics
        norm_occurrences = data['occurrences'] / max_occurrences if max_occurrences > 0 else 0
        norm_articles = len(data['articles']) / max_articles if max_articles > 0 else 0
        norm_sources = len(data['sources']) / max_sources if max_sources > 0 else 0
        
        # Calculate composite score with weights
        composite_score = (
            0.4 * norm_occurrences +  # Importance of total mentions
            0.4 * norm_articles +     # Importance of article coverage
            0.2 * norm_sources        # Importance of source diversity
        )
        
        composite_scores[entity] = {
            'score': composite_score,
            'type': data['type']
        }
    
    return composite_scores

# Calculate scores for each period
time_periods = ['pre_crimea', 'post_crimea', 'covid', 'war']
period_scores = {}
for period in time_periods:
    period_data = df[df['period'] == period]
    if not period_data.empty:
        period_scores[period] = calculate_period_scores(period_data)

# Create a DataFrame with scores for all periods
entities = set()
for period_data in period_scores.values():
    entities.update(period_data.keys())

scores_data = []
for entity in entities:
    row = {'Entity': entity}
    total_score = 0
    valid_periods = 0
    
    # Get entity type (should be same across periods)
    entity_type = None
    for period in time_periods:
        if entity in period_scores[period]:
            if entity_type is None:
                entity_type = period_scores[period][entity]['type']
            score = period_scores[period][entity]['score']
            row[period] = score
            total_score += score
            valid_periods += 1
    
    row['Entity_Type'] = entity_type
    row['average_score'] = total_score / valid_periods if valid_periods > 0 else 0
    scores_data.append(row)

# Convert to DataFrame
scores_df = pd.DataFrame(scores_data)

# Print top entities by type
print("\nTop entities by type:")
for entity_type in scores_df['Entity_Type'].unique():
    print(f"\n{entity_type}:")
    type_scores = scores_df[scores_df['Entity_Type'] == entity_type].nlargest(5, 'average_score')
    print(type_scores[['Entity', 'average_score']].to_string())

# Get overall top 10 actors (excluding RDIF)
print("\nOverall Top 10 Actors:")
# Get top 11 to account for RDIF exclusion
all_top_actors = scores_df.nlargest(11, 'average_score')

# Filter out RDIF-related entities
rdif_keywords = ['РФПИ', 'RDIF', 'Российский фонд прямых инвестиций', 'Russian Direct Investment Fund']
top_10_actors = all_top_actors[~all_top_actors['Entity'].str.contains('|'.join(rdif_keywords), case=False, na=False)].head(10)

print(top_10_actors[['Entity', 'Entity_Type', 'average_score']].to_string())

# Create visualization with wider aspect ratio
plt.figure(figsize=(20, 8))

# Plot lines for each actor with proper handling of missing periods
for _, row in top_10_actors.iterrows():
    actor_scores = []
    for period in time_periods:
        if period in row and pd.notna(row[period]):
            actor_scores.append(row[period])
        else:
            actor_scores.append(0)  # Use 0 for periods where actor doesn't appear
    
    # Only plot if actor has data in at least one period
    if any(score > 0 for score in actor_scores):
        plt.plot(range(len(time_periods)), actor_scores, marker='o', linewidth=3,
                 markersize=8, label=f"{row['Entity']} ({row['Entity_Type']})")
    
    # Print info about missing periods for entities
    missing_periods = [period for i, period in enumerate(time_periods) if actor_scores[i] == 0]
    if missing_periods:
        print(f"{row['Entity']}: No data in {missing_periods} (expected for entities like Gamaleya Center that emerged during COVID)")

# Customize plot
period_labels = ['Pre-Crimea', 'Post-Crimea', 'Covid', 'War']
plt.title('Top 10 Actors: Composite Score Changes Over Time Periods', fontsize=16, pad=20)
plt.xlabel('Time Period', fontsize=14)
plt.ylabel('Composite Score', fontsize=14)

# Make x-axis labels more prominent
plt.xticks(range(len(time_periods)), period_labels, rotation=0, fontsize=12)

# Add grid for better readability
plt.grid(True, linestyle='--', alpha=0.7)

# Adjust y-axis to start from 0
plt.ylim(bottom=0)

# Move legend below the plot
plt.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=2, 
          fontsize=12, borderaxespad=0.)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save the plot with extra space at bottom for legend
plt.savefig('composite_score_evolution.png', dpi=300, bbox_inches='tight', 
            pad_inches=0.5)
plt.close()