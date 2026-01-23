import pandas as pd
import re

# Load the dataset
df = pd.read_csv('ner_entity_dataset_superclean_lt50.csv')

print(f"Initial dataset size: {len(df):,} rows")
print(f"Unique entities before filtering: {df['Entity'].nunique():,}")

# Comprehensive keyword lists for context analysis
SANCTIONS_KEYWORDS = [
    'санкции', 'санкций', 'санкциям', 'санкциями', 'санкциях',
    'ограничения', 'ограничений', 'ограничениям', 'ограничениями', 'ограничениях',
    'запрет', 'запрета', 'запрету', 'запретом', 'запрете', 'запреты', 'запретов',
    'эмбарго', 'блокировка', 'блокировки', 'блокировке', 'блокировку', 'блокировкой',
    'заморозка', 'заморозки', 'заморозке', 'заморозку', 'заморозкой',
    'замораживание', 'замораживания', 'замораживанию', 'замораживанием',
    'арест', 'ареста', 'аресту', 'арестом', 'аресте', 'арестованы', 'арестован',
    'конфискация', 'конфискации', 'конфискацию', 'конфискацией',
    'изъятие', 'изъятия', 'изъятию', 'изъятием', 'изъятии',
    'черный список', 'черного списка', 'черному списку', 'черным списком',
    'персональные санкции', 'секторальные санкции', 'экономические санкции',
    'финансовые санкции', 'торговые санкции', 'банковские санкции',
    'sanctions', 'embargo', 'restrictions', 'blacklist', 'freeze', 'frozen',
    'blocked', 'prohibited', 'banned', 'restricted', 'sanctioned'
]

DIPLOMACY_KEYWORDS = [
    'дипломатия', 'дипломатии', 'дипломатию', 'дипломатией',
    'переговоры', 'переговоров', 'переговорам', 'переговорами', 'переговорах',
    'диалог', 'диалога', 'диалогу', 'диалогом', 'диалоге',
    'консультации', 'консультаций', 'консультациям', 'консультациями', 'консультациях',
    'встреча', 'встречи', 'встрече', 'встречу', 'встречей', 'встречам',
    'саммит', 'саммита', 'саммиту', 'саммитом', 'саммите', 'саммиты',
    'форум', 'форума', 'форуму', 'форумом', 'форуме', 'форумы',
    'конференция', 'конференции', 'конференцию', 'конференцией',
    'соглашение', 'соглашения', 'соглашению', 'соглашением', 'соглашении',
    'договор', 'договора', 'договору', 'договором', 'договоре', 'договоры',
    'протокол', 'протокола', 'протоколу', 'протоколом', 'протоколе',
    'меморандум', 'меморандума', 'меморандуму', 'меморандумом', 'меморандуме',
    'дипломат', 'дипломата', 'дипломату', 'дипломатом', 'дипломате', 'дипломаты',
    'посол', 'посла', 'послу', 'послом', 'после', 'послы', 'послов',
    'посольство', 'посольства', 'посольству', 'посольством', 'посольстве',
    'консульство', 'консульства', 'консульству', 'консульством', 'консульстве',
    'министр иностранных дел', 'мид', 'внешняя политика', 'внешней политики',
    'международные отношения', 'международных отношений',
    'двусторонние отношения', 'двусторонних отношений',
    'многосторонние отношения', 'многосторонних отношений',
    'урегулирование', 'урегулирования', 'урегулированию', 'урегулированием',
    'разрешение конфликта', 'разрешения конфликта', 'мирное урегулирование',
    'дипломатический', 'дипломатическая', 'дипломатические', 'дипломатических',
    'diplomacy', 'diplomatic', 'negotiations', 'dialogue', 'summit', 'forum',
    'conference', 'agreement', 'treaty', 'protocol', 'memorandum', 'ambassador',
    'embassy', 'consulate', 'foreign minister', 'foreign policy', 'bilateral',
    'multilateral', 'international relations'
]

INVESTMENT_KEYWORDS = [
    'инвестиции', 'инвестиций', 'инвестициям', 'инвестициями', 'инвестициях',
    'инвестор', 'инвестора', 'инвестору', 'инвестором', 'инвесторе', 'инвесторы',
    'инвестирование', 'инвестирования', 'инвестированию', 'инвестированием',
    'инвестиционный', 'инвестиционная', 'инвестиционное', 'инвестиционные',
    'капитал', 'капитала', 'капиталу', 'капиталом', 'капитале',
    'капиталовложения', 'капиталовложений', 'капиталовложениям', 'капиталовложениями',
    'финансирование', 'финансирования', 'финансированию', 'финансированием',
    'фонд', 'фонда', 'фонду', 'фондом', 'фонде', 'фонды', 'фондов',
    'портфель', 'портфеля', 'портфелю', 'портфелем', 'портфеле',
    'акции', 'акций', 'акциям', 'акциями', 'акциях',
    'облигации', 'облигаций', 'облигациям', 'облигациями', 'облигациях',
    'ценные бумаги', 'ценных бумаг', 'ценным бумагам', 'ценными бумагами',
    'биржа', 'биржи', 'бирже', 'биржу', 'биржей', 'биржам',
    'рынок капитала', 'рынка капитала', 'рынку капитала', 'рынком капитала',
    'финансовый рынок', 'финансового рынка', 'финансовому рынку',
    'венчурный', 'венчурная', 'венчурное', 'венчурные', 'венчурного',
    'прямые инвестиции', 'прямых инвестиций', 'прямым инвестициям',
    'портфельные инвестиции', 'портфельных инвестиций',
    'иностранные инвестиции', 'иностранных инвестиций',
    'частные инвестиции', 'частных инвестиций', 'государственные инвестиции',
    'доходность', 'доходности', 'доходностью', 'прибыльность', 'прибыльности',
    'рентабельность', 'рентабельности', 'рентабельностью',
    'дивиденды', 'дивидендов', 'дивидендам', 'дивидендами',
    'проект', 'проекта', 'проекту', 'проектом', 'проекте', 'проекты', 'проектов',
    'сделка', 'сделки', 'сделке', 'сделку', 'сделкой', 'сделок',
    'слияние', 'слияния', 'слиянию', 'слиянием', 'слиянии',
    'поглощение', 'поглощения', 'поглощению', 'поглощением', 'поглощении',
    'приватизация', 'приватизации', 'приватизацию', 'приватизацией',
    'ipo', 'размещение', 'размещения', 'размещению', 'размещением',
    'листинг', 'листинга', 'листингу', 'листингом', 'листинге',
    'investment', 'investor', 'capital', 'funding', 'fund', 'portfolio',
    'stocks', 'shares', 'bonds', 'securities', 'market', 'exchange',
    'venture', 'private equity', 'hedge fund', 'mutual fund', 'etf',
    'dividend', 'yield', 'return', 'profit', 'revenue', 'deal', 'merger',
    'acquisition', 'ipo', 'listing', 'trading', 'financial'
]

# Combine all keywords
ALL_KEYWORDS = SANCTIONS_KEYWORDS + DIPLOMACY_KEYWORDS + INVESTMENT_KEYWORDS

# Function to check if context contains any of the keywords
def contains_relevant_keywords(context_text):
    if pd.isna(context_text):
        return False
    
    # Convert to lowercase for case-insensitive matching
    context_lower = str(context_text).lower()
    
    # Check if any keyword is present in the context
    for keyword in ALL_KEYWORDS:
        if keyword.lower() in context_lower:
            return True
    
    return False

# Apply the filter
print("Filtering entities based on context keywords...")
df_filtered = df[df['Context_Text'].apply(contains_relevant_keywords)].copy()

print(f"Entities after keyword filtering: {len(df_filtered):,} rows")
print(f"Unique entities after filtering: {df_filtered['Entity'].nunique():,}")
print(f"Reduction: {((len(df) - len(df_filtered)) / len(df) * 100):.1f}%")

# Save the filtered dataset
output_file = 'ner_entity_dataset_superclean_lt50_filtered.csv'
df_filtered.to_csv(output_file, index=False)

print(f"\nFiltered dataset saved to: {output_file}")

# Show statistics by entity type
print(f"\nEntity type distribution after filtering:")
print(df_filtered['Entity_Type'].value_counts())

# Show top entities by occurrence
print(f"\nTop 15 entities after filtering:")
top_entities = df_filtered.groupby('Entity')['Occurrences'].first().sort_values(ascending=False).head(15)
for entity, count in top_entities.items():
    print(f"  {entity}: {count:,} occurrences")

# Show some examples of filtered contexts
print(f"\nSample contexts that passed the filter:")
sample_contexts = df_filtered['Context_Text'].head(5)
for i, context in enumerate(sample_contexts, 1):
    # Show first 200 characters of context
    context_preview = str(context)[:200] + "..." if len(str(context)) > 200 else str(context)
    print(f"\n{i}. {context_preview}")

# Keyword frequency analysis
print(f"\nKeyword category analysis:")
sanctions_count = df_filtered[df_filtered['Context_Text'].str.contains('|'.join(SANCTIONS_KEYWORDS), case=False, na=False)].shape[0]
diplomacy_count = df_filtered[df_filtered['Context_Text'].str.contains('|'.join(DIPLOMACY_KEYWORDS), case=False, na=False)].shape[0]
investment_count = df_filtered[df_filtered['Context_Text'].str.contains('|'.join(INVESTMENT_KEYWORDS), case=False, na=False)].shape[0]

print(f"Entities with sanctions-related context: {sanctions_count:,}")
print(f"Entities with diplomacy-related context: {diplomacy_count:,}")
print(f"Entities with investment-related context: {investment_count:,}")
