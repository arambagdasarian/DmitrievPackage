import pandas as pd
from natasha import (
    Doc,
    Segmenter,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger
)
from collections import defaultdict
import re

# Initialize Natasha NLP pipeline
segmenter = Segmenter()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
syntax_parser = NewsSyntaxParser(emb)
ner_tagger = NewsNERTagger(emb)

# Configuration
BLACKLIST = {'дмитриев', 'кирилл', 'путин', 'кремль', 'россия', 'рф', 'москва'}
INPUT_CSV = 'cleaned_articles_combined.csv'
OUTPUT_CSV = 'ner_analysis.csv'

def extract_entities(text):
    """Extract entities using Natasha's full NLP pipeline"""
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)
    doc.tag_ner(ner_tagger)
    
    entities = []
    for span in doc.spans:
        entities.append((span.text, span.type))
    return entities

# Process dataset
df = pd.read_csv(INPUT_CSV)
entity_records = []
entity_article_counts = defaultdict(int)

for _, row in df.iterrows():
    text = str(row['body']) if pd.notnull(row['body']) else ''
    if not text.strip():
        continue  # Skip empty articles

    date = row['date']
    source = row['source']
    
    # Extract entities with Natasha
    entities = extract_entities(text)
    
    # Track unique entities per article
    unique_entities = set()
    for entity, etype in entities:
        entity_lower = entity.lower()
        if any(re.search(rf'\b{bl_word}\b', entity_lower) for bl_word in BLACKLIST):
            continue
        if len(entity) < 2 or etype not in ['PER', 'LOC', 'ORG']:
            continue
        unique_entities.add((entity, etype))
        entity_records.append({
            'entity': entity,
            'type': etype,
            'date': date,
            'source': source,
            'context': text[:120] + '...'
        })
    for entity in unique_entities:
        entity_article_counts[entity] += 1

# Calculate weights
total_articles = len(df)
results = []

for record in entity_records:
    key = (record['entity'], record['type'])
    article_count = entity_article_counts[key]
    weight = article_count / total_articles
    
    results.append({
        'entity': record['entity'],
        'type': record['type'],
        'date': record['date'],
        'source': record['source'],
        'occurrence_count': article_count,
        'weight': f"{weight:.6f}",
        'context': record['context']
    })

# Save results
output_df = pd.DataFrame(results)
output_df.to_csv(OUTPUT_CSV, index=False)
print(f"Processed {len(results)} entity occurrences from {total_articles} articles")
