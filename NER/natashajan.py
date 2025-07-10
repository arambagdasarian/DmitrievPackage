import pandas as pd
from natasha import (
    Doc, Segmenter, NewsEmbedding, NewsMorphTagger, NewsSyntaxParser, NewsNERTagger
)
from collections import defaultdict, Counter
import re
from itertools import combinations

# Load the articles dataset
file_path = 'cleaned_articles_combined.csv'
df = pd.read_csv(file_path)

# Initialize Natasha NLP pipeline
segmenter = Segmenter()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
syntax_parser = NewsSyntaxParser(emb)
ner_tagger = NewsNERTagger(emb)

# Comprehensive blacklist for Russian news (add more as needed)
BLACKLIST = {
    'дмитриев', 'кирилл', 'путин', 'кремль', 'россия', 'рф', 'москва', 'российская федерация',
    'российской федерации', 'россиянин', 'россияне', 'россиянами', 'россиян', 'правительство',
    'сша', 'америка', 'вашингтон', 'европа', 'министерство', 'госдума',
    'совет федерации', 'министр', 'президент', 'правительство', 'государство', 'администрация',
    'федерация', 'депутат', 'губернатор', 'министр', 'правительство', 'официальный представитель',
    'агентство', 'комитет', 'служба', 'центр', 'суд', 'республика', 'область', 'край', 'город',
    'район', 'улица', 'дом', 'корреспондент', 'редакция', 'новости', 'интерфакс', 'рбк', 'коммерсантъ',
    'ведомости', 'газета', 'ап', 'afp', 'dw', 'российский', 'российская',
    'российское', 'российские', 'российских', 'российскому', 'российским', 'российском', 'российская федерация'
}

def is_blacklisted(entity):
    entity_lower = entity.lower()
    for bl_word in BLACKLIST:
        if re.search(rf'\b{re.escape(bl_word)}\b', entity_lower):
            return True
    return False

def extract_entities(text):
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)
    doc.tag_ner(ner_tagger)
    return [(span.text, span.type) for span in doc.spans]

entity_records = []
entity_article_counts = defaultdict(set)  # entity -> set of article_ids

for idx, row in df.iterrows():
    text = str(row['body']) if pd.notnull(row['body']) else ''
    if not text.strip():
        continue  # Skip empty articles

    date = row['date']
    source = row['source']
    article_id = row['article_id']

    # Extract entities with Natasha
    entities = extract_entities(text)
    unique_entities = set()
    for entity, etype in entities:
        if is_blacklisted(entity):
            continue
        if len(entity) < 2 or etype not in ['PER', 'LOC', 'ORG']:
            continue
        unique_entities.add((entity, etype))
    for entity, etype in unique_entities:
        entity_records.append({
            'Article_ID': article_id,
            'Date': date,
            'Source': source,
            'Entity': entity,
            'Entity_Type': etype,
            'Context_Text': text[:120] + '...'
        })
        entity_article_counts[entity].add(article_id)

# Filter entities with at least 5 mentions
entity_mentions = Counter({entity: len(article_ids) for entity, article_ids in entity_article_counts.items()})
entities_to_keep = {entity for entity, count in entity_mentions.items() if count >= 5}
filtered_records = [rec for rec in entity_records if rec['Entity'] in entities_to_keep]

# Save the filtered entity dataset
entity_df = pd.DataFrame(filtered_records)
entity_df.to_csv('ner_entity_dataset.csv', index=False)

# --- Co-occurrence / Edge List for SNA ---

edge_records = []
# Group by article
articles = entity_df.groupby('Article_ID')
edge_counter = Counter()

for article_id, group in articles:
    entities = list(zip(group['Entity'], group['Entity_Type']))
    date = group['Date'].iloc[0]
    for (e1, t1), (e2, t2) in combinations(entities, 2):
        if e1 == e2:
            continue
        # Sort to avoid duplicate edges (A-B and B-A)
        source_entity, target_entity = sorted([e1, e2])
        target_type = t2 if target_entity == e2 else t1
        edge = (source_entity, target_entity, target_type, article_id, date)
        edge_counter[edge] += 1

# Prepare edge list records
for (source_entity, target_entity, target_type, article_id, date), freq in edge_counter.items():
    edge_records.append({
        'Source_Entity': source_entity,
        'Target_Entity': target_entity,
        'Entity_Type_Target': target_type,
        'Article_ID': article_id,
        'Date': date,
        'Frequency': freq
    })

edge_df = pd.DataFrame(edge_records)
edge_df.to_csv('ner_cooccurrence_edgelist.csv', index=False)

print(f"Saved {len(entity_df)} entity occurrences to ner_entity_dataset.csv")
print(f"Saved {len(edge_df)} co-occurrence edges to ner_cooccurrence_edgelist.csv")
