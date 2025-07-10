import pandas as pd
import re
from rapidfuzz import process, fuzz

# Load dataset
input_file = 'ner_entity_dataset_normalized.csv'
output_file = 'ner_entity_dataset_superclean.csv'
df = pd.read_csv(input_file)

print(f"Loaded dataset with {len(df):,} rows and columns: {df.columns.tolist()}")

def normalize_person_name(entity):
    """
    Normalize Russian person names: merges cases, declensions, and common variants.
    Keeps distinct people separate (e.g., Medvedev ≠ Sokolov).
    """
    # Remove extra whitespace and punctuation
    entity = str(entity).strip()
    entity = re.sub(r'[().,;:!?\"\']', '', entity)
    entity = re.sub(r'\s+', ' ', entity)
    entity_lower = entity.lower()

    # Putin normalization
    putin_patterns = [
        r'^владимир(ом|у|а|е|ы|и|)\s+пути(н|на|ну|ным|не|)$',
        r'^пути(н|на|ну|ным|не|)$',
        r'^в\.?в\.?\s+пути(н|на|ну|ным|не|)$',
        r'^владимиром владимировичем путиным$',
        r'^владимира владимировича путина$'
    ]
    for pat in putin_patterns:
        if re.match(pat, entity_lower):
            return 'Владимир Путин'

    # Trump normalization
    trump_patterns = [
        r'^дональд(ом|у|а|е|ы|и|)\s+трамп(а|у|ом|е|)$',
        r'^трамп(а|у|ом|е|)$',
        r'^donald trump$'
    ]
    for pat in trump_patterns:
        if re.match(pat, entity_lower):
            return 'Дональд Трамп'

    # Lavrov normalization
    lavrov_patterns = [
        r'^сергей(ем|ю|я|е|и|)\s+лавров(а|у|ым|е|)$',
        r'^лавров(а|у|ым|е|)$'
    ]
    for pat in lavrov_patterns:
        if re.match(pat, entity_lower):
            return 'Сергей Лавров'

    # Medvedev normalization
    medvedev_patterns = [
        r'^дмитрий(ем|ю|я|е|и|)\s+медведев(а|у|ым|е|)$',
        r'^медведев(а|у|ым|е|)$'
    ]
    for pat in medvedev_patterns:
        if re.match(pat, entity_lower):
            return 'Дмитрий Медведев'

    # Dmitriev normalization
    dmitriev_patterns = [
        r'^кирилл(ом|у|а|е|и|)\s+дмитриев(а|у|ым|е|)$',
        r'^дмитриев(а|у|ым|е|)$'
    ]
    for pat in dmitriev_patterns:
        if re.match(pat, entity_lower):
            return 'Кирилл Дмитриев'

    # Peskov normalization
    peskov_patterns = [
        r'^дмитрий(ем|ю|я|е|и|)\s+песков(а|у|ым|е|)$',
        r'^песков(а|у|ым|е|)$'
    ]
    for pat in peskov_patterns:
        if re.match(pat, entity_lower):
            return 'Дмитрий Песков'

    # Ushakov normalization
    ushakov_patterns = [
        r'^юрий(ем|ю|я|е|и|)\s+ушаков(а|у|ым|е|)$',
        r'^ушаков(а|у|ым|е|)$'
    ]
    for pat in ushakov_patterns:
        if re.match(pat, entity_lower):
            return 'Юрий Ушаков'

    return entity

def normalize_org_name(entity):
    """
    Normalize common Russian organization names (banks, telecom, etc.).
    """
    entity_lower = entity.lower()
    org_map = {
        'Сбербанк': ['сбербанк', 'сбербанка', 'сбербанку', 'сбербанком', 'сбербанке'],
        'ВТБ': ['втб', 'банк втб'],
        'ВЭБ': ['вэб', 'внешэкономбанк'],
        'МТС': ['мтс', 'мобильные телесистемы'],
        'Ростелеком': ['ростелеком', 'ростелекома', 'ростелекому', 'ростелекомом', 'ростелекоме'],
        'Госдума': ['госдума', 'госдумы', 'госдуме', 'госдуму', 'госдумой', 'государственная дума'],
        'БРИКС': ['брикс', 'brics']
    }
    for canon, variants in org_map.items():
        if entity_lower in variants:
            return canon
    return entity

def normalize_entity(row):
    if row['Entity_Type'] == 'PER':
        return normalize_person_name(row['Entity'])
    elif row['Entity_Type'] == 'ORG':
        return normalize_org_name(row['Entity'])
    else:
        return row['Entity']

print("Normalizing entities (rule-based)...")
df['Entity_normalized'] = df.apply(normalize_entity, axis=1)

# Fuzzy merge close variants (for all types)
print("Performing fuzzy matching...")
unique_entities = df['Entity_normalized'].unique().tolist()
entity_map = {}
canonical_entities = []
FUZZY_THRESHOLD = 92

for entity in unique_entities:
    if not canonical_entities:
        canonical_entities.append(entity)
        entity_map[entity] = entity
        continue
    result = process.extractOne(entity, canonical_entities, scorer=fuzz.token_sort_ratio)
    if result is not None:
        match, score, _ = result
        if score >= FUZZY_THRESHOLD:
            entity_map[entity] = match
        else:
            entity_map[entity] = entity
            canonical_entities.append(entity)
    else:
        entity_map[entity] = entity
        canonical_entities.append(entity)

print("Mapping normalized entities to canonical entities...")
df['Entity_canonical'] = df['Entity_normalized'].map(entity_map)

# Enhanced blacklist
BLACKLIST = set([
    'правительство', 'президент', 'министерство', 'минздрав', 'мид', 'минфин', 'минэкономразвития',
    'кремль', 'госдума', 'совет федерации', 'парламент', 'администрация', 'корреспондент', 'журналист',
    'агентство', 'служба', 'комитет', 'департамент', 'управление', 'ведомство', 'корпорация', 'холдинг',
    'группа компаний', 'ооо', 'зао', 'оао', 'ао', 'пао', 'нко', 'ltd', 'llc', 'inc', 'corp', 'gmbh',
    'компания', 'организация', 'учреждение', 'фирма', 'предприятие', 'структура', 'банк', 'биржа', 'рынок',
    'экономика', 'финансы', 'бюджет', 'инвестиции', 'директор', 'руководитель', 'председатель', 'заместитель',
    'министр', 'губернатор', 'мэр', 'глава', 'начальник', 'секретарь', 'эксперт', 'аналитик', 'специалист',
    'источник', 'собеседник', 'спецпредставитель', 'представитель', 'помощник', 'советник', 'первый', 'главный',
    'старший', 'исполняющий', 'временно', 'сми', 'тасс', 'рбк', 'коммерсантъ', 'ведомости', 'интерфакс',
    'россия сегодня', 'rt', 'russia today', 'bbc', 'cnn', 'reuters', 'bloomberg', 'ap', 'afp', 'dw', 'france24',
    'euronews', 'прайм'
])

print("Applying blacklist...")
df_clean = df[~df['Entity_canonical'].str.lower().isin(BLACKLIST)].copy()

print(f"After blacklist: {len(df_clean):,} rows")

# Recalculate occurrences for canonical entities
print("Recalculating occurrences...")
entity_article_counts = df_clean.groupby(['Entity_canonical', 'Entity_Type'])['Article_ID'].nunique().reset_index()
entity_article_counts = entity_article_counts.rename(columns={'Article_ID': 'New_Occurrences'})

print(f"Calculated occurrences for {len(entity_article_counts):,} unique entities")

# Filter entities with at least 5 occurrences
entities_to_keep = entity_article_counts[entity_article_counts['New_Occurrences'] >= 5]
print(f"Entities with >= 5 occurrences: {len(entities_to_keep):,}")

keep_entities = set(zip(entities_to_keep['Entity_canonical'], entities_to_keep['Entity_Type']))
df_final = df_clean[df_clean[['Entity_canonical', 'Entity_Type']].apply(tuple, axis=1).isin(keep_entities)].copy()

print(f"Final dataset before merge: {len(df_final):,} rows")

# Merge occurrences - FIXED VERSION
df_final = df_final.merge(
    entities_to_keep[['Entity_canonical', 'Entity_Type', 'New_Occurrences']], 
    on=['Entity_canonical', 'Entity_Type'], 
    how='left'
)

print(f"Columns after merge: {df_final.columns.tolist()}")

# Clean up columns - FIXED VERSION
# Drop old columns first
columns_to_drop = []
if 'Entity' in df_final.columns:
    columns_to_drop.append('Entity')
if 'Occurrences' in df_final.columns:
    columns_to_drop.append('Occurrences')
if 'Entity_normalized' in df_final.columns:
    columns_to_drop.append('Entity_normalized')

if columns_to_drop:
    df_final = df_final.drop(columns=columns_to_drop)

# Rename columns
df_final = df_final.rename(columns={
    'Entity_canonical': 'Entity',
    'New_Occurrences': 'Occurrences'
})

print(f"Columns after cleanup: {df_final.columns.tolist()}")

# Reorder columns - FIXED VERSION
available_columns = df_final.columns.tolist()
desired_cols = ['Article_ID', 'Date', 'Source', 'Entity', 'Entity_Type', 'Occurrences', 'Context_Text']
cols = [col for col in desired_cols if col in available_columns]

# Add any remaining columns
for col in available_columns:
    if col not in cols:
        cols.append(col)

print(f"Final column order: {cols}")
df_final = df_final[cols]

# Sort
df_final = df_final.sort_values(['Occurrences', 'Entity'], ascending=[False, True]).reset_index(drop=True)

# Save
print(f"Saving cleaned dataset to {output_file}...")
df_final.to_csv(output_file, index=False)

print(f"\n=== CLEANING COMPLETE ===")
print(f"Original dataset: {len(df):,} rows")
print(f"Final dataset: {len(df_final):,} rows")
print(f"Unique entities: {df_final['Entity'].nunique():,}")

# Show top entities
print(f"\nTop 10 entities by occurrence:")
top_entities = df_final.groupby('Entity')['Occurrences'].first().sort_values(ascending=False).head(10)
for entity, count in top_entities.items():
    print(f"  {entity}: {count:,}")

print(f"\nCleaned dataset saved to: {output_file}")
