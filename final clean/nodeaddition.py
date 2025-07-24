import pandas as pd

def update_merged_dataset():
    # Extract only the final (normalized) entities from the mapping
    normalized_entities = set([
        'Джордж Надер', 'Александр Чоботов', 'Кирилл Шамалов', 'Газпром Нефть Восток',
        'Kuwait Investment Authority', 'Türkiye Wealth Fund (TWF)', 'Fraport (Frankfurt Airport)',
        'принц Бандар бен Султан', 'Рик Герсон', 'принц Мухаммед бен Сальман Аль Сауд (MBS)',
        'Нефтетранссервис (NTS)', 'Pharco Pharmaceuticals', 'Serum Institute of India',
        'Adienne Pharma & Biotech', 'Mitsui & Co.', 'Мариинский театр', 'ГИТИС',
        'Фонд История Отечества', 'Pizzarotti Group', 'ЗапСибНефтехим',
        'Saudi Basic Industries Corporation (SABIC)', 'ESN Group', 'Русэнергосбыт',
        'KazanForum', 'Султан Ахмед бен Сулейм', 'Шон Глобек',
        'China Construction Bank Corporation (CCB)', 'CROSAPF', 'Автодор', 'MAYKOR',
        'АО Волтайр-Пром', 'JPMorgan Chase & Co.', 'КАРО', 'UFG Private Equity',
        'Paul Heth', 'Динг Хуонг', 'Бадер Мохаммад Аль-Саад', 'Ахмад Мухаммад Аль-Сауд',
        'Hongchul Ahn', 'Халдун Халифа Аль Мубарак', 'Тадаши Маэда', 'Маурицио Таманьини',
        'Стивен Шварцман', 'Леон Блэк', 'Apollo Management', 'Джозеф Шулл',
        'Warburg Pincus Europe', 'Мартин Халуса', 'Apax Partners LLP', 'Курт Бьерклунд',
        'Permira', 'Махмуд Хашим Аль-Кохеджи', 'Ричард Дэйли', 'Fondo Strategico Italiano (FSI)',
        'Korea Investment Corporation', 'Российско-корейская инвестиционная платформа',
        'Департамент Финансов Абу-Даби', 'Хамад Аль Хурр Аль Сувайди', 'Mumtalakat',
        'Жозеф Доминик Силва', 'Khazanah', 'Анвар Ибрагим', 'Всемирный экономический форум',
        'BlackRock', 'CapMan Russia Fund', 'Titan International', 'One Equity Partners',
        'AGC Equity Partners', 'Фонд национального благосостояния',
        'Российско-французский инвестиционный фонд', 'JASE-W', 'Анатолий Браверман',
        'Российская венчурная компания', 'Тагир Ситдеков', 'SBI Holdings', 'Станислав Сонг',
        'KIA', 'State bank of India', 'Восточный комитет немецкой экономики', 'Tata power',
        'IDFC', 'Лу Цзивэй', 'Чон Сук Чой', 'NIIF', 'Российско-индийский инвестиционный фонд',
        'Российско-саудовский инвестиционный фонд', 'Государственная корпорация по инвестициям капитала (SCIC)',
        'Российско-вьетнамская инвестиционная платформа', 'Inventis Investment Holdings',
        'TUS-Holdings', 'Российско-китайский венчурный фонд', 'Российско-турецкий инвестиционный фонд (RTIF)',
        'Ircon', 'TH Group', 'Китайско-евразийский фонд экономического сотрудничества (КЕФЭС)',
        'BTG Panctual', 'Банк развития Южной Африки (DBSA)', 'Hyperloop', 'ARC International',
        'SME Investments', 'Российско-армянский инвестиционный фонд', 'ИнфоВотч',
        'Профессиональные логистические технологии (PLT)', 'NtechLab', 'Свеза', 'ANAS',
        'Zhaogang', 'Dakaitaowa', 'RFC International', 'Проект Тушино', 'Interhealth Saudi Arabia',
        'Globaltruck', 'NIO', 'Hitachi Zosen Inova (HZI)', 'Olmix', 'Клуб инвесторов Армении (ICA)',
        'Makyol', 'Саудовская железнодорожная компания',
        'Саудовская компания по технологическому развитию и инвестициям (TAQNIA)',
        'Саудовский центр международных стратегических партнерств (SCISP)',
        'Министерство инвестиций Египта', 'Турецкий суверенный фонд (TSF)',
        'Российско-турецкий инвестиционный фонд', 'Буровая компания Евразия',
        'Строительство ЦКАД 3 и 4', 'Автобан', 'Евразийский банк развития (EDB)',
        'Первый железнодорожный мост между Россией и Китаем'
    ])
    
    # Load NER dataset and check which entities exist
    df_ner = pd.read_csv('ner_entity_dataset_superclean.csv')
    ner_entities = set(df_ner['Entity'].unique())
    
    # Find entities that exist in both lists
    entities_to_check = normalized_entities & ner_entities
    
    # Load merged dataset
    df_merged = pd.read_excel('merged_dataset.xlsx')
    existing_merged_entities = set(df_merged['Entity'].unique())
    
    # Find entities that are in NER but not in merged dataset
    entities_to_add = entities_to_check - existing_merged_entities
    
    if entities_to_add:
        # Get the data for these entities from NER dataset
        new_data = df_ner[df_ner['Entity'].isin(entities_to_add)]
        
        # Combine datasets
        df_combined = pd.concat([df_merged, new_data], ignore_index=True)
        
        # Save to Excel
        df_combined.to_excel('merged_dataset.xlsx', index=False)
        
        print(f"Added {len(new_data)} rows for {len(entities_to_add)} entities:")
        for entity in sorted(entities_to_add):
            count = len(new_data[new_data['Entity'] == entity])
            print(f"  - {entity}: {count} rows")
    else:
        print("No new entities to add")
    
    print(f"Final dataset size: {len(df_combined) if entities_to_add else len(df_merged)} rows")

if __name__ == "__main__":
    update_merged_dataset()
