import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

print("Reading data...")
df = pd.read_csv('final_nodes.csv')
df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y %H:%M', errors='coerce')

cut_edges = [pd.Timestamp.min,
             pd.to_datetime('2014-01-01'),
             pd.to_datetime('2017-02-01'),
             pd.to_datetime('2022-02-24'),
             pd.Timestamp.max]
cut_labels = ['Pre-Crimea', 'Post-Crimea', 'Covid', 'War']

df = df.dropna(subset=['Date'])

df['month'] = df['Date'].dt.to_period('M').dt.to_timestamp()
df['month_period'] = pd.cut(df['month'], bins=cut_edges, labels=cut_labels, include_lowest=True, right=False)

df = df.dropna(subset=['month_period'])

monthly = (
    df.groupby(['Entity', 'Entity_Type', 'month'], as_index=False)['Occurrences']
      .sum()
      .rename(columns={'Occurrences': 'monthly_freq'})
)
monthly['period'] = pd.cut(monthly['month'], bins=cut_edges, labels=cut_labels, include_lowest=True, right=False)

print("Selecting specific actors for analysis...")
target_actors = [
    'Внешэкономбанк (ВЭБ)',
    'Фонд национального благосостояния (ФНБ)',
    'ОАО «Газпром»',
    'Сергей Чемезов',
    'Сбербанк',
    'Новатэк',
    'Российско-китайский инвестиционный фонд (РКИФ)',
    'China Investment Corporation',
    'Европейский банк реконструкции и развития (ЕБРР)',
    'Public Investment Fund (PIF)',
    'Deutsche Bank',
    'Apax Partners LLP'
]

actor_totals = monthly.groupby(['Entity'], as_index=False)['monthly_freq'].sum()
actor_totals = actor_totals[actor_totals['Entity'].isin(target_actors)]
actor_totals = actor_totals.sort_values('monthly_freq', ascending=False)

entity_types = monthly.groupby('Entity')['Entity_Type'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]).reset_index()
actor_totals = actor_totals.merge(entity_types, on='Entity')

top_actors = actor_totals['Entity'].tolist()
print(f"Found {len(top_actors)} of {len(target_actors)} target actors in data")

print("Creating plots...")
num_actors = len(top_actors)
if num_actors <= 6:
    nrows, ncols = 3, 2
elif num_actors <= 10:
    nrows, ncols = 5, 2
elif num_actors <= 12:
    nrows, ncols = 6, 2
elif num_actors <= 16:
    nrows, ncols = 8, 2
else:
    nrows, ncols = (num_actors + 1) // 2, 2

fig, axes = plt.subplots(nrows, ncols, figsize=(16, nrows*4))
fig.suptitle(f'Monthly Occurrence Frequency and Trend for Selected Actors ({num_actors} entities)', fontsize=16, y=1.02)
axes_flat = axes.flatten()

colors = {
    'Pre-Crimea': '#1f77b4',
    'Post-Crimea': '#2ca02c',
    'Covid': '#ff7f0e',
    'War': '#d62728'
}

for idx, (entity, etype, total) in enumerate(actor_totals[['Entity', 'Entity_Type', 'monthly_freq']].itertuples(index=False, name=None)):
    ax = axes_flat[idx]
    actor_months = monthly[monthly['Entity'] == entity].copy()
    if actor_months.empty:
        ax.set_visible(False)
        continue

    actor_months = actor_months.sort_values('month')
    start_month = actor_months['month'].min()
    actor_months['x_days'] = (actor_months['month'] - start_month).dt.days

    for p in cut_labels:
        subset = actor_months[actor_months['period'] == p]
        if not subset.empty:
            ax.scatter(subset['x_days'], subset['monthly_freq'],
                       c=colors[p], s=60, alpha=0.75, label=p)

    if len(actor_months) > 1:
        slope, intercept, r_value, _, _ = stats.linregress(actor_months['x_days'], actor_months['monthly_freq'])
        x_range = np.array([actor_months['x_days'].min(), actor_months['x_days'].max()])
        y_pred = slope * x_range + intercept
        ax.plot(x_range, y_pred, 'k--', linewidth=2, label=f'Trend (R²={r_value**2:.2f})')

    ax.set_title(f"{entity[:32]}{'...' if len(entity) > 32 else ''}\n({etype}, Total: {int(total)})", fontsize=11)
    # Format x-axis to show monthly labels at ~4 evenly spaced ticks
    tick_positions = np.linspace(actor_months['x_days'].min(), actor_months['x_days'].max(), 4)
    tick_dates = [start_month + pd.Timedelta(days=float(d)) for d in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([d.strftime('%Y-%m') for d in tick_dates], rotation=35)

    y_max = actor_months['monthly_freq'].max()
    ax.set_ylim(0, max(1, y_max * 1.15))
    ax.set_ylabel('Monthly Occurrence Frequency')
    ax.grid(True, alpha=0.3)

for i in range(num_actors, len(axes_flat)):
    axes_flat[i].set_visible(False)

handles, labels = axes_flat[0].get_legend_handles_labels()
seen = set()
unique_handles_labels = [(h, l) for h, l in zip(handles, labels) if (l not in seen and not seen.add(l))]
if unique_handles_labels:
    uh, ul = zip(*unique_handles_labels)
    fig.legend(uh, ul, loc='center', bbox_to_anchor=(0.5, 0.02), ncol=4, fontsize=11)

plt.tight_layout()
plt.subplots_adjust(bottom=0.1)

print("Saving plot...")
plt.savefig('occurrence_regressions.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"\nSelected Actors by Total Monthly Occurrence Frequency:")
for _, r in actor_totals.iterrows():
    print(f"- {r['Entity']} ({r['Entity_Type']}): {int(r['monthly_freq'])}")

missing_actors = [actor for actor in target_actors if actor not in top_actors]
if missing_actors:
    print(f"\nActors not found in data:")
    for actor in missing_actors:
        print(f"- {actor}")

print("Done!")