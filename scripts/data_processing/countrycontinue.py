import pandas as pd
import re
from collections import defaultdict

def clean_foreign_locations_from_dataset(input_file, output_file, min_occurrences=5):
    """
    Remove all foreign countries and ambiguous geopolitical terms from the dataset
    """
    print("Loading dataset...")
    df = pd.read_csv(input_file)
    print(f"Initial dataset size: {len(df):,} rows")
    print(f"Unique entities before filtering: {df['Entity'].nunique():,}")
    
    # Comprehensive list of foreign countries, regions, and ambiguous terms to exclude
    FOREIGN_LOCATIONS = {
        # Middle East and Arab countries
        'эр-рияд', 'эр-рияда', 'эр-рияду', 'эр-риядом', 'эр-рияде',
        'ближний восток', 'ближнем востоке', 'ближнего востока', 'ближнему востоку',
        'средний восток', 'среднем востоке', 'среднего востока',
        'саудовская аравия', 'саудовской аравии', 'саудовскую аравию',
        'оаэ', 'эмираты', 'эмиратов', 'эмиратам', 'эмиратами',
        'катар', 'катара', 'катару', 'катаром', 'катаре',
        'кувейт', 'кувейта', 'кувейту', 'кувейтом', 'кувейте',
        'бахрейн', 'бахрейна', 'бахрейну', 'бахрейном', 'бахрейне',
        'оман', 'омана', 'оману', 'оманом', 'омане',
        'йемен', 'йемена', 'йемену', 'йеменом', 'йемене',
        'ирак', 'ирака', 'ираку', 'ираком', 'ираке',
        'иран', 'ирана', 'ирану', 'ираном', 'иране',
        'сирия', 'сирии', 'сирию', 'сирией', 'сирии',
        'ливан', 'ливана', 'ливану', 'ливаном', 'ливане',
        'иордания', 'иордании', 'иорданию', 'иорданией',
        'израиль', 'израиля', 'израилю', 'израилем', 'израиле',
        'палестина', 'палестины', 'палестину', 'палестиной', 'палестине',
        'дубай', 'дубая', 'дубаю', 'дубаем', 'дубае',
        'абу-даби',
        
        # Europe and European countries
        'европа', 'европы', 'европе', 'европой', 'европу',
        'евросоюз', 'евросоюза', 'евросоюзу', 'евросоюзом', 'евросоюзе',
        'великобритания', 'великобритании', 'великобританию', 'великобританией',
        'британия', 'британии', 'британию', 'британией',
        'англия', 'англии', 'англию', 'англией',
        'шотландия', 'шотландии', 'шотландию', 'шотландией',
        'уэльс', 'уэльса', 'уэльсу', 'уэльсом', 'уэльсе',
        'ирландия', 'ирландии', 'ирландию', 'ирландией',
        'франция', 'франции', 'францию', 'францией',
        'германия', 'германии', 'германию', 'германией',
        'италия', 'италии', 'италию', 'италией',
        'испания', 'испании', 'испанию', 'испанией',
        'португалия', 'португалии', 'португалию', 'португалией',
        'нидерланды', 'нидерландов', 'нидерландам', 'нидерландами',
        'голландия', 'голландии', 'голландию', 'голландией',
        'бельгия', 'бельгии', 'бельгию', 'бельгией',
        'люксембург', 'люксембурга', 'люксембургу', 'люксембургом',
        'австрия', 'австрии', 'австрию', 'австрией',
        'швейцария', 'швейцарии', 'швейцарию', 'швейцарией',
        'швеция', 'швеции', 'швецию', 'швецией',
        'норвегия', 'норвегии', 'норвегию', 'норвегией',
        'дания', 'дании', 'данию', 'данией',
        'финляндия', 'финляндии', 'финляндию', 'финляндией',
        'исландия', 'исландии', 'исландию', 'исландией',
        'польша', 'польши', 'польшу', 'польшей',
        'чехия', 'чехии', 'чехию', 'чехией',
        'словакия', 'словакии', 'словакию', 'словакией',
        'венгрия', 'венгрии', 'венгрию', 'венгрией',
        'румыния', 'румынии', 'румынию', 'румынией',
        'болгария', 'болгарии', 'болгарию', 'болгарией',
        'греция', 'греции', 'грецию', 'грецией',
        'кипр', 'кипра', 'кипру', 'кипром', 'кипре',
        'мальта', 'мальты', 'мальту', 'мальтой', 'мальте',
        'эстония', 'эстонии', 'эстонию', 'эстонией',
        'латвия', 'латвии', 'латвию', 'латвией',
        'литва', 'литвы', 'литву', 'литвой', 'литве',
        'сербия', 'сербии', 'сербию', 'сербией',
        'хорватия', 'хорватии', 'хорватию', 'хорватией',
        'словения', 'словении', 'словению', 'словенией',
        'босния', 'боснии', 'боснию', 'боснией',
        'черногория', 'черногории', 'черногорию', 'черногорией',
        'македония', 'македонии', 'македонию', 'македонией',
        'албания', 'албании', 'албанию', 'албанией',
        'давос', 'давоса', 'давосу', 'давосом', 'давосе',
        
        # Americas
        'сша', 'соединенные штаты', 'соединенных штатов', 'соединенным штатам',
        'америка', 'америки', 'америке', 'америкой', 'америку',
        'канада', 'канады', 'канаде', 'канадой', 'канаду',
        'мексика', 'мексики', 'мексике', 'мексикой', 'мексику',
        'бразилия', 'бразилии', 'бразилию', 'бразилией',
        'аргентина', 'аргентины', 'аргентине', 'аргентину', 'аргентиной',
        'чили', 'чили',
        'перу', 'перу',
        'колумбия', 'колумбии', 'колумбию', 'колумбией',
        'венесуэла', 'венесуэлы', 'венесуэле', 'венесуэлу', 'венесуэлой',
        'эквадор', 'эквадора', 'эквадору', 'эквадором', 'эквадоре',
        'боливия', 'боливии', 'боливию', 'боливией',
        'парагвай', 'парагвая', 'парагваю', 'парагваем', 'парагвае',
        'уругвай', 'уругвая', 'уругваю', 'уругваем', 'уругвае',
        
        # Asia-Pacific
        'китай', 'китая', 'китаю', 'китаем', 'китае', 'кнр',
        'япония', 'японии', 'японию', 'японией',
        'южная корея', 'южной кореи', 'южную корею', 'южной кореей',
        'северная корея', 'северной кореи', 'северную корею', 'северной кореей',
        'индия', 'индии', 'индию', 'индией',
        'пакистан', 'пакистана', 'пакистану', 'пакистаном', 'пакистане',
        'бангладеш', 'бангладеша', 'бангладешу', 'бангладешем', 'бангладеше',
        'шри-ланка', 'шри-ланки', 'шри-ланке', 'шри-ланку', 'шри-ланкой',
        'мьянма', 'мьянмы', 'мьянме', 'мьянму', 'мьянмой',
        'таиланд', 'таиланда', 'таиланду', 'таиландом', 'таиланде',
        'вьетнам', 'вьетнама', 'вьетнаму', 'вьетнамом', 'вьетнаме',
        'камбоджа', 'камбоджи', 'камбодже', 'камбоджу', 'камбоджей',
        'лаос', 'лаоса', 'лаосу', 'лаосом', 'лаосе',
        'малайзия', 'малайзии', 'малайзию', 'малайзией',
        'сингапур', 'сингапура', 'сингапуру', 'сингапуром', 'сингапуре',
        'индонезия', 'индонезии', 'индонезию', 'индонезией',
        'филиппины', 'филиппин', 'филиппинам', 'филиппинами', 'филиппинах',
        'австралия', 'австралии', 'австралию', 'австралией',
        'новая зеландия', 'новой зеландии', 'новую зеландию', 'новой зеландией',
        
        # Africa
        'африка', 'африки', 'африке', 'африкой', 'африку',
        'египет', 'египта', 'египту', 'египтом', 'египте',
        'ливия', 'ливии', 'ливию', 'ливией',
        'алжир', 'алжира', 'алжиру', 'алжиром', 'алжире',
        'марокко', 'марокко',
        'тунис', 'туниса', 'тунису', 'тунисом', 'тунисе',
        'судан', 'судана', 'судану', 'суданом', 'судане',
        'эфиопия', 'эфиопии', 'эфиопию', 'эфиопией',
        'кения', 'кении', 'кению', 'кенией',
        'танзания', 'танзании', 'танзанию', 'танзанией',
        'уганда', 'уганды', 'уганде', 'уганду', 'угандой',
        'руанда', 'руанды', 'руанде', 'руанду', 'руандой',
        'бурунди', 'бурунди',
        'замбия', 'замбии', 'замбию', 'замбией',
        'зимбабве', 'зимбабве',
        'ботсвана', 'ботсваны', 'ботсване', 'ботсвану', 'ботсваной',
        'намибия', 'намибии', 'намибию', 'намибией',
        'южная африка', 'южной африки', 'южную африку', 'южной африкой',
        'юар', 'юар',
        'мозамбик', 'мозамбика', 'мозамбику', 'мозамбиком', 'мозамбике',
        'ангола', 'анголы', 'анголе', 'анголу', 'анголой',
        'конго', 'конго',
        'камерун', 'камеруна', 'камеруну', 'камеруном', 'камеруне',
        'нигерия', 'нигерии', 'нигерию', 'нигерией',
        'гана', 'ганы', 'гане', 'гану', 'ганой',
        'кот-д\'ивуар', 'кот-д\'ивуара', 'кот-д\'ивуару', 'кот-д\'ивуаром',
        'сенегал', 'сенегала', 'сенегалу', 'сенегалом', 'сенегале',
        'мали', 'мали',
        'буркина-фасо', 'буркина-фасо',
        'нигер', 'нигера', 'нигеру', 'нигером', 'нигере',
        'чад', 'чада', 'чаду', 'чадом', 'чаде',
        
        # Other regions and ambiguous terms
        'океания', 'океании', 'океанию', 'океанией',
        'антарктида', 'антарктиды', 'антарктиде', 'антарктиду', 'антарктидой',
        'арктика', 'арктики', 'арктике', 'арктику', 'арктикой',
        'запад', 'запада', 'западу', 'западом', 'западе',
        'восток', 'востока', 'востоку', 'востоком', 'востоке',
        'север', 'севера', 'северу', 'севером', 'севере',
        'юг', 'юга', 'югу', 'югом', 'юге',
        
        # Former Soviet states (non-Russian)
        'украина', 'украины', 'украине', 'украину', 'украиной',
        'беларусь', 'белоруссия', 'белоруссии', 'белоруссию', 'белоруссией',
        'казахстан', 'казахстана', 'казахстану', 'казахстаном', 'казахстане',
        'узбекистан', 'узбекистана', 'узбекистану', 'узбекистаном', 'узбекистане',
        'таджикистан', 'таджикистана', 'таджикистану', 'таджикистаном', 'таджикистане',
        'киргизия', 'киргизии', 'киргизию', 'киргизией',
        'туркменистан', 'туркменистана', 'туркменистану', 'туркменистаном', 'туркменистане',
        'азербайджан', 'азербайджана', 'азербайджану', 'азербайджаном', 'азербайджане',
        'армения', 'армении', 'армению', 'арменией',
        'грузия', 'грузии', 'грузию', 'грузией',
        'молдова', 'молдовы', 'молдове', 'молдову', 'молдовой',
        'эстония', 'эстонии', 'эстонию', 'эстонией',
        'латвия', 'латвии', 'латвию', 'латвией',
        'литва', 'литвы', 'литве', 'литву', 'литвой',
        
        # Turkish region
        'турция', 'турции', 'турцию', 'турцией',
        
        # Remove ambiguous political terms that aren't specific locations
        'кремль', 'кремля', 'кремлю', 'кремлем', 'кремле'  # Too generic/political
    }
    
    def normalize_entity_name(name):
        """Normalize entity name for matching"""
        name = str(name).lower()
        name = re.sub(r'[().,;:!?"\'\-]', '', name)
        name = name.strip()
        return name
    
    def is_foreign_location(entity, entity_type):
        """Check if entity is a foreign location that should be excluded"""
        if entity_type != 'LOC':
            return False  # Keep all non-location entities
        
        entity_norm = normalize_entity_name(entity)
        return entity_norm in FOREIGN_LOCATIONS
    
    # Filter out foreign locations
    print("Filtering out foreign locations...")
    initial_count = len(df)
    df_filtered = df[~df.apply(lambda row: is_foreign_location(row['Entity'], row['Entity_Type']), axis=1)].copy()
    print(f"Removed {initial_count - len(df_filtered):,} foreign location mentions")
    
    # Recalculate occurrences after filtering
    print("Recalculating entity occurrences...")
    entity_article_counts = df_filtered.groupby(['Entity', 'Entity_Type'])['Article_ID'].nunique().reset_index()
    entity_article_counts = entity_article_counts.rename(columns={'Article_ID': 'New_Occurrences'})
    
    # Filter entities with minimum occurrences
    entities_to_keep = entity_article_counts[entity_article_counts['New_Occurrences'] >= min_occurrences]
    print(f"Entities with >= {min_occurrences} occurrences: {len(entities_to_keep):,}")
    
    # Create set for faster lookup
    keep_entities = set(zip(entities_to_keep['Entity'], entities_to_keep['Entity_Type']))
    
    # Filter main dataset
    df_final = df_filtered[df_filtered[['Entity', 'Entity_Type']].apply(tuple, axis=1).isin(keep_entities)].copy()
    
    # Update occurrence counts
    df_final = df_final.merge(
        entity_article_counts[['Entity', 'Entity_Type', 'New_Occurrences']], 
        on=['Entity', 'Entity_Type'], 
        how='left'
    )
    
    # Clean up columns
    if 'Occurrences' in df_final.columns:
        df_final = df_final.drop(columns=['Occurrences'])
    df_final = df_final.rename(columns={'New_Occurrences': 'Occurrences'})
    
    # Sort by occurrences
    df_final = df_final.sort_values(['Occurrences', 'Entity'], ascending=[False, True])
    df_final = df_final.reset_index(drop=True)
    
    # Save cleaned dataset
    df_final.to_csv(output_file, index=False)
    
    # Print summary statistics
    print(f"\n=== FINAL FILTERING SUMMARY ===")
    print(f"Original dataset: {len(df):,} rows")
    print(f"Final dataset: {len(df_final):,} rows")
    print(f"Reduction: {((len(df) - len(df_final)) / len(df) * 100):.1f}%")
    print(f"Unique entities before: {df['Entity'].nunique():,}")
    print(f"Unique entities after: {df_final['Entity'].nunique():,}")
    
    print(f"\nEntity type distribution:")
    print(df_final['Entity_Type'].value_counts())
    
    # Show top entities
    print(f"\nTop 20 most frequent entities:")
    top_entities = df_final.groupby('Entity')['Occurrences'].first().sort_values(ascending=False).head(20)
    for entity, count in top_entities.items():
        print(f"{entity}: {count:,}")
    
    # Show location filtering results
    print(f"\n=== LOCATION FILTERING VERIFICATION ===")
    location_entities = df_final[df_final['Entity_Type'] == 'LOC']
    if len(location_entities) > 0:
        print(f"Remaining location entities: {location_entities['Entity'].nunique():,}")
        print("\nTop 15 remaining locations (should all be Russian):")
        top_locations = location_entities.groupby('Entity')['Occurrences'].first().sort_values(ascending=False).head(15)
        for location, count in top_locations.items():
            print(f"  {location}: {count:,}")
    
    print(f"\nFinal dataset saved to: {output_file}")
    return df_final

# Run the filtering process
if __name__ == "__main__":
    cleaned_df = clean_foreign_locations_from_dataset(
        input_file='ner_entity_dataset_russian_locations_only.csv',  # Input from previous step
        output_file='ner_entity_dataset_truly_russian_only.csv',     # New output file
        min_occurrences=5
    )
    
    print("\n=== VERIFICATION CHECK ===")
    print("Checking if problematic entities were removed:")
    
    # Check if the problematic entities from your example are gone
    problematic_entities = ['Эр-Рияде', 'Европе', 'Великобритании', 'Ближнем Востоке', 
                          'Ближнего Востока', 'ДАВОС', 'Аргентине', 'Запад']
    
    for entity in problematic_entities:
        if entity in cleaned_df['Entity'].values:
            print(f"❌ {entity}: Still present")
        else:
            print(f"✅ {entity}: Successfully removed")
