# clean_entities.py

import pandas as pd
import re
import spacy

# ========== CONFIG ==========
INPUT_CSV = "dmitriev_entities.csv"           # path to your extracted entities
OUTPUT_CSV = "dmitriev_entities_cleaned.csv"  # where to write the cleaned nodes

MIN_LEN = 3            # minimum character length for entity
FREQ_THRESH = 2        # minimum number of mentions to keep (lowered from 3)
SEED_LIST = [
    "Кирилл Дмитриев",
    "Российский фонд прямых инвестиций",
    # add other seed names here...
]
BLACKLIST = [
    "г н", "редакция", "статья", "пример",
    # add other non-name terms...
]

# ========== LOAD DATA ==========
df = pd.read_csv(INPUT_CSV)
print(f"Initial total mentions: {len(df)}")
print(f"Unique raw entities: {df['entity'].nunique()}")

# ========== SETUP NORMALIZER ==========
nlp = spacy.load("ru_core_news_lg", disable=["parser", "ner", "tok2vec", "attribute_ruler"])
nlp.max_length = 5_000_000

def normalize(text: str) -> str:
    text = str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    doc = nlp(text)
    lemmas = [tok.lemma_.lower() for tok in doc if not tok.is_punct]
    return " ".join(lemmas).strip()

# ========== ADD NORMALIZED COLUMN ==========
df['norm'] = df['entity'].apply(normalize)
print(f"Unique normalized forms: {df['norm'].nunique()}")

# ========== FILTERS ==========
# 1) Remove seeds
seed_norms = {normalize(s) for s in SEED_LIST}

# 2) Remove blacklist
black_norms = {normalize(b) for b in BLACKLIST}

# 3) Length and digits filters
mask_len   = df['entity'].str.len() >= MIN_LEN
mask_digit = ~df['entity'].str.contains(r'\d')

# Combined mask
keep_mask = mask_len & mask_digit & ~df['norm'].isin(seed_norms) & ~df['norm'].isin(black_norms)
filtered = df[keep_mask].copy()
print(f"Mentions after basic filtering: {len(filtered)}")

# ========== FREQUENCY THRESHOLD ==========
freq = filtered['norm'].value_counts()
valid_norms = set(freq[freq >= FREQ_THRESH].index)
print(f"Distinct norms ≥ {FREQ_THRESH} mentions: {len(valid_norms)}")

# 1) Slice to only high-frequency norms
hf_mentions = filtered[filtered['norm'].isin(valid_norms)]

# 2) Deduplicate to one row per norm
final = hf_mentions.drop_duplicates(subset=['norm'])
print(f"Final unique nodes: {len(final)}")

# ========== SAVE ==========
final.to_csv(OUTPUT_CSV, index=False)
print(f"Saved cleaned nodes to: {OUTPUT_CSV}")
