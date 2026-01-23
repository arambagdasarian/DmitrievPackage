import pandas as pd
import re
from collections import defaultdict, Counter

def normalize_entity_name(entity):
    """
    Carefully normalize entity names while preserving distinct individuals
    """
    entity_clean = str(entity).strip()
    entity_lower = entity_clean.lower()
    
    # Remove extra whitespace and normalize punctuation
    entity_clean = re.sub(r'\s+', ' ', entity_clean)
    entity_clean = re.sub(r'[().,;:!?\"\']', '', entity_clean)
    entity_clean = entity_clean.strip()
    
    # Putin normalization - all forms to "Владимир Путин"
    putin_patterns = [
        r'^владимир путин$',
        r'^владимира путина$',
        r'^владимиром путиным$',
        r'^путин$',
        r'^путина$',
        r'^путину$',
        r'^путиным$',
        r'^путине$',
        r'^в\.?в\.? путин[а-я]*$',
        r'^владимир владимирович путин[а-я]*$',
        r'^владимиром владимировичем путиным$'
    ]
    
    for pattern in putin_patterns:
        if re.match(pattern, entity_lower):
            return 'Владимир Путин'
    
    # Dmitriev normalization - all forms to "Кирилл Дмитриев"
    dmitriev_patterns = [
        r'^кирилл дмитриев$',
        r'^кирилла дмитриева$',
        r'^кириллом дмитриевым$',
        r'^кириллу дмитриеву$',
        r'^кирилле дмитриеве$',
        r'^к\.? дмитриев[а-я]*$',
        r'^кирилл александрович дмитриев[а-я]*$'
    ]
    
    for pattern in dmitriev_patterns:
        if re.match(pattern, entity_lower):
            return 'Кирилл Дмитриев'
    
    # Trump normalization - all forms to "Дональд Трамп"
    trump_patterns = [
        r'^дональд трамп$',
        r'^дональда трампа$',
        r'^дональдом трампом$',
        r'^дональду трампу$',
        r'^дональде трампе$',
        r'^трамп$',
        r'^трампа$',
        r'^трампу$',
        r'^трампом$',
        r'^трампе$',
        r'^д\.? трамп[а-я]*$',
        r'^donald trump$'
    ]
    
    for pattern in trump_patterns:
        if re.match(pattern, entity_lower):
            return 'Дональд Трамп'
    
    # Lavrov normalization - all forms to "Сергей Лавров"
    lavrov_patterns = [
        r'^сергей лавров$',
        r'^сергея лаврова$',
        r'^сергеем лавровым$',
        r'^сергею лаврову$',
        r'^сергее лаврове$',
        r'^лавров$',
        r'^лаврова$',
        r'^лаврову$',
        r'^лавровым$',
        r'^лаврове$',
        r'^с\.? лавров[а-я]*$'
    ]
    
    for pattern in lavrov_patterns:
        if re.match(pattern, entity_lower):
            return 'Сергей Лавров'
    
    # Medvedev normalization - all forms to "Дмитрий Медведев"
    medvedev_patterns = [
        r'^дмитрий медведев$',
        r'^дмитрия медведева$',
        r'^дмитрием медведевым$',
        r'^дмитрию медведеву$',
        r'^дмитрии медведеве$',
        r'^медведев$',
        r'^медведева$',
        r'^медведеву$',
        r'^медведевым$',
        r'^медведеве$',
        r'^д\.? медведев[а-я]*$'
    ]
    
    for pattern in medvedev_patterns:
        if re.match(pattern, entity_lower):
            return 'Дмитрий Медведев'
    
    # Peskov normalization - all forms to "Дмитрий Песков"
    peskov_patterns = [
        r'^дмитрий песков$',
        r'^дмитрия пескова$',
        r'^дмитрием песковым$',
        r'^дмитрию пескову$',
        r'^дмитрии пескове$',
        r'^песков$',
        r'^пескова$',
        r'^пескову$',
        r'^песковым$',
        r'^пескове$',
        r'^д\.? песков[а-я]*$'
    ]
    
    for pattern in peskov_patterns:
        if re.match(pattern, entity_lower):
            return 'Дмитрий Песков'
    
    # Ushakov normalization - all forms to "Юрий Ушаков"
    ushakov_patterns = [
        r'^юрий ушаков$',
        r'^юрия ушакова$',
        r'^юрием ушаковым$',
        r'^юрию ушакову$',
        r'^юрии ушакове$',
        r'^ушаков$',
        r'^ушакова$',
        r'^ушакову$',
        r'^ушаковым$',
        r'^ушакове$',
        r'^ю\.? ушаков[а-я]*$'
    ]
    
    for pattern in ushakov_patterns:
        if re.match(pattern, entity_lower):
            return 'Юрий Ушаков'
    
    # Organization normalizations (only exact matches, not partial)
    org_normalizations = {
        # Banks
        'сбербанк': 'Сбербанк',
        'сбербанка': 'Сбербанк',
        'сбербанку': 'Сбербанк',
        'сбербанком': 'Сбербанк',
        'сбербанке': 'Сбербанк',
        'втб': 'ВТБ',
        'банк втб': 'ВТБ',
        'веб': 'ВЭБ',
        'внешэкономбанк': 'ВЭБ',
        
        # Telecom
        'мтс': 'МТС',
        'мобильные телесистемы': 'МТС',
        'ростелеком': 'Ростелеком',
        'ростелекома': 'Ростелеком',
        'ростелекому': 'Ростелеком',
        'ростелекомом': 'Ростелеком',
        'ростелекоме': 'Ростелеком',
        
        # Government bodies
        'госдума': 'Госдума',
        'госдумы': 'Госдума',
        'госдуме': 'Госдума',
        'госдуму': 'Госдума',
        'госдумой': 'Госдума',
        'государственная дума': 'Госдума',
        
        # International organizations
        'брикс': 'БРИКС',
        'brics': 'БРИКС'
    }
    
    if entity_lower in org_normalizations:
        return org_normalizations[entity_lower]
    
    # Return original if no normalization needed
    return entity_clean

def is_blacklisted_entity(entity, entity_type):
    """
    Enhanced blacklist based on context analysis
    """
    entity_lower = entity.lower().strip()
    
    # Expanded blacklist based on dataset analysis
    ENHANCED_BLACKLIST = {
        # Generic government terms
        'правительство', 'правительства', 'правительству', 'правительством', 'правительстве',
        'президент', 'президента', 'президенту', 'президентом', 'президенте',
        'министерство', 'министерства', 'министерству', 'министерством', 'министерстве',
        'минздрав', 'мид', 'минфин', 'минэкономразвития', 'минтранс', 'минобороны',
        'кремль', 'кремля', 'кремлю', 'кремлем', 'кремле',
        'администрация', 'администрации', 'администрацию', 'администрацией', 'администрации',
        
        # Generic titles and positions
        'директор', 'директора', 'директору', 'директором', 'директоре',
        'руководитель', 'руководителя', 'руководителю', 'руководителем', 'руководителе',
        'председатель', 'председателя', 'председателю', 'председателем', 'председателе',
        'заместитель', 'заместителя', 'заместителю', 'заместителем', 'заместителе',
        'министр', 'министра', 'министру', 'министром', 'министре',
        'губернатор', 'губернатора', 'губернатору', 'губернатором', 'губернаторе',
        'мэр', 'мэра', 'мэру', 'мэром', 'мэре',
        'глава', 'главы', 'главе', 'главу', 'главой',
        'руководство', 'руководства', 'руководству', 'руководством', 'руководстве',
        'начальник', 'начальника', 'начальнику', 'начальником', 'начальнике',
        'секретарь', 'секретаря', 'секретарю', 'секретарем', 'секретаре',
        
        # Generic organizational terms
        'агентство', 'агентства', 'агентству', 'агентством', 'агентстве',
        'служба', 'службы', 'службу', 'службой', 'службе',
        'комитет', 'комитета', 'комитету', 'комитетом', 'комитете',
        'департамент', 'департамента', 'департаменту', 'департаментом', 'департаменте',
        'управление', 'управления', 'управлению', 'управлением', 'управлении',
        'ведомство', 'ведомства', 'ведомству', 'ведомством', 'ведомстве',
        'корпорация', 'корпорации', 'корпорацию', 'корпорацией', 'корпорации',
        'холдинг', 'холдинга', 'холдингу', 'холдингом', 'холдинге',
        'группа компаний', 'группы компаний', 'группе компаний',
        
        # Generic company suffixes and terms
        'ооо', 'зао', 'оао', 'ао', 'пао', 'нко', 'ип',
        'ltd', 'llc', 'inc', 'corp', 'gmbh', 'sa', 'bv',
        'компания', 'компании', 'компанию', 'компанией', 'компании',
        'организация', 'организации', 'организацию', 'организацией', 'организации',
        'учреждение', 'учреждения', 'учреждению', 'учреждением', 'учреждении',
        'фирма', 'фирмы', 'фирму', 'фирмой', 'фирме',
        'предприятие', 'предприятия', 'предприятию', 'предприятием', 'предприятии',
        'структура', 'структуры', 'структуру', 'структурой', 'структуре',
        
        # Generic financial terms
        'банк', 'банка', 'банку', 'банком', 'банке',
        'биржа', 'биржи', 'бирже', 'биржей', 'биржу',
        'рынок', 'рынка', 'рынку', 'рынком', 'рынке',
        'экономика', 'экономики', 'экономике', 'экономикой', 'экономику',
        'финансы', 'финансов', 'финансам', 'финансами', 'финансах',
        'бюджет', 'бюджета', 'бюджету', 'бюджетом', 'бюджете',
        'инвестиции', 'инвестиций', 'инвестициям', 'инвестициями', 'инвестициях',
        
        # Generic locations and directions
        'центр', 'центра', 'центру', 'центром', 'центре',
        'регион', 'региона', 'региону', 'регионом', 'регионе',
        'область', 'области', 'область', 'областью', 'области',
        'район', 'района', 'району', 'районом', 'районе',
        'город', 'города', 'городу', 'городом', 'городе',
        'столица', 'столицы', 'столицу', 'столицей', 'столице',
        'территория', 'территории', 'территорию', 'территорией', 'территории',
        'зона', 'зоны', 'зону', 'зоной', 'зоне',
        'округ', 'округа', 'округу', 'округом', 'округе',
        
        # Generic time and event terms
        'год', 'года', 'году', 'годом', 'годе', 'лет', 'года',
        'время', 'времени', 'времени', 'временем', 'времени',
        'период', 'периода', 'периоду', 'периодом', 'периоде',
        'момент', 'момента', 'моменту', 'моментом', 'моменте',
        'день', 'дня', 'дню', 'днем', 'дне',
        'неделя', 'недели', 'неделе', 'неделю', 'неделей',
        'месяц', 'месяца', 'месяцу', 'месяцем', 'месяце',
        'событие', 'события', 'событию', 'событием', 'событии',
        'мероприятие', 'мероприятия', 'мероприятию', 'мероприятием', 'мероприятии',
        
        # Generic descriptive terms
        'вопрос', 'вопроса', 'вопросу', 'вопросом', 'вопросе',
        'проблема', 'проблемы', 'проблеме', 'проблему', 'проблемой',
        'ситуация', 'ситуации', 'ситуацию', 'ситуацией', 'ситуации',
        'процесс', 'процесса', 'процессу', 'процессом', 'процессе',
        'результат', 'результата', 'результату', 'результатом', 'результате',
        'решение', 'решения', 'решению', 'решением', 'решении',
        'развитие', 'развития', 'развитию', 'развитием', 'развитии',
        'система', 'системы', 'системе', 'систему', 'системой',
        'программа', 'программы', 'программе', 'программу', 'программой',
        'проект', 'проекта', 'проекту', 'проектом', 'проекте',
        'план', 'плана', 'плану', 'планом', 'плане',
        'стратегия', 'стратегии', 'стратегию', 'стратегией', 'стратегии',
        'политика', 'политики', 'политике', 'политику', 'политикой',
        'реформа', 'реформы', 'реформе', 'реформу', 'реформой',
        'изменение', 'изменения', 'изменению', 'изменением', 'изменении',
        'улучшение', 'улучшения', 'улучшению', 'улучшением', 'улучшении',
        
        # Generic action terms
        'работа', 'работы', 'работе', 'работу', 'работой',
        'деятельность', 'деятельности', 'деятельность', 'деятельностью', 'деятельности',
        'сотрудничество', 'сотрудничества', 'сотрудничеству', 'сотрудничеством', 'сотрудничестве',
        'взаимодействие', 'взаимодействия', 'взаимодействию', 'взаимодействием', 'взаимодействии',
        'отношения', 'отношений', 'отношениям', 'отношениями', 'отношениях',
        'связь', 'связи', 'связи', 'связью', 'связи',
        'контакт', 'контакта', 'контакту', 'контактом', 'контакте',
        'встреча', 'встречи', 'встрече', 'встречу', 'встречей',
        'переговоры', 'переговоров', 'переговорам', 'переговорами', 'переговорах',
        'обсуждение', 'обсуждения', 'обсуждению', 'обсуждением', 'обсуждении',
        'диалог', 'диалога', 'диалогу', 'диалогом', 'диалоге',
        'консультации', 'консультаций', 'консультациям', 'консультациями', 'консультациях',
        
        # Specific problematic entities from the dataset
        'спецпредставитель', 'представитель', 'представителя', 'представителю',
        'корреспондент', 'корреспондента', 'корреспонденту', 'корреспондентом',
        'журналист', 'журналиста', 'журналисту', 'журналистом', 'журналисте',
        'эксперт', 'эксперта', 'эксперту', 'экспертом', 'эксперте',
        'аналитик', 'аналитика', 'аналитику', 'аналитиком', 'аналитике',
        'специалист', 'специалиста', 'специалисту', 'специалистом', 'специалисте',
        'источник', 'источника', 'источнику', 'источником', 'источнике',
        'собеседник', 'собеседника', 'собеседнику', 'собеседником', 'собеседнике'
    }
    
    # Check if entity is blacklisted
    if entity_lower in ENHANCED_BLACKLIST:
        return True
    
    # Additional pattern-based blacklisting
    blacklist_patterns = [
        r'^визит[а-я]*\s',  # "визиту путина" etc.
        r'^\d+\s',          # Numbers with text
        r'^[а-я]+\s(путина|медведева|лаврова)$',  # "что-то + person name"
        r'^(пресс-)?секретар[ья]\s',  # Press secretary
        r'^помощник\s',     # Assistant
        r'^советник\s',     # Advisor
        r'^заместитель\s',  # Deputy
        r'^первый\s',       # First something
        r'^главный\s',      # Chief something
        r'^старший\s',      # Senior something
        r'^исполняющий\s',  # Acting something
        r'^временно\s',     # Temporarily something
    ]
    
    for pattern in blacklist_patterns:
        if re.match(pattern, entity_lower):
            return True
    
    return False

def advanced_entity_cleaning(input_file, output_file, min_occurrences=5):
    """
    Advanced entity cleaning with careful normalization and enhanced blacklisting
    """
    print("Loading dataset...")
    df = pd.read_csv(input_file)
    print(f"Initial dataset size: {len(df):,} rows")
    print(f"Unique entities before cleaning: {df['Entity'].nunique():,}")
    
    # Apply normalization
    print("\nNormalizing entity names...")
    df['Entity_normalized'] = df['Entity'].apply(normalize_entity_name)
    
    # Remove blacklisted entities
    print("Removing blacklisted entities...")
    initial_count = len(df)
    df_filtered = df[~df.apply(lambda row: is_blacklisted_entity(row['Entity_normalized'], row['Entity_Type']), axis=1)].copy()
    removed_count = initial_count - len(df_filtered)
    print(f"Removed {removed_count:,} blacklisted entity mentions")
    
    # Recalculate occurrences for normalized entities
    print("Recalculating entity occurrences...")
    entity_article_counts = df_filtered.groupby(['Entity_normalized', 'Entity_Type'])['Article_ID'].nunique().reset_index()
    entity_article_counts = entity_article_counts.rename(columns={'Article_ID': 'New_Occurrences'})
    
    # Filter entities with minimum occurrences
    entities_to_keep = entity_article_counts[entity_article_counts['New_Occurrences'] >= min_occurrences]
    print(f"Entities with >= {min_occurrences} occurrences: {len(entities_to_keep):,}")
    
    # Create set for faster lookup
    keep_entities = set(zip(entities_to_keep['Entity_normalized'], entities_to_keep['Entity_Type']))
    
    # Filter main dataset
    df_final = df_filtered[df_filtered[['Entity_normalized', 'Entity_Type']].apply(tuple, axis=1).isin(keep_entities)].copy()
    
    # Update occurrence counts
    df_final = df_final.merge(
        entity_article_counts[['Entity_normalized', 'Entity_Type', 'New_Occurrences']], 
        on=['Entity_normalized', 'Entity_Type'], 
        how='left'
    )
    
    # Clean up columns
    df_final = df_final.drop(columns=['Entity', 'Occurrences'])
    df_final = df_final.rename(columns={'Entity_normalized': 'Entity', 'New_Occurrences': 'Occurrences'})
    
    # Reorder columns
    columns_order = ['Article_ID', 'Date', 'Source', 'Entity', 'Entity_Type', 'Occurrences', 'Context_Text']
    df_final = df_final[columns_order]
    
    # Sort by occurrences
    df_final = df_final.sort_values(['Occurrences', 'Entity'], ascending=[False, True])
    df_final = df_final.reset_index(drop=True)
    
    # Save cleaned dataset
    df_final.to_csv(output_file, index=False)
    
    # Print summary statistics
    print(f"\n=== FINAL CLEANING SUMMARY ===")
    print(f"Original dataset: {len(df):,} rows")
    print(f"Final dataset: {len(df_final):,} rows")
    print(f"Reduction: {((len(df) - len(df_final)) / len(df) * 100):.1f}%")
    print(f"Unique entities before: {df['Entity'].nunique():,}")
    print(f"Unique entities after: {df_final['Entity'].nunique():,}")
    
    print(f"\nEntity type distribution:")
    print(df_final['Entity_Type'].value_counts())
    
    print(f"\nTop 20 most frequent entities after normalization:")
    top_entities = df_final.groupby('Entity')['Occurrences'].first().sort_values(ascending=False).head(20)
    for entity, count in top_entities.items():
        print(f"{entity}: {count:,}")
    
    # Show normalization examples
    print(f"\n=== NORMALIZATION EXAMPLES ===")
    
    # Putin variants
    putin_variants = df[df['Entity'].str.contains('путин', case=False, na=False)]['Entity'].value_counts()
    if len(putin_variants) > 0:
        print("Putin variants found:")
        for entity, count in putin_variants.head(10).items():
            print(f"  {entity}: {count:,}")
    
    # RDIF/Fund variants
    fund_variants = df[df['Entity'].str.contains('фонд|рфпи', case=False, na=False)]['Entity'].value_counts()
    if len(fund_variants) > 0:
        print("\nRDIF/Fund variants found:")
        for entity, count in fund_variants.head(10).items():
            print(f"  {entity}: {count:,}")
    
    print(f"\nFinal dataset saved to: {output_file}")
    return df_final

# Run the cleaning process
if __name__ == "__main__":
    cleaned_df = advanced_entity_cleaning(
        input_file='ner_entity_dataset_final_clean.csv',
        output_file='ner_entity_dataset_normalized.csv',
        min_occurrences=5
    )
    
    print("\n=== VERIFICATION ===")
    print("Checking normalization results:")
    
    # Check if Putin variants were properly merged
    putin_entities = cleaned_df[cleaned_df['Entity'].str.contains('путин', case=False, na=False)]['Entity'].unique()
    print(f"Putin entities remaining: {len(putin_entities)}")
    for entity in putin_entities:
        count = cleaned_df[cleaned_df['Entity'] == entity]['Occurrences'].iloc[0]
        print(f"  {entity}: {count:,}")
    
    # Check RDIF variants
    rdif_entities = cleaned_df[cleaned_df['Entity'] == 'РФПИ']['Occurrences'].iloc[0] if 'РФПИ' in cleaned_df['Entity'].values else 0
    print(f"\nРФПИ occurrences: {rdif_entities:,}")
