import pandas as pd
from datetime import datetime

def process_entity_datasets():
    """
    Process NER entity datasets to:
    1. Merge similar entities 
    2. Fix spelling errors
    3. Filter to keep only specified entities
    4. Save changes to original files
    """
    
    print("🔧 PROCESSING ENTITY DATASETS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Define the dataset filenames
    files = [
        'ner_entity_dataset_TOP_100.csv',
        'ner_entity_dataset_TOP_100_UNIQUE.csv'
    ]
    
    # Define renaming map for merging and fixing spelling errors
    rename_map = {
        # MERGE entities
        'Екатерины Тихоновой': 'Екатерина Тихонова',
        'Тихонова': 'Екатерина Тихонова',
        
        # FIX SPELLING
        'Эриком Принсом': 'Эрик Принс',
        'Суммы': 'Сумма',
        'Стросс-Кан': 'Доминик Стросс-Кан',
        'Россетях': '«Россети»',
        'Росатомом': 'Росатом',
        'Александра Джапаридзе': 'Александр Джапаридзе',
        'ОАО Детский мир': 'Детский мир',
        'Детским миром': 'Детский мир',
        'Еврохима': 'ЕвроХим',
        'Алросе': 'АК АЛРОСА',
        'Дмитрия Сергеева': 'Дмитрий Сергеев',
        'Mubadala Development': 'Mubadala Investment Company',
        'Моисеев': 'Алексей Моисеев',
        'DP World Russia': 'DP World',
        'Андреем Белоусовым': 'Андрей Белоусов'
    }
    
    # Define entities to keep after filtering
    keep_entities = {
        'AGC Equity Partners',
        'Almaz Capital Partners',
        'Altera Capital',
        'Apollo Global Management',
        'Arc International',
        'CDC International Capital',
        'Cassa Depositi e Prestiti SpA',
        'Dr Reddys',
        'Dubai Ports',
        'Franklin Templeton',
        'Fraport AG',
        'Gland Pharma',
        'Hetero Biopharma',
        'JBIC IG Partners',
        'RTP Global',
        'Russia Forest Products',
        'Serum Institute of India',
        'Stelis Biopharma',
        'Tata Power',
        'Tesla Motors',
        'UFG Private Equity',
        'Virchow Biotech',
        'Warburg Pincus',
        'АФГ Националь',
        'АЭС Аккую',
        'Александр Афанасьев',
        'Александр Джапаридзе',  # Updated name after renaming
        'Амин Нассер',
        'Анатолий Браверман',
        'Бадер Мохаммад Аль-Саад',
        'Владимир Рожанковский',
        'Волож',
        'Волтайр-Пром',
        'Вэнь Цзябао',
        'Герофарм',
        'Гонконгской бирже',
        'Дельпаль',
        'Детская Галерея Якиманка',
        'Дикси',
        'Дмитрий Сергеев',  # Updated name after renaming
        'Евгений Юрченко',
        'ЕврАзЭС',
        'ЕвроХим',  # Updated name after renaming
        'ЗАО Терминал Владивосток',
        'ЗапСиб-2',
        'Зоозавр',
        'Ивлев',
        'Ирина Парфентьева',
        'КИТ Финанс',
        'Каро Фильм',
        'Кира Кирюхина',
        'Леон Блэк',
        'Леонид Богуславский',
        'Лю Цзивэй',
        'Максим Перельман',
        'Маурицио Таманьини',
        'Михаил Алексеев',
        'Михаил Ковальчук',
        'Нефтетранссервис',
        'Нихат Зейбекчи',
        'Новапорт',
        'Новый бизнес',
        'Олег Трутнев',
        'Олимпик Парк',
        'Павел Теплухин',
        'РТ-Инвест',
        'Ремдесивира',
        'Стивен Шварцман',
        'Тагир Ситдеков',
        'Тедрос Гебрейесус',
        'Тина Канделаки',
        'Транснефть Телеком',
        'Уралхим',
        'Чжан Гаоли',
        'Электрощит Самара',
        'Энрико Летты',
        # Additional entities that might result from renaming
        'Екатерина Тихонова',  # Result of merging
        'Эрик Принс',  # Result of spelling fix
        'Сумма',  # Result of spelling fix
        'Доминик Стросс-Кан',  # Result of spelling fix
        '«Россети»',  # Result of spelling fix
        'Росатом',  # Result of spelling fix
        'Детский мир',  # Result of merging
        'АК АЛРОСА',  # Result of spelling fix
        'Mubadala Investment Company',  # Result of spelling fix
        'Алексей Моисеев',  # Result of spelling fix
        'DP World',  # Result of spelling fix
        'Андрей Белоусов'  # Result of spelling fix
    }
    
    def process_file(filename):
        """Process a single CSV file"""
        try:
            # Load the dataset
            df = pd.read_csv(filename)
            print(f"✓ Loaded {filename}: {len(df)} rows")
            
            if 'Entity' not in df.columns:
                print(f"❌ Error: 'Entity' column not found in {filename}")
                return None, None
            
            original_entities = df['Entity'].nunique()
            
            # Step 1: Apply renaming (merging and spelling fixes)
            df['Entity'] = df['Entity'].replace(rename_map)
            
            # Count entities after renaming
            renamed_entities = df['Entity'].nunique()
            
            # Step 2: Filter to keep only specified entities
            df_filtered = df[df['Entity'].isin(keep_entities)].copy()
            
            # Step 3: Save the fully processed dataset back to original file
            df.to_csv(filename, index=False)
            print(f"✓ Saved updated {filename}")
            
            # Step 4: Create a filtered version
            filtered_filename = filename.replace('.csv', '_filtered.csv')
            df_filtered.to_csv(filtered_filename, index=False)
            print(f"✓ Created filtered version: {filtered_filename}")
            
            # Print statistics
            print(f"   - Original unique entities: {original_entities}")
            print(f"   - After renaming: {renamed_entities}")
            print(f"   - After filtering: {df_filtered['Entity'].nunique()}")
            print(f"   - Rows kept after filtering: {len(df_filtered)} of {len(df)}")
            
            return df, df_filtered
            
        except FileNotFoundError:
            print(f"❌ Error: File '{filename}' not found.")
            return None, None
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            return None, None
    
    # Process both files
    results = {}
    
    for filename in files:
        print(f"\n{'='*40}")
        print(f"PROCESSING: {filename}")
        print(f"{'='*40}")
        
        original_df, filtered_df = process_file(filename)
        
        if original_df is not None:
            results[filename] = {
                'original': original_df,
                'filtered': filtered_df,
                'success': True
            }
        else:
            results[filename] = {'success': False}
    
    # Print final summary
    print(f"\n{'='*60}")
    print(f"PROCESSING SUMMARY")
    print(f"{'='*60}")
    
    successful_files = [f for f, r in results.items() if r['success']]
    failed_files = [f for f, r in results.items() if not r['success']]
    
    print(f"✅ Successfully processed: {len(successful_files)} files")
    for f in successful_files:
        print(f"   - {f}")
    
    if failed_files:
        print(f"❌ Failed to process: {len(failed_files)} files")
        for f in failed_files:
            print(f"   - {f}")
    
    print(f"\n📋 RENAMING RULES APPLIED:")
    for old_name, new_name in rename_map.items():
        print(f"   '{old_name}' → '{new_name}'")
    
    print(f"\n🔍 FILTERING APPLIED:")
    print(f"   Kept only {len(keep_entities)} specified entities")
    
    return results


# Helper function to show entity changes
def show_entity_changes(filename):
    """Show what entities were changed in a specific file"""
    try:
        df = pd.read_csv(filename)
        
        if 'Entity' not in df.columns:
            print(f"❌ Error: 'Entity' column not found in {filename}")
            return
        
        print(f"\n📊 ENTITY ANALYSIS FOR {filename}:")
        print(f"{'='*50}")
        
        entity_counts = df['Entity'].value_counts()
        
        print(f"Top 10 most frequent entities:")
        for i, (entity, count) in enumerate(entity_counts.head(10).items(), 1):
            print(f"{i:>2}. {entity}: {count} mentions")
        
        print(f"\nTotal unique entities: {len(entity_counts)}")
        print(f"Total rows: {len(df)}")
        
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found.")
    except Exception as e:
        print(f"❌ Error analyzing {filename}: {e}")


# Main execution
if __name__ == "__main__":
    print("🚀 ENTITY DATASET PROCESSING")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Process the datasets
    results = process_entity_datasets()
    
    # Show analysis for processed files
    for filename in ['ner_entity_dataset_TOP_100.csv', 'ner_entity_dataset_TOP_100_UNIQUE.csv']:
        if filename in results and results[filename]['success']:
            show_entity_changes(filename)
    
    print(f"\n✅ PROCESSING COMPLETED!")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
