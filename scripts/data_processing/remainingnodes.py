import pandas as pd
import re
from datetime import datetime
import os

def manual_ner_analysis(articles_path="Articles/cleaned_articles_combined.csv", output_path="manual_ner_analysis_results.csv"):
    """
    Perform manual NER analysis to identify specific entities in articles dataset.
    
    Args:
        articles_path (str): Path to the articles CSV file
        output_path (str): Path to save the results CSV file
    
    Returns:
        pandas.DataFrame: Results dataframe with entity mentions
    """
    
    print("🔍 STARTING MANUAL NER ANALYSIS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Define entities with all their potential variants for better matching
    entity_data = [
        {
            'Normalized_Entity': 'Автодор',
            'Entity_Type': 'Organization',
            'Variants': [
                'Avtodorozhnaya Stroitelnaya Korporatsiya, LLC', 'Avtodorozhnaya Stroitelnaya Korporatsiya',
                'Автодор', 'Автодора', 'Автодору', 'компания Автодор', 'АО Автодор',
                'государственная компания Автодор', 'ГК Автодор'
            ]
        },
        {
            'Normalized_Entity': 'принц Мухаммед бен Сальман Аль Сауд (MBS)',
            'Entity_Type': 'Person',
            'Variants': [
                'Mohammed bin Salman (MBS)', 'Mohammed bin Salman', 'MBS',
                'принц Мухаммед бен Сальман', 'Мухаммед бен Сальман', 'наследный принц Саудовской Аравии',
                'принца Мухаммеда бен Сальмана', 'принцу Мухаммеду бен Сальману',
                'наследный принц', 'кронпринц Саудовской Аравии'
            ]
        },
        {
            'Normalized_Entity': 'Александр Чоботов',
            'Entity_Type': 'Person',
            'Variants': [
                'Alexander Chobotov', 'Александр Чоботов', 'Александра Чоботова',
                'Александру Чоботову', 'Александром Чоботовым', 'об Александре Чоботове',
                'А. Чоботов', 'Чоботов'
            ]
        },
        {
            'Normalized_Entity': 'Рик Герсон',
            'Entity_Type': 'Person',
            'Variants': [
                'Rick Gerson', 'Рик Герсон', 'Рика Герсона', 'Рику Герсону',
                'Риком Герсоном', 'о Рике Герсоне', 'Р. Герсон', 'Герсон'
            ]
        },
        {
            'Normalized_Entity': 'Русэнергосбыт',
            'Entity_Type': 'Organization',
            'Variants': [
                'Rusenergosbyt', 'Русэнергосбыт', 'Русэнергосбыта', 'Русэнергосбыту',
                'компания Русэнергосбыт', 'ООО Русэнергосбыт', 'группа Русэнергосбыт'
            ]
        },
        {
            'Normalized_Entity': 'Газпром Нефть Восток',
            'Entity_Type': 'Organization',
            'Variants': [
                'Gazpromneft-Vostok JV', 'Газпром Нефть Восток', 'Газпрома Нефть Восток',
                'Газпрому Нефть Восток', 'компания Газпром Нефть Восток',
                'СП Газпром Нефть Восток', 'совместное предприятие Газпром Нефть Восток'
            ]
        },
        {
            'Normalized_Entity': 'NIIF',
            'Entity_Type': 'Organization',
            'Variants': [
                'National Investment and Infrastructure Fund (NIIF)', 'National Investment and Infrastructure Fund',
                'NIIF', 'НИФ', 'Национальный инвестиционный и инфраструктурный фонд',
                'Национальный инвестиционный фонд', 'инвестиционный фонд NIIF'
            ]
        },
        {
            'Normalized_Entity': 'Евразийский банк развития (EDB)',
            'Entity_Type': 'Organization',
            'Variants': [
                'Eurasian Development Bank (EDB)', 'Eurasian Development Bank', 'EDB', 'ЕБР',
                'Евразийский банк развития', 'Евразийского банка развития', 'банк ЕБР'
            ]
        },
        {
            'Normalized_Entity': 'ЗапСибНефтехим',
            'Entity_Type': 'Organization',
            'Variants': [
                'ZapSibNeftekhim', 'ЗапСибНефтехим', 'ЗапСибНефтехима', 'ЗапСибНефтехиму',
                'компания ЗапСибНефтехим', 'завод ЗапСибНефтехим', 'комплекс ЗапСибНефтехим'
            ]
        },
        {
            'Normalized_Entity': 'Türkiye Wealth Fund (TWF)',
            'Entity_Type': 'Organization',
            'Variants': [
                'Türkiye Wealth Fund (TWF)', 'Türkiye Wealth Fund', 'TWF',
                'Турецкий фонд благосостояния', 'Фонд благосостояния Турции',
                'суверенный фонд Турции', 'турецкий суверенный фонд'
            ]
        },
        {
            'Normalized_Entity': 'Saudi Basic Industries Corporation (SABIC)',
            'Entity_Type': 'Organization',
            'Variants': [
                'Saudi Basic Industries Corporation (SABIC)', 'Saudi Basic Industries Corporation',
                'SABIC', 'САБИК', 'Саудовская корпорация базовых отраслей промышленности',
                'компания САБИК', 'корпорация САБИК'
            ]
        },
        {
            'Normalized_Entity': 'Шон Глобек',
            'Entity_Type': 'Person',
            'Variants': [
                'Sean Glodek', 'Шон Глобек', 'Шона Глобека', 'Шону Глобеку',
                'Шоном Глобеком', 'Ш. Глобек', 'Глобек'
            ]
        },
        {
            'Normalized_Entity': 'Российско-французский инвестиционный фонд',
            'Entity_Type': 'Organization',
            'Variants': [
                'Russia-France Investment Fund (RFIF)', 'Russia-France Investment Fund',
                'Российско-французский инвестиционный фонд', 'РФИФ',
                'российско-французский фонд', 'фонд РФИФ'
            ]
        },
        {
            'Normalized_Entity': 'Тадаши Маэда',
            'Entity_Type': 'Person',
            'Variants': [
                'Tadashi Maeda', 'Тадаши Маэда', 'Тадаши Маэды', 'Тадаши Маэде',
                'Т. Маэда', 'Маэда'
            ]
        },
        {
            'Normalized_Entity': 'принц Бандар бен Султан',
            'Entity_Type': 'Person',
            'Variants': [
                'Prince Bandar bin Sultan', 'принц Бандар бен Султан', 'принца Бандара бен Султана',
                'принцу Бандару бен Султан', 'Бандар бен Султан', 'принц Бандар'
            ]
        },
        {
            'Normalized_Entity': 'Анвар Ибрагим',
            'Entity_Type': 'Person',
            'Variants': [
                'Anwar Ibrahim', 'Анвар Ибрагим', 'Анвара Ибрагима', 'Анвару Ибрагиму',
                'А. Ибрагим', 'Ибрагим'
            ]
        },
        {
            'Normalized_Entity': 'Всемирный экономический форум',
            'Entity_Type': 'Organization',
            'Variants': [
                'World Economic Forum', 'Всемирный экономический форум', 'ВЭФ',
                'Давосский форум', 'форум в Давосе', 'экономический форум в Давосе'
            ]
        },
        {
            'Normalized_Entity': 'Чон Сук Чой',
            'Entity_Type': 'Person',
            'Variants': [
                'Chong-Suk Choi', 'Чон Сук Чой', 'Чон Сука Чоя', 'Чон Суку Чою',
                'Чой', 'Ч.С. Чой'
            ]
        },
        {
            'Normalized_Entity': 'Государственная корпорация по инвестициям капитала (SCIC)',
            'Entity_Type': 'Organization',
            'Variants': [
                'State Capital Investment Corporation (SCIC)', 'State Capital Investment Corporation',
                'SCIC', 'Государственная корпорация по инвестициям капитала',
                'корпорация SCIC', 'вьетнамская SCIC'
            ]
        },
        {
            'Normalized_Entity': 'JPMorgan Chase & Co.',
            'Entity_Type': 'Organization',
            'Variants': [
                'JPMorgan Chase & Co.', 'JPMorgan Chase', 'JPMorgan',
                'Джей Пи Морган Чейз', 'ДжейПиМорган', 'банк JPMorgan'
            ]
        },
        {
            'Normalized_Entity': 'BlackRock',
            'Entity_Type': 'Organization',
            'Variants': [
                'BlackRock', 'БлэкРок', 'компания BlackRock', 'фонд BlackRock'
            ]
        },
        {
            'Normalized_Entity': 'KIA',
            'Entity_Type': 'Organization',
            'Variants': [
                'Korea Investment Corporation', 'KIA', 'КИА',
                'Корейская инвестиционная корпорация', 'корпорация KIA'
            ]
        },
        {
            'Normalized_Entity': 'Mitsui & Co.',
            'Entity_Type': 'Organization',
            'Variants': [
                'Mitsui & Co.', 'Mitsui', 'Мицуи энд Ко', 'компания Мицуи',
                'корпорация Мицуи', 'группа Мицуи'
            ]
        },
        {
            'Normalized_Entity': 'Фонд национального благосостояния',
            'Entity_Type': 'Organization',
            'Variants': [
                'National Wealth Fund', 'Фонд национального благосостояния', 'ФНБ',
                'российский ФНБ', 'национальный фонд благосостояния'
            ]
        }
        # Adding more entities would follow the same pattern...
    ]
    
    # Read the articles dataset
    try:
        if not os.path.exists(articles_path):
            raise FileNotFoundError(f"Articles file not found at: {articles_path}")
        
        df_articles = pd.read_csv(articles_path)
        print(f"✓ Successfully loaded articles dataset: {articles_path}")
        print(f"✓ Total articles: {len(df_articles):,}")
        print(f"✓ Columns: {list(df_articles.columns)}")
        
    except Exception as e:
        print(f"❌ Error loading articles dataset: {e}")
        return None
    
    # Prepare results list
    results = []
    
    # Context window size (characters before and after the match)
    context_window = 50
    
    # Precompile regex patterns for all variants (case-insensitive, word boundaries)
    for entity in entity_data:
        entity['Compiled_Patterns'] = []
        for variant in entity['Variants']:
            # Use word boundaries for better matching, escape special regex characters
            pattern = r'\b' + re.escape(variant) + r'\b'
            try:
                entity['Compiled_Patterns'].append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                # Fallback for problematic patterns
                entity['Compiled_Patterns'].append(re.compile(re.escape(variant), re.IGNORECASE))
    
    print(f"\n🔍 Analyzing {len(entity_data)} entities across {len(df_articles)} articles...")
    
    # Process each article
    for idx, row in df_articles.iterrows():
        if idx % 1000 == 0:
            print(f"   Processing article {idx+1:,} of {len(df_articles):,}")
        
        article_id = row.get('article_id', f'article_{idx}')
        date = row.get('date', '')
        source = row.get('source', '')
        
        # Combine title and body for text analysis
        title_text = str(row.get('title', ''))
        body_text = str(row.get('body', ''))
        full_text = f"{title_text} {body_text}"
        
        # Skip if no meaningful text
        if len(full_text.strip()) < 10:
            continue
        
        text_len = len(full_text)
        
        # Search for each entity and its variants
        for entity in entity_data:
            normalized_entity = entity['Normalized_Entity']
            entity_type = entity['Entity_Type']
            
            entity_mentions = []
            
            # Search all variant patterns
            for pattern in entity['Compiled_Patterns']:
                for match in pattern.finditer(full_text):
                    start, end = match.start(), match.end()
                    matched_text = match.group()
                    
                    # Extract context around the match
                    context_start = max(0, start - context_window)
                    context_end = min(text_len, end + context_window)
                    context_text = full_text[context_start:context_end].strip()
                    
                    # Clean up context text
                    context_text = re.sub(r'\s+', ' ', context_text)  # Remove extra whitespace
                    context_text = context_text.replace('\n', ' ').replace('\t', ' ')
                    
                    entity_mentions.append({
                        'matched_text': matched_text,
                        'context': context_text,
                        'position': (start, end)
                    })
            
            # Add results for this entity in this article
            if entity_mentions:
                # Remove duplicate mentions at the same position
                unique_mentions = []
                seen_positions = set()
                for mention in entity_mentions:
                    if mention['position'] not in seen_positions:
                        unique_mentions.append(mention)
                        seen_positions.add(mention['position'])
                
                # Create one entry per unique mention
                for mention in unique_mentions:
                    results.append({
                        'Article_ID': article_id,
                        'Date': date,
                        'Source': source,
                        'Entity': normalized_entity,
                        'Entity_Type': entity_type,
                        'Occurrences': 1,
                        'Context_Text': mention['context']
                    })
    
    # Create DataFrame from results
    if results:
        results_df = pd.DataFrame(results)
        
        # Sort by article ID and entity for better organization
        results_df = results_df.sort_values(['Article_ID', 'Entity', 'Date'])
        
        # Save results to CSV
        results_df.to_csv(output_path, index=False, encoding='utf-8')
        
        # Print summary statistics
        print(f"\n{'='*60}")
        print(f"MANUAL NER ANALYSIS RESULTS")
        print(f"{'='*60}")
        print(f"✓ Total entity mentions found: {len(results_df):,}")
        print(f"✓ Unique entities found: {results_df['Entity'].nunique()}")
        print(f"✓ Articles with mentions: {results_df['Article_ID'].nunique()}")
        print(f"✓ Results saved to: {output_path}")
        
        # Show top entities by frequency
        print(f"\n📊 TOP 10 MOST MENTIONED ENTITIES:")
        top_entities = results_df['Entity'].value_counts().head(10)
        for i, (entity, count) in enumerate(top_entities.items(), 1):
            print(f"{i:>2}. {entity}: {count} mentions")
        
        # Show entity type distribution
        print(f"\n📊 ENTITY TYPE DISTRIBUTION:")
        type_dist = results_df['Entity_Type'].value_counts()
        for entity_type, count in type_dist.items():
            print(f"   {entity_type}: {count} mentions")
        
        return results_df
        
    else:
        print(f"\n⚠️  No entity mentions found in the articles dataset")
        # Create empty DataFrame with correct structure
        empty_df = pd.DataFrame(columns=['Article_ID', 'Date', 'Source', 'Entity', 'Entity_Type', 'Occurrences', 'Context_Text'])
        empty_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✓ Empty results file created: {output_path}")
        return empty_df


def analyze_ner_results(results_path="manual_ner_analysis_results.csv"):
    """
    Analyze the NER results and provide detailed statistics.
    """
    try:
        df = pd.read_csv(results_path)
        
        print(f"\n{'='*60}")
        print(f"DETAILED NER ANALYSIS REPORT")
        print(f"{'='*60}")
        
        # Overall statistics
        print(f"📈 OVERALL STATISTICS:")
        print(f"   Total mentions: {len(df):,}")
        print(f"   Unique entities: {df['Entity'].nunique()}")
        print(f"   Unique articles: {df['Article_ID'].nunique()}")
        print(f"   Unique sources: {df['Source'].nunique()}")
        
        # Entity frequency analysis
        print(f"\n📊 ENTITY FREQUENCY ANALYSIS:")
        entity_freq = df['Entity'].value_counts()
        print(f"   Most mentioned entity: {entity_freq.index[0]} ({entity_freq.iloc[0]} mentions)")
        print(f"   Average mentions per entity: {entity_freq.mean():.1f}")
        print(f"   Median mentions per entity: {entity_freq.median():.1f}")
        
        # Source analysis
        if 'Source' in df.columns and df['Source'].notna().any():
            print(f"\n📰 SOURCE ANALYSIS:")
            source_freq = df['Source'].value_counts().head(5)
            for source, count in source_freq.items():
                print(f"   {source}: {count} mentions")
        
        # Monthly analysis if dates are available
        if 'Date' in df.columns and df['Date'].notna().any():
            print(f"\n📅 TEMPORAL ANALYSIS:")
            try:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Month'] = df['Date'].dt.to_period('M')
                monthly_mentions = df['Month'].value_counts().sort_index().tail(6)
                for month, count in monthly_mentions.items():
                    print(f"   {month}: {count} mentions")
            except:
                print("   Could not analyze temporal patterns")
        
        return df
        
    except FileNotFoundError:
        print(f"❌ Results file not found: {results_path}")
        return None


# Main execution
if __name__ == "__main__":
    print("🚀 MANUAL NER ANALYSIS FOR SPECIFIED ENTITIES")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the manual NER analysis
    results_df = manual_ner_analysis(
        articles_path="Articles/cleaned_articles_combined.csv",
        output_path="manual_ner_analysis_results.csv"
    )
    
    if results_df is not None and len(results_df) > 0:
        # Analyze the results
        analyze_ner_results("manual_ner_analysis_results.csv")
        
        print(f"\n✅ ANALYSIS COMPLETED SUCCESSFULLY!")
        print(f"✓ Results file: 'manual_ner_analysis_results.csv'")
        print(f"✓ Dataset structure: Article_ID, Date, Source, Entity, Entity_Type, Occurrences, Context_Text")
    else:
        print(f"\n⚠️  Analysis completed but no entity mentions were found")
    
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
