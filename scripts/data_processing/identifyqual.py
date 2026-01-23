import pandas as pd
from datetime import datetime

# Entity mapping dictionary
entity_mapping = {
    # George Nader
    'George Nader': 'Джордж Надер',
    'Джордж Надер': 'Джордж Надер',
    'Джорджа Надера': 'Джордж Надер',
    'Джорджу Надеру': 'Джордж Надер',
    'Джорджем Надером': 'Джордж Надер',
    'о Джордже Надере': 'Джордж Надер',
    
    # Alexander Chobotov
    'Alexander Chobotov': 'Александр Чоботов',
    'Александр Чоботов': 'Александр Чоботов',
    'Александра Чоботова': 'Александр Чоботов',
    'Александру Чоботову': 'Александр Чоботов',
    'Александром Чоботовым': 'Александр Чоботов',
    'об Александре Чоботове': 'Александр Чоботов',
    
    # Kirill Shamalov
    'Kirill Shamalov': 'Кирилл Шамалов',
    'Кирилл Шамалов': 'Кирилл Шамалов',
    'Кирилла Шамалова': 'Кирилл Шамалов',
    'Кириллу Шамалову': 'Кирилл Шамалов',
    'Кириллом Шамаловым': 'Кирилл Шамалов',
    'о Кирилле Шамалове': 'Кирилл Шамалов',
    
    # Gazpromneft-Vostok JV
    'Gazpromneft-Vostok JV': 'Газпром Нефть Восток',
    'Газпром Нефть Восток': 'Газпром Нефть Восток',
    'Газпрома Нефть Восток': 'Газпром Нефть Восток',
    'Газпрому Нефть Восток': 'Газпром Нефть Восток',
    'компания Газпром Нефть Восток': 'Газпром Нефть Восток',
    
    # Kuwait Investment Authority
    'Kuwait Investment Authority': 'Kuwait Investment Authority',
    'Кувейтский инвестиционный фонд': 'Kuwait Investment Authority',
    'КИФ': 'Kuwait Investment Authority',
    
    # Türkiye Wealth Fund
    'Türkiye Wealth Fund (TWF)': 'Türkiye Wealth Fund (TWF)',
    'Türkiye Wealth Fund': 'Türkiye Wealth Fund (TWF)',
    'TWF': 'Türkiye Wealth Fund (TWF)',
    'Турецкий фонд благосостояния': 'Türkiye Wealth Fund (TWF)',
    'Фонд благосостояния Турции': 'Türkiye Wealth Fund (TWF)',
    
    # Fraport
    'Fraport (Frankfurt Airport)': 'Fraport (Frankfurt Airport)',
    'Fraport': 'Fraport (Frankfurt Airport)',
    'Франкфуртский аэропорт': 'Fraport (Frankfurt Airport)',
    'аэропорт Франкфурта': 'Fraport (Frankfurt Airport)',
    
    # Prince Bandar bin Sultan
    'Prince Bandar bin Sultan': 'принц Бандар бен Султан',
    'принц Бандар бен Султан': 'принц Бандар бен Султан',
    'принца Бандара бен Султана': 'принц Бандар бен Султан',
    'принцу Бандару бен Sultan': 'принц Бандар бен Султан',
    
    # Rick Gerson
    'Rick Gerson': 'Рик Герсон',
    'Рик Герсон': 'Рик Герсон',
    'Рика Герсона': 'Рик Герсон',
    'Рику Герсону': 'Рик Герсон',
    'Риком Герсоном': 'Рик Герсон',
    'о Рике Герсоне': 'Рик Герсон',
    
    # Mohammed bin Salman
    'Mohammed bin Salman (MBS)': 'принц Мухаммед бен Сальман Аль Сауд (MBS)',
    'Mohammed bin Salman': 'принц Мухаммед бен Сальман Аль Сауд (MBS)',
    'MBS': 'принц Мухаммед бен Сальман Аль Сауд (MBS)',
    'принц Мухаммед бен Сальман': 'принц Мухаммед бен Сальман Аль Сауд (MBS)',
    'Мухаммед бен Сальман': 'принц Мухаммед бен Сальман Аль Сауд (MBS)',
    'наследный принц Саудовской Аравии': 'принц Мухаммед бен Сальман Аль Сауд (MBS)',
    
    # NefteTransService
    'NefteTransService (NTS)': 'Нефтетранссервис (NTS)',
    'NefteTransService': 'Нефтетранссервис (NTS)',
    'НТС': 'Нефтетранссервис (NTS)',
    'Нефтетранссервис': 'Нефтетранссервис (NTS)',
    'компания Нефтетранссервис': 'Нефтетранссервис (NTS)',
    
    # Pharco Pharmaceuticals
    'Pharco Pharmaceuticals': 'Pharco Pharmaceuticals',
    'Фарко Фармасьютикалс': 'Pharco Pharmaceuticals',
    
    # Serum Institute of India
    'Serum Institute of India': 'Serum Institute of India',
    'Индийский институт сывороток': 'Serum Institute of India',
    
    # Adienne Pharma & Biotech
    'Adienne Pharma & Biotech': 'Adienne Pharma & Biotech',
    'Адьенне Фарма энд Биотек': 'Adienne Pharma & Biotech',
    
    # Mitsui & Co.
    'Mitsui & Co.': 'Mitsui & Co.',
    'Мицуи энд Ко': 'Mitsui & Co.',
    'компания Мицуи': 'Mitsui & Co.',
    
    # Mariinsky Theatre
    'The Mariinsky Theatre': 'Мариинский театр',
    'Мариинский театр': 'Мариинский театр',
    'Мариинского театра': 'Мариинский театр',
    'Мариинскому театру': 'Мариинский театр',
    'в Мариинском театре': 'Мариинский театр',
    
    # Russian Institute of Theatre Arts
    'Russian Institute of Theatre Arts': 'ГИТИС',
    'ГИТИС': 'ГИТИС',
    'ГИТИСа': 'ГИТИС',
    'ГИТИСу': 'ГИТИС',
    'Российский институт театрального искусства': 'ГИТИС',
    
    # History of the Fatherland Foundation
    'The History of the Fatherland Foundation': 'Фонд История Отечества',
    'Фонд История Отечества': 'Фонд История Отечества',
    'Фонда История Отечества': 'Фонд История Отечества',
    'Фонду История Отечества': 'Фонд История Отечества',
    
    # Pizzarotti Group
    'Pizzarotti Group': 'Pizzarotti Group',
    'группа Пиццаротти': 'Pizzarotti Group',
    'Пиццаротти': 'Pizzarotti Group',
    
    # ZapSibNeftekhim
    'ZapSibNeftekhim': 'ЗапСибНефтехим',
    'ЗапСибНефтехим': 'ЗапСибНефтехим',
    'ЗапСибНефтехима': 'ЗапСибНефтехим',
    'ЗапСибНефтехиму': 'ЗапСибНефтехим',
    'компания ЗапСибНефтехим': 'ЗапСибНефтехим',
    
    # Saudi Basic Industries Corporation
    'Saudi Basic Industries Corporation (SABIC)': 'Saudi Basic Industries Corporation (SABIC)',
    'Saudi Basic Industries Corporation': 'Saudi Basic Industries Corporation (SABIC)',
    'SABIC': 'Saudi Basic Industries Corporation (SABIC)',
    'САБИК': 'Saudi Basic Industries Corporation (SABIC)',
    'Саудовская корпорация базовых отраслей промышленности': 'Saudi Basic Industries Corporation (SABIC)',
    
    # ESN Group
    'ESN Group': 'ESN Group',
    'группа ESN': 'ESN Group',
    'ЕСН Групп': 'ESN Group',
    
    # Rusenergosbyt
    'Rusenergosbyt': 'Русэнергосбыт',
    'Русэнергосбыт': 'Русэнергосбыт',
    'Русэнергосбыта': 'Русэнергосбыт',
    'Русэнергосбыту': 'Русэнергосбыт',
    'компания Русэнергосбыт': 'Русэнергосбыт',
    
    # KazanForum
    'KazanForum': 'KazanForum',
    'КазанФорум': 'KazanForum',
    'Казанский форум': 'KazanForum',
    
    # Sultan Ahmed bin Sulayem
    'Sultan Ahmed bin Sulayem': 'Султан Ахмед бен Сулейм',
    'Султан Ахмед бен Сулейм': 'Султан Ахмед бен Сулейм',
    'Султана Ахмеда бен Сулейма': 'Султан Ахмед бен Сулейм',
    'Султану Ахмеду бен Сулейму': 'Султан Ахмед бен Сулейм',
    
    # Sean Glodek
    'Sean Glodek': 'Шон Глобек',
    'Шон Глобек': 'Шон Глобек',
    'Шона Глобека': 'Шон Глобек',
    'Шону Глобеку': 'Шон Глобек',
    'Шоном Глобеком': 'Шон Глобек',
    
    # China Construction Bank Corporation
    'China Construction Bank Corporation (CCB)': 'China Construction Bank Corporation (CCB)',
    'China Construction Bank Corporation': 'China Construction Bank Corporation (CCB)',
    'CCB': 'China Construction Bank Corporation (CCB)',
    'ССВ': 'China Construction Bank Corporation (CCB)',
    'Китайский строительный банк': 'China Construction Bank Corporation (CCB)',
    'Строительный банк Китая': 'China Construction Bank Corporation (CCB)',
    
    # CROSAPF
    'CROSAPF (Co-investment Roundtable of Sovereign and Pension Funds)': 'CROSAPF',
    'CROSAPF': 'CROSAPF',
    'КРОСАПФ': 'CROSAPF',
    'Круглый стол по совместным инвестициям суверенных и пенсионных фондов': 'CROSAPF',
    
    # Avtodorozhnaya Stroitelnaya Korporatsiya
    'Avtodorozhnaya Stroitelnaya Korporatsiya, LLC': 'Автодор',
    'Avtodorozhnaya Stroitelnaya Korporatsiya': 'Автодор',
    'Автодор': 'Автодор',
    'Автодора': 'Автодор',
    'Автодору': 'Автодор',
    'компания Автодор': 'Автодор',
    'АО Автодор': 'Автодор',
    
    # Maykor
    'Maykor': 'MAYKOR',
    'MAYKOR': 'MAYKOR',
    'Майкор': 'MAYKOR',
    'компания Майкор': 'MAYKOR',
    
    # Voltyre-Prom
    'Voltyre-Prom': 'АО Волтайр-Пром',
    'АО Волтайр-Пром': 'АО Волтайр-Пром',
    'Волтайр-Пром': 'АО Волтайр-Пром',
    'компания Волтайр-Пром': 'АО Волтайр-Пром',
    
    # JPMorgan Chase & Co.
    'JPMorgan Chase & Co.': 'JPMorgan Chase & Co.',
    'Джей Пи Морган Чейз': 'JPMorgan Chase & Co.',
    'ДжейПиМорган': 'JPMorgan Chase & Co.',
    
    # Karo Film
    'Karo Film': 'КАРО',
    'КАРО': 'КАРО',
    'сеть кинотеатров КАРО': 'КАРО',
    'кинотеатры КАРО': 'КАРО',
    
    # UFG Private Equity
    'UFG Private Equity': 'UFG Private Equity',
    'ЮФГ Прайвет Эквити': 'UFG Private Equity',
    
    # Paul Heth
    'Paul Heth': 'Paul Heth',
    'Пол Хет': 'Paul Heth',
    'Пола Хета': 'Paul Heth',
    'Полу Хету': 'Paul Heth',
    
    # Ding Xuedong
    'Ding Xuedong': 'Динг Хуонг',
    'Динг Хуонг': 'Динг Хуонг',
    'Динга Хуонга': 'Динг Хуонг',
    'Дингу Хуонгу': 'Динг Хуонг',
    
    # Bader Mohammad Al-Sa'ad
    "Bader Mohammad Al-Sa'ad": 'Бадер Мохаммад Аль-Саад',
    'Бадер Мохаммад Аль-Саад': 'Бадер Мохаммад Аль-Саад',
    'Бадера Мохаммада Аль-Саада': 'Бадер Мохаммад Аль-Саад',
    
    # Ahmad Mohamed Al-Sayed
    'Ahmad Mohamed Al-Sayed': 'Ахмад Мухаммад Аль-Сауд',
    'Ахмад Мухаммад Аль-Сауд': 'Ахмад Мухаммад Аль-Сауд',
    'Ахмада Мухаммада Аль-Сауда': 'Ахмад Мухаммад Аль-Сауд',
    
    # Hongchul Ahn
    'Hongchul (Hank) Ahn': 'Hongchul Ahn',
    'Hongchul Ahn': 'Hongchul Ahn',
    'Хонгчул Ан': 'Hongchul Ahn',
    'Хэнк Ан': 'Hongchul Ahn',
    
    # Khaldoon Khalifa Al-Mubarak
    'Khaldoon Khalifa Al-Mubarak': 'Халдун Халифа Аль Мубарак',
    'Халдун Халифа Аль Мубарак': 'Халдун Халифа Аль Мубарак',
    'Халдуна Халифы Аль Мубарака': 'Халдун Халифа Аль Мубарак',
    
    # Tadashi Maeda
    'Tadashi Maeda': 'Тадаши Маэда',
    'Тадаши Маэда': 'Тадаши Маэда',
    'Тадаши Маэды': 'Тадаши Маэда',
    'Тадаши Маэде': 'Тадаши Маэда',
    
    # Maurizio Tamagnini
    'Maurizio Tamagnini': 'Маурицио Таманьини',
    'Маурицио Таманьини': 'Маурицио Таманьини',
    
    # Stephen Schwarzman
    'Stephen Schwarzman': 'Стивен Шварцман',
    'Стивен Шварцман': 'Стивен Шварцман',
    'Стивена Шварцмана': 'Стивен Шварцман',
    'Стивену Шварцману': 'Стивен Шварцман',
    
    # Leon Black
    'Leon Black': 'Леон Блэк',
    'Леон Блэк': 'Леон Блэк',
    'Леона Блэка': 'Леон Блэк',
    'Леону Блэку': 'Леон Блэк',
    
    # Apollo Management
    'Apollo Management': 'Apollo Management',
    'Аполло Менеджмент': 'Apollo Management',
    
    # Joseph Schull
    'Joseph Schull': 'Джозеф Шулл',
    'Джозеф Шулл': 'Джозеф Шулл',
    'Джозефа Шулла': 'Джозеф Шулл',
    'Джозефу Шуллу': 'Джозеф Шулл',
    
    # Warburg Pincus Europe
    'Warburg Pincus Europe': 'Warburg Pincus Europe',
    'Варбург Пинкус Европа': 'Warburg Pincus Europe',
    
    # Martin Halusa
    'Dr. Martin Halusa': 'Мартин Халуса',
    'доктор Мартин Халуса': 'Мартин Халуса',
    'Мартин Халуса': 'Мартин Халуса',
    'Мартина Халусы': 'Мартин Халуса',
    
    # Apax Partners
    'Apax Partners': 'Apax Partners LLP',
    'Apax Partners LLP': 'Apax Partners LLP',
    'Апакс Партнерс': 'Apax Partners LLP',
    
    # Kurt Bjorklund
    'Kurt Bjorklund': 'Курт Бьерклунд',
    'Курт Бьерклунд': 'Курт Бьерклунд',
    'Курта Бьерклунда': 'Курт Бьерклунд',
    'Курту Бьерклунду': 'Курт Бьерклунд',
    
    # Permira
    'Permira': 'Permira',
    'Пермира': 'Permira',
    
    # Mahmood Hashim Al Kooheji
    'Mahmood Hashim Al Kooheji': 'Махмуд Хашим Аль-Кохеджи',
    'Махмуд Хашим Аль-Кохеджи': 'Махмуд Хашим Аль-Кохеджи',
    'Махмуда Хашима Аль-Кохеджи': 'Махмуд Хашим Аль-Кохеджи',
    
    # Richard M. Daley
    'Richard M. Daley': 'Ричард Дэйли',
    'Ричард Дэйли': 'Ричард Дэйли',
    'Ричарда Дэйли': 'Ричард Дэйли',
    'Ричарду Дэйли': 'Ричард Дэйли',
    
    # Fondo Strategico Italiano
    'Fondo Strategico Italiano (FSI)': 'Fondo Strategico Italiano (FSI)',
    'Fondo Strategico Italiano': 'Fondo Strategico Italiano (FSI)',
    'FSI': 'Fondo Strategico Italiano (FSI)',
    'ФСИ': 'Fondo Strategico Italiano (FSI)',
    'Итальянский стратегический фонд': 'Fondo Strategico Italiano (FSI)',
    
    # Korea Investment Corporation
    'Korea Investment Corporation': 'Korea Investment Corporation',
    'Корейская инвестиционная корпорация': 'Korea Investment Corporation',
    
    # Russia-Korea Investment Fund
    'Russia-Korea Investment Fund': 'Российско-корейская инвестиционная платформа',
    'Российско-корейская инвестиционная платформа': 'Российско-корейская инвестиционная платформа',
    'российско-корейский инвестиционный фонд': 'Российско-корейская инвестиционная платформа',
    
    # Abu Dhabi Department of Finance
    'Abu Dhabi Department of Finance': 'Департамент Финансов Абу-Даби',
    'Департамент Финансов Абу-Даби': 'Департамент Финансов Абу-Даби',
    'Департамента Финансов Абу-Даби': 'Департамент Финансов Абу-Даби',
    
    # Hamad Mohammed Al Hurr Al Suwaidi
    'Hamad Mohammed Al Hurr Al Suwaidi': 'Хамад Аль Хурр Аль Сувайди',
    'Хамад Аль Хурр Аль Сувайди': 'Хамад Аль Хурр Аль Сувайди',
    'Хамада Аль Хурра Аль Сувайди': 'Хамад Аль Хурр Аль Сувайди',
    
    # Mumtalakat
    'Mumtalakat (Bahrain)': 'Mumtalakat',
    'Mumtalakat': 'Mumtalakat',
    'Мумталакат': 'Mumtalakat',
    'бахрейнский суверенный фонд': 'Mumtalakat',
    
    # Joseph Dominic Silva
    'JOSEPH DOMINIC SILVA': 'Жозеф Доминик Силва',
    'Joseph Dominic Silva': 'Жозеф Доминик Силва',
    'Жозеф Доминик Силва': 'Жозеф Доминик Силва',
    'Жозефа Доминика Силвы': 'Жозеф Доминик Силва',
    
    # Khazanah Nasional Berhad
    'Khazanah Nasional Berhad': 'Khazanah',
    'Khazanah': 'Khazanah',
    'Хазана': 'Khazanah',
    'малайзийский суверенный фонд': 'Khazanah',
    
    # Anwar Ibrahim
    'Anwar Ibrahim': 'Анвар Ибрагим',
    'Анвар Ибрагим': 'Анвар Ибрагим',
    'Анвара Ибрагима': 'Анвар Ибрагим',
    'Анвару Ибрагиму': 'Анвар Ибрагим',
    
    # World Economic Forum
    'World Economic Forum': 'Всемирный экономический форум',
    'Всемирный экономический форум': 'Всемирный экономический форум',
    'ВЭФ': 'Всемирный экономический форум',
    'Давосский форум': 'Всемирный экономический форум',
    
    # BlackRock
    'BlackRock': 'BlackRock',
    'БлэкРок': 'BlackRock',
    
    # CapMan Russia Fund
    'CapMan Russia Fund': 'CapMan Russia Fund',
    'КэпМан Раша Фанд': 'CapMan Russia Fund',
    
    # Titan International
    'Titan International': 'Titan International',
    'Титан Интернешнл': 'Titan International',
    
    # One Equity Partners
    'One Equity Partners': 'One Equity Partners',
    'Ван Эквити Партнерс': 'One Equity Partners',
    
    # AGC Equity Partners
    'AGC Equity Partners': 'AGC Equity Partners',
    'ЭйДжиСи Эквити Партнерс': 'AGC Equity Partners',
    
    # National Wealth Fund
    'National Wealth Fund': 'Фонд национального благосостояния',
    'Фонд национального благосостояния': 'Фонд национального благосостояния',
    'ФНБ': 'Фонд национального благосостояния',
    
    # Russia-France Investment Fund
    'Russia-France Investment Fund (RFIF)': 'Российско-французский инвестиционный фонд',
    'Russia-France Investment Fund': 'Российско-французский инвестиционный фонд',
    'Российско-французский инвестиционный фонд': 'Российско-французский инвестиционный фонд',
    'РФИФ': 'Российско-французский инвестиционный фонд',
    
    # Japanese Business Alliance for Smart Energy Worldwide
    'Japanese Business Alliance for Smart Energy Worldwide (JASE-W)': 'JASE-W',
    'Japanese Business Alliance for Smart Energy Worldwide': 'JASE-W',
    'JASE-W': 'JASE-W',
    'Японский деловой альянс по умной энергетике': 'JASE-W',
    
    # Anatoly Braverman
    'Anatoly Braverman': 'Анатолий Браверман',
    'Анатолий Браверман': 'Анатолий Браверман',
    'Анатолия Бравермана': 'Анатолий Браверман',
    'Анатолию Браверману': 'Анатолий Браверман',
    
    # Russian Venture Company
    'Russian Venture Company': 'Российская венчурная компания',
    'Российская венчурная компания': 'Российская венчурная компания',
    'РВК': 'Российская венчурная компания',
    
    # Tagir Sitdekov
    'Tagir Sitdekov': 'Тагир Ситдеков',
    'Тагир Ситдеков': 'Тагир Ситдеков',
    'Тагира Ситдекова': 'Тагир Ситдеков',
    'Тагиру Ситдекову': 'Тагир Ситдеков',
    
    # SBI Holdings
    'SBI Holdings': 'SBI Holdings',
    'СБИ Холдингс': 'SBI Holdings',
    
    # Stanislav Song
    'Stanislav Song': 'Станислав Сонг',
    'Станислав Сонг': 'Станислав Сонг',
    'Станислава Сонга': 'Станислав Сонг',
    'Станиславу Сонгу': 'Станислав Сонг',
    
    # KIA
    'KIA': 'KIA',
    'КИА': 'KIA',
    'Корейская инвестиционная корпорация': 'KIA',
    
    # State bank of India
    'State bank of India': 'State bank of India',
    'Государственный банк Индии': 'State bank of India',
    
    # Ost-Ausschuss der Deutschen Wirtschaft
    'Ost-Ausschuss der Deutschen Wirtschaft': 'Восточный комитет немецкой экономики',
    'Восточный комитет немецкой экономики': 'Восточный комитет немецкой экономики',
    'Ост-Аусшус': 'Восточный комитет немецкой экономики',
    
    # Tata power
    'Tata power': 'Tata power',
    'Тата павер': 'Tata power',
    
    # IDFC
    'IDFC': 'IDFC',
    'ИДФС': 'IDFC',
    
    # Lou Jiwei
    'Lou Jiwei': 'Лу Цзивэй',
    'Лу Цзивэй': 'Лу Цзивэй',
    'Лу Цзивэя': 'Лу Цзивэй',
    'Лу Цзивэю': 'Лу Цзивэй',
    
    # Chong-Suk Choi
    'Chong-Suk Choi': 'Чон Сук Чой',
    'Чон Сук Чой': 'Чон Сук Чой',
    'Чон Сука Чоя': 'Чон Сук Чой',
    'Чон Суку Чою': 'Чон Сук Чой',
    
    # National Investment and Infrastructure Fund
    'National Investment and Infrastructure Fund (NIIF)': 'NIIF',
    'National Investment and Infrastructure Fund': 'NIIF',
    'NIIF': 'NIIF',
    'НИФ': 'NIIF',
    'Национальный инвестиционный и инфраструктурный фонд': 'NIIF',
    
    # Russia-India Investment Fund
    'Russia-India Investment Fund': 'Российско-индийский инвестиционный фонд',
    'Российско-индийский инвестиционный фонд': 'Российско-индийский инвестиционный фонд',
    'РИФ': 'Российско-индийский инвестиционный фонд',
    
    # Russia-Saudi Investment Fund
    'Russia-Saudi Investment Fund': 'Российско-саудовский инвестиционный фонд',
    'Российско-саудовский инвестиционный фонд': 'Российско-саудовский инвестиционный фонд',
    'РСИФ': 'Российско-саудовский инвестиционный фонд',
    
    # State Capital Investment Corporation
    'State Capital Investment Corporation (SCIC)': 'Государственная корпорация по инвестициям капитала (SCIC)',
    'State Capital Investment Corporation': 'Государственная корпорация по инвестициям капитала (SCIC)',
    'SCIC': 'Государственная корпорация по инвестициям капитала (SCIC)',
    'Государственная корпорация по инвестициям капитала': 'Государственная корпорация по инвестициям капитала (SCIC)',
    
    # Russian-Vietnamese investment platform
    'Russian-Vietnamese investment platform': 'Российско-вьетнамская инвестиционная платформа',
    'Российско-вьетнамская инвестиционная платформа': 'Российско-вьетнамская инвестиционная платформа',
    'российско-вьетнамский инвестиционный фонд': 'Российско-вьетнамская инвестиционная платформа',
    
    # Inventis Investment Holdings
    'Inventis Investment Holdings': 'Inventis Investment Holdings',
    'Инвентис Инвестмент Холдингс': 'Inventis Investment Holdings',
    
    # TUS-Holdings
    'TUS-Holdings': 'TUS-Holdings',
    'ТУС-Холдингс': 'TUS-Holdings',
    
    # Russia-China Venture Fund
    'Russia-China Venture Fund': 'Российско-китайский венчурный фонд',
    'Российско-китайский венчурный фонд': 'Российско-китайский венчурный фонд',
    'РКФВ': 'Российско-китайский венчурный фонд',
    
    # Russia–Turkey Investment Fund
    'Russia–Turkey Investment Fund (RTIF)': 'Российско-турецкий инвестиционный фонд (RTIF)',
    'Russia–Turkey Investment Fund': 'Российско-турецкий инвестиционный фонд (RTIF)',
    'RTIF': 'Российско-турецкий инвестиционный фонд (RTIF)',
    'Российско-турецкий инвестиционный фонд': 'Российско-турецкий инвестиционный фонд (RTIF)',
    
    # Ircon
    'Ircon': 'Ircon',
    'Иркон': 'Ircon',
    
    # TH Group
    'TH Group': 'TH Group',
    'ТХ Групп': 'TH Group',
    
    # China-Eurasian Economic Cooperation Fund
    'China-Eurasian Economic Cooperation Fund (CEF)': 'Китайско-евразийский фонд экономического сотрудничества (КЕФЭС)',
    'China-Eurasian Economic Cooperation Fund': 'Китайско-евразийский фонд экономического сотрудничества (КЕФЭС)',
    'КЕФЭС': 'Китайско-евразийский фонд экономического сотрудничества (КЕФЭС)',
    'CEF': 'Китайско-евразийский фонд экономического сотрудничества (КЕФЭС)',
    'Китайско-евразийский фонд экономического сотрудничества': 'Китайско-евразийский фонд экономического сотрудничества (КЕФЭС)',
    
    # BTG Panctual
    'BTG Panctual': 'BTG Panctual',
    'БТГ Панктуал': 'BTG Panctual',
    
    # The Development Bank of Southern Africa
    'The Development Bank of Southern Africa (DBSA)': 'Банк развития Южной Африки (DBSA)',
    'The Development Bank of Southern Africa': 'Банк развития Южной Африки (DBSA)',
    'DBSA': 'Банк развития Южной Африки (DBSA)',
    'Банк развития Южной Африки': 'Банк развития Южной Африки (DBSA)',
    
    # Hyperloop
    'Hyperloop': 'Hyperloop',
    'Гиперлуп': 'Hyperloop',
    
    # ARC International
    'ARC International': 'ARC International',
    'АРС Интернешнл': 'ARC International',
    
    # SME Investments
    'SME Investments': 'SME Investments',
    'СМЕ Инвестментс': 'SME Investments',
    
    # Russia-Armenia Investment Fund
    'Russia-Armenia Investment Fund': 'Российско-армянский инвестиционный фонд',
    'Российско-армянский инвестиционный фонд': 'Российско-армянский инвестиционный фонд',
    'РАИФ': 'Российско-армянский инвестиционный фонд',
    
    # InfoWatch
    'InfoWatch': 'ИнфоВотч',
    'ИнфоВотч': 'ИнфоВотч',
    'компания ИнфоВотч': 'ИнфоВотч',
    
    # Prosessional Logistics Technologies
    'Prosessional Logistics Technologies (PLT)': 'Профессиональные логистические технологии (PLT)',
    'Prosessional Logistics Technologies': 'Профессиональные логистические технологии (PLT)',
    'PLT': 'Профессиональные логистические технологии (PLT)',
    'Профессиональные логистические технологии': 'Профессиональные логистические технологии (PLT)',
    
    # NtechLab
    'NtechLab': 'NtechLab',
    'НтехЛаб': 'NtechLab',
    
    # Sveza
    'Sveza': 'Свеза',
    'Свеза': 'Свеза',
    'компания Свеза': 'Свеза',
    
    # ANAS
    'ANAS': 'ANAS',
    'АНАС': 'ANAS',
    
    # Zhaogang
    'Zhaogang': 'Zhaogang',
    'Жаоганг': 'Zhaogang',
    
    # Dakaitaowa
    'Dakaitaowa': 'Dakaitaowa',
    'Дакайтаова': 'Dakaitaowa',
    
    # RFC International
    'RFC International': 'RFC International',
    'РФС Интернешнл': 'RFC International',
    
    # The Tushino project
    'The Tushino project': 'Проект Тушино',
    'Проект Тушино': 'Проект Тушино',
    'проекта Тушино': 'Проект Тушино',
    'проекту Тушино': 'Проект Тушино',
    
    # Interhealth Saudi Arabia
    'Interhealth Saudi Arabia': 'Interhealth Saudi Arabia',
    'Интерхелс Саудовская Аравия': 'Interhealth Saudi Arabia',
    
    # Globaltruck Management PJSC
    'Globaltruck Management PJSC': 'Globaltruck',
    'Globaltruck': 'Globaltruck',
    'Глобалтрак': 'Globaltruck',
    
    # NIO
    'NIO': 'NIO',
    'НИО': 'NIO',
    
    # Hitachi Zosen Inova
    'Hitachi Zosen Inova (HZI)': 'Hitachi Zosen Inova (HZI)',
    'Hitachi Zosen Inova': 'Hitachi Zosen Inova (HZI)',
    'HZI': 'Hitachi Zosen Inova (HZI)',
    'Хитачи Зосен Инова': 'Hitachi Zosen Inova (HZI)',
    
    # Olmix
    'Olmix': 'Olmix',
    'Олмикс': 'Olmix',
    
    # The investors club of Armenia
    'The investors club of Armenia (ICA)': 'Клуб инвесторов Армении (ICA)',
    'The investors club of Armenia': 'Клуб инвесторов Армении (ICA)',
    'ICA': 'Клуб инвесторов Армении (ICA)',
    'Клуб инвесторов Армении': 'Клуб инвесторов Армении (ICA)',
    
    # Makyol
    'Makyol': 'Makyol',
    'Макьол': 'Makyol',
    
    # Saudi Railway Company
    'Saudi Railway Company': 'Саудовская железнодорожная компания',
    'Саудовская железнодорожная компания': 'Саудовская железнодорожная компания',
    'железнодорожная компания Саудовской Аравии': 'Саудовская железнодорожная компания',
    
    # The Saudi Technology Development and Investment Company
    'The Saudi Technology Development and Investment Company (TAQNIA)': 'Саудовская компания по технологическому развитию и инвестициям (TAQNIA)',
    'The Saudi Technology Development and Investment Company': 'Саудовская компания по технологическому развитию и инвестициям (TAQNIA)',
    'TAQNIA': 'Саудовская компания по технологическому развитию и инвестициям (TAQNIA)',
    'Саудовская компания по технологическому развитию и инвестициям': 'Саудовская компания по технологическому развитию и инвестициям (TAQNIA)',
    
    # The Saudi Center for International Strategic Partnerships
    'The Saudi Center for International Strategic Partnerships (SCISP)': 'Саудовский центр международных стратегических партнерств (SCISP)',
    'The Saudi Center for International Strategic Partnerships': 'Саудовский центр международных стратегических партнерств (SCISP)',
    'SCISP': 'Саудовский центр международных стратегических партнерств (SCISP)',
    'Саудовский центр международных стратегических партнерств': 'Саудовский центр международных стратегических партнерств (SCISP)',
    
    # The Egyptian Ministry of Investment
    'The Egyptian Ministry of Investment': 'Министерство инвестиций Египта',
    'Министерство инвестиций Египта': 'Министерство инвестиций Египта',
    'Министерства инвестиций Египта': 'Министерство инвестиций Египта',
    
    # Turkish Sovereign Fund
    'Turkish Sovereign Fund (TSF)': 'Турецкий суверенный фонд (TSF)',
    'Turkish Sovereign Fund': 'Турецкий суверенный фонд (TSF)',
    'TSF': 'Турецкий суверенный фонд (TSF)',
    'Турецкий суверенный фонд': 'Турецкий суверенный фонд (TSF)',
    
    # The Russian-Turkish Investment Fund
    'The Russian-Turkish Investment Fund': 'Российско-турецкий инвестиционный фонд',
    'Российско-турецкий инвестиционный фонд': 'Российско-турецкий инвестиционный фонд',
    'российско-турецкого инвестиционного фонда': 'Российско-турецкий инвестиционный фонд',
    
    # EDC Group
    'EDC Group': 'Буровая компания Евразия',
    'Буровая компания Евразия': 'Буровая компания Евразия',
    
    # Central Ring Road
    'Central Ring Road (CRR)': 'Строительство ЦКАД 3 и 4',
    'Central Ring Road': 'Строительство ЦКАД 3 и 4',
    'ЦКАД': 'Строительство ЦКАД 3 и 4',
    'Центральная кольцевая автодорога': 'Строительство ЦКАД 3 и 4',
    'строительство ЦКАД': 'Строительство ЦКАД 3 и 4',
    
    # Avtoban Group
    'Avtoban Group': 'Автобан',
    'Автобан': 'Автобан',
    'группа Автобан': 'Автобан',
    
    # Eurasian Development Bank
    'Eurasian Development Bank (EDB)': 'Евразийский банк развития (EDB)',
    'Eurasian Development Bank': 'Евразийский банк развития (EDB)',
    'EDB': 'Евразийский банк развития (EDB)',
    'ЕБР': 'Евразийский банк развития (EDB)',
    'Евразийский банк развития': 'Евразийский банк развития (EDB)',
    
    # First railway bridge between Russia and China
    'First railway bridge between Russia and China': 'Первый железнодорожный мост между Россией и Китаем',
    'Первый железнодорожный мост между Россией и Китаем': 'Первый железнодорожный мост между Россией и Китаем',
    'российско-китайский железнодорожный мост': 'Первый железнодорожный мост между Россией и Китаем',
    'мост через Амур': 'Первый железнодорожный мост между Россией и Китаем',
}


def find_missing_entities(ner_csv_path='ner_entity_dataset_superclean.csv'):
    """
    Find entities from the entity mapping that are not in the NER entity dataset.
    Create a CSV file with the missing normalized entities.
    """
    
    print("🔍 FINDING ENTITIES NOT IN NER DATASET")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Read the NER dataset
    try:
        df = pd.read_csv(ner_csv_path)
        print(f"✓ Successfully loaded NER dataset: {ner_csv_path}")
        print(f"✓ Total rows in NER dataset: {len(df):,}")
        print(f"✓ Unique entities in NER dataset: {len(df['Entity'].unique()):,}")
    except FileNotFoundError:
        print(f"❌ Error: File '{ner_csv_path}' not found.")
        return None
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None
    
    # Get all entities from the NER dataset
    ner_entities = set(df['Entity'].unique())
    
    # Get all entities from the mapping (both keys and values)
    mapping_keys = set(entity_mapping.keys())
    mapping_values = set(entity_mapping.values())
    all_mapping_entities = mapping_keys | mapping_values
    
    print(f"✓ Total entities in mapping dictionary: {len(all_mapping_entities):,}")
    print(f"✓ Unique normalized entities (values): {len(mapping_values):,}")
    
    # Find entities from mapping that are NOT in NER dataset
    missing_from_ner = all_mapping_entities - ner_entities
    
    # Find normalized entities that are NOT in NER dataset
    missing_normalized = mapping_values - ner_entities
    
    print(f"\n{'='*60}")
    print(f"ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Total mapping entities NOT in NER dataset: {len(missing_from_ner)}")
    print(f"Normalized entities NOT in NER dataset: {len(missing_normalized)}")
    
    # Create CSV with missing normalized entities
    if missing_normalized:
        missing_entities_data = []
        
        for entity in sorted(list(missing_normalized)):
            # Count how many keys map to this normalized entity
            mapping_variants = [k for k, v in entity_mapping.items() if v == entity]
            
            missing_entities_data.append({
                'Normalized_Entity': entity,
                'Number_of_Variants': len(mapping_variants),
                'Mapping_Variants': ' | '.join(mapping_variants),
                'Status': 'NOT_FOUND_IN_NER',
                'Analysis_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Create DataFrame
        missing_df = pd.DataFrame(missing_entities_data)
        missing_df = missing_df.sort_values('Number_of_Variants', ascending=False)
        
        # Save to CSV
        output_file = 'entities_not_in_ner_dataset.csv'
        try:
            missing_df.to_csv(output_file, index=False)
            print(f"✓ Missing entities saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return None
        
        # Display top missing entities
        print(f"\n{'='*60}")
        print(f"TOP 20 NORMALIZED ENTITIES NOT FOUND IN NER DATASET")
        print(f"{'='*60}")
        
        for i, row in missing_df.head(20).iterrows():
            print(f"{i+1:>2}. {row['Normalized_Entity']} ({row['Number_of_Variants']} variants)")
        
        # Show some examples of variants
        print(f"\n{'='*60}")
        print(f"EXAMPLES OF MAPPING VARIANTS FOR TOP ENTITIES")
        print(f"{'='*60}")
        
        for i, row in missing_df.head(5).iterrows():
            print(f"\n{i+1}. {row['Normalized_Entity']}")
            variants = row['Mapping_Variants'].split(' | ')
            for j, variant in enumerate(variants[:5], 1):  # Show max 5 variants
                print(f"   {j}. {variant}")
            if len(variants) > 5:
                print(f"   ... and {len(variants) - 5} more variants")
        
        return missing_df
    
    else:
        print("✓ All normalized entities from the mapping are present in the NER dataset!")
        
        # Create empty file to indicate all entities were found
        output_file = 'entities_not_in_ner_dataset.csv'
        empty_df = pd.DataFrame(columns=[
            'Normalized_Entity', 'Number_of_Variants', 'Mapping_Variants', 
            'Status', 'Analysis_Date'
        ])
        empty_df.to_csv(output_file, index=False)
        print(f"✓ Empty results file created: {output_file}")
        
        return empty_df


# Run the analysis
if __name__ == "__main__":
    result_df = find_missing_entities()
    
    if result_df is not None:
        print(f"\n✅ ANALYSIS COMPLETED SUCCESSFULLY!")
        print(f"✓ Results saved to: 'entities_not_in_ner_dataset.csv'")
        if len(result_df) > 0:
            print(f"✓ Found {len(result_df)} normalized entities not in NER dataset")
        else:
            print(f"✓ All entities from mapping are present in NER dataset")
    else:
        print(f"\n❌ ANALYSIS FAILED - Please check error messages above")
