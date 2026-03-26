from flask import Flask, render_template, request, jsonify, redirect, session
from datetime import datetime
from groq import Groq
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "virus-secret-2026"


# ===== TRANSLATIONS =====
translations = {
    'hy': {
        # Navbar
        'home': '🏠 Գլխավոր',
        'map': '🗺️ Քարտեզ',
        'quiz': '🧪 Վիկտորինա',
        'leaderboard': '🏆 Ցուցակ',
        'simulator': '🧬 Սիմուլյատոր',
        'compare': '🔍 Համեմատել',
        
        # Footer
        'footer': '© 2026 Վիրուսների ուսումնասիրման հարթակ | Բոլոր իրավունքները պաշտպանված են',
        'footer_update': 'Տվյալները թարմացվել են՝ 2026 մարտի 7',
        
        # Hero
        'hero_title': '🦠 ՎԻՐՈՒՍՆԵՐԻ ԱՇԽԱՐՀ',
        'hero_subtitle': 'Բացահայտիր անտեսանելի թշնամուն. 2026 թվականի ամենաթարմ տվյալներ',
        'hero_stat1': 'Մարդկային վիրուսներ',
        'hero_stat2': 'Հետազոտություններ',
        'hero_stat3': 'Պատվաստանյութեր',
        
        # What are viruses
        'what_are_viruses': '🔬 Ի՞նչ են վիրուսները',
        'virus_desc1': 'Վիրուսները միկրոսկոպիկ ինֆեկցիոն ագենտներ են, որոնք կարող են վարակել բոլոր կենդանի օրգանիզմները։',
        'virus_desc2': 'Դրանք կանգնած են կենդանի և ոչ կենդանի սահմանին․ չեն կարող բազմանալ ինքնուրույն, սակայն ունեն գենետիկ նյութ։',
        'virus_desc3': '2026 թ․ հայտնի է 6590 վիրուս, որից 219-ը մարդկային։ Ամեն օր հայտնաբերվում է 2-3 նոր վիրուս։',
        'virus_fact': 'Վիրուսները 100 անգամ փոքր են բակտերիաներից',
        
        # Gallery
        'gallery': '🦠 Վիրուսների պատկերասրահ',
        'covid_facts': '🔴 Փաստեր',
        'ebola_facts': '⚠️ Վտանգ',
        'hiv_facts': '📊 Վիճակագրություն',
        'flu_facts': '📅 Սեզոնային',
        
        # Facts
        'facts_title': '🧠 10 ՓԱՍՏ, ՈՐ ՉԳԻՏԵԻՐ',
        
        # Bacteriophages
        'phage_title': '🧪 Բակտերիոֆագեր. վիրուսներ, որոնք որսում են բակտերիաներ',
        'phage_what': 'Ի՞նչ են բակտերիոֆագերը',
        'phage_what_text': 'Բակտերիոֆագերը (ֆագեր) վիրուսներ են, որոնք հատուկ վարակում են բակտերիաները։ Դրանք ամենատարածված կենսաբանական օբյեկտներն են Երկրի վրա. մեկ կաթիլ ջրում կարող են լինել միլիոնավոր ֆագեր։',
        'phage_structure': 'Կառուցվածքը',
        'phage_structure_text': 'Ֆագերն ունեն բարդ կառուցվածք՝ գլխիկ (որտեղ պահվում է գենետիկ նյութը), պոչ և պոչի թելիկներ, որոնք օգնում են ճանաչել բակտերիային։',
        'phage_work': 'Ինչպես են աշխատում',
        'phage_work_text': 'Ֆագերը կպչում են բակտերիայի մակերեսին, ներարկում իրենց ԴՆԹ-ն, և բակտերիան սկսում է արտադրել նոր ֆագեր, մինչև պայթի և ազատի դրանք։',
        'phage_therapy': 'Ֆագային թերապիա',
        'phage_therapy_text': 'Օգտագործվում է բակտերիալ ինֆեկցիաների բուժման համար, հատկապես երբ բակտերիաները կայուն են հակաբիոտիկների նկատմամբ։',
        
        # Timeline
        'timeline_title': '📜 Պատմական ամենամահաբեր համաճարակները (մ.թ.ա. - 2023)',
    },
    'ru': {
        # Navbar
        'home': '🏠 Главная',
        'map': '🗺️ Карта',
        'quiz': '🧪 Викторина',
        'leaderboard': '🏆 Таблица',
        'simulator': '🧬 Симулятор',
        'compare': '🔍 Сравнить',
        
        # Footer
        'footer': '© 2026 Платформа изучения вирусов | Все права защищены',
        'footer_update': 'Данные обновлены: 7 марта 2026',
        
        # Hero
        'hero_title': '🦠 МИР ВИРУСОВ',
        'hero_subtitle': 'Открой невидимого врага. Самые свежие данные 2026 года',
        'hero_stat1': 'Вирусов человека',
        'hero_stat2': 'Исследований',
        'hero_stat3': 'Вакцин',
        
        # What are viruses
        'what_are_viruses': '🔬 Что такое вирусы',
        'virus_desc1': 'Вирусы — это микроскопические инфекционные агенты, которые могут заражать все живые организмы.',
        'virus_desc2': 'Они находятся на грани живого и неживого: не могут размножаться самостоятельно, но имеют генетический материал.',
        'virus_desc3': 'В 2026 году известно 6590 вирусов, из которых 219 — человеческие. Каждый день обнаруживается 2-3 новых вируса.',
        'virus_fact': 'Вирусы в 100 раз меньше бактерий',
        
        # Gallery
        'gallery': '🦠 Галерея вирусов',
        'covid_facts': '🔴 Факты',
        'ebola_facts': '⚠️ Опасность',
        'hiv_facts': '📊 Статистика',
        'flu_facts': '📅 Сезонный',
        
        # Facts
        'facts_title': '🧠 10 ФАКТОВ, КОТОРЫХ ВЫ НЕ ЗНАЛИ',
        
        # Bacteriophages
        'phage_title': '🧪 Бактериофаги — вирусы, охотящиеся на бактерии',
        'phage_what': 'Что такое бактериофаги',
        'phage_what_text': 'Бактериофаги (фаги) — это вирусы, которые заражают бактерии. Они являются самыми распространенными биологическими объектами на Земле: в одной капле воды могут быть миллионы фагов.',
        'phage_structure': 'Строение',
        'phage_structure_text': 'Фаги имеют сложное строение: головка (где хранится генетический материал), хвост и хвостовые нити, которые помогают распознать бактерию.',
        'phage_work': 'Как работают',
        'phage_work_text': 'Фаги прикрепляются к поверхности бактерии, впрыскивают свою ДНК, и бактерия начинает производить новые фаги, пока не лопнет и не выпустит их.',
        'phage_therapy': 'Фаговая терапия',
        'phage_therapy_text': 'Используется для лечения бактериальных инфекций, особенно когда бактерии устойчивы к антибиотикам.',
        
        # Timeline
        'timeline_title': '📜 Самые смертоносные пандемии в истории (до н.э. - 2023)',
    },
    'en': {
        # Navbar
        'home': '🏠 Home',
        'map': '🗺️ Map',
        'quiz': '🧪 Quiz',
        'leaderboard': '🏆 Leaderboard',
        'simulator': '🧬 Simulator',
        'compare': '🔍 Compare',
        
        # Footer
        'footer': '© 2026 Virus Study Platform | All rights reserved',
        'footer_update': 'Data updated: March 7, 2026',
        
        # Hero
        'hero_title': '🦠 WORLD OF VIRUSES',
        'hero_subtitle': 'Discover the invisible enemy. Latest data for 2026',
        'hero_stat1': 'Human viruses',
        'hero_stat2': 'Research',
        'hero_stat3': 'Vaccines',
        
        # What are viruses
        'what_are_viruses': '🔬 What are viruses',
        'virus_desc1': 'Viruses are microscopic infectious agents that can infect all living organisms.',
        'virus_desc2': 'They stand on the border between living and non-living: cannot reproduce on their own, but have genetic material.',
        'virus_desc3': 'In 2026, 6,590 viruses are known, of which 219 are human. 2-3 new viruses are discovered every day.',
        'virus_fact': 'Viruses are 100 times smaller than bacteria',
        
        # Gallery
        'gallery': '🦠 Virus Gallery',
        'covid_facts': '🔴 Facts',
        'ebola_facts': '⚠️ Danger',
        'hiv_facts': '📊 Statistics',
        'flu_facts': '📅 Seasonal',
        
        # Facts
        'facts_title': '🧠 10 FACTS YOU DIDN\'T KNOW',
        
        # Bacteriophages
        'phage_title': '🧪 Bacteriophages - viruses that hunt bacteria',
        'phage_what': 'What are bacteriophages',
        'phage_what_text': 'Bacteriophages (phages) are viruses that specifically infect bacteria. They are the most common biological objects on Earth: one drop of water can contain millions of phages.',
        'phage_structure': 'Structure',
        'phage_structure_text': 'Phages have a complex structure: a head (where the genetic material is stored), a tail, and tail fibers that help recognize the bacteria.',
        'phage_work': 'How they work',
        'phage_work_text': 'Phages attach to the bacterial surface, inject their DNA, and the bacteria starts producing new phages until it bursts and releases them.',
        'phage_therapy': 'Phage therapy',
        'phage_therapy_text': 'Used to treat bacterial infections, especially when bacteria are resistant to antibiotics.',
        
        # Timeline
        'timeline_title': '📜 Deadliest pandemics in history (BC - 2023)',
    }
}


app = Flask(__name__)
app.secret_key = "virus-secret-2026"

# ===== LANGUAGE SUPPORT =====
def get_lang():
    # 1. Check URL parameter
    lang = request.args.get('lang')
    if lang in ['hy', 'ru', 'en']:
        session['lang'] = lang
        return lang
    # 2. Check session
    if 'lang' in session:
        return session['lang']
    # 3. Default Armenian
    return 'hy'


def get_translations(lang):
    return translations.get(lang, translations['hy'])

@app.context_processor
def inject_lang():
    lang = get_lang()
    return {'lang': lang}

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

print("=== API KEY DIAGNOSTICS ===")
print(f"GENAI_API_KEY exists: {os.environ.get('GENAI_API_KEY') is not None}")
print(f"GENAI_API_KEY length: {len(os.environ.get('GENAI_API_KEY', ''))}")
print(f"GOOGLE_API_KEY exists: {os.environ.get('GOOGLE_API_KEY') is not None}")
print("============================")

app = Flask(__name__)
app.secret_key = "virus-secret-2026"

# ================= DATABASE =================
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL', 'sqlite:///scores.db').replace('postgres://', 'postgresql://')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

    
# ================= SCORE MODEL =================
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    level_display = db.Column(db.String(50))
    level_class = db.Column(db.String(50))
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    percent = db.Column(db.String(10))
    date = db.Column(db.String(50))

    def to_dict(self):
        return {
            'name': self.name,
            'level': self.level,
            'level_display': self.level_display,
            'level_class': self.level_class,
            'score': self.score,
            'total': self.total,
            'percent': self.percent,
            'date': self.date
        }

# ==================== ՎԻԿՏՈՐԻՆԱՅԻ ՀԱՐՑԵՐ ====================
questions_db = {
    'very_easy': [
        {
            "question": "Վիրուսները տեսանելի են անզեն աչքով?",
            "options": ["Այո", "Ոչ"],
            "correct": 1,
            "explanation": "Վիրուսները շատ փոքր են (20-300 նանոմետր), տեսանելի են միայն էլեկտրոնային մանրադիտակով:"
        },
        {
            "question": "Գրիպը վիրուսային հիվանդությո՞ւն է",
            "options": ["Այո", "Ոչ"],
            "correct": 0,
            "explanation": "Գրիպը առաջանում է ինֆլուենցա վիրուսից:"
        },
        {
            "question": "Պատվաստումը պաշտպանում է վիրուսներից?",
            "options": ["Այո", "Ոչ"],
            "correct": 0,
            "explanation": "Պատվաստումները օգնում են իմունային համակարգին ճանաչել և պայքարել վիրուսների դեմ:"
        }
    ],
    'easy': [
        {
            "question": "Ո՞րն է ամենատարածված վիրուսային հիվանդությունը",
            "options": ["Գրիպ", "Էբոլա", "COVID-19", "Կարմրուկ"],
            "correct": 0,
            "explanation": "Գրիպը ամենատարածված վիրուսային հիվանդությունն է, ամեն տարի վարակում է միլիոնավոր մարդկանց:"
        },
        {
            "question": "Ինչպե՞ս են վիրուսները բազմանում",
            "options": ["Բաժանվելով", "Բջիջների ներսում պատճենվելով", "Սպորներով", "Պարզ բաժանմամբ"],
            "correct": 1,
            "explanation": "Վիրուսները կարող են բազմանալ միայն կենդանի բջիջների ներսում՝ օգտագործելով բջջի մեխանիզմները:"
        },
        {
            "question": "Ո՞ր օրգանիզմներն են ավելի փոքր՝ վիրուսները, թե բակտերիաները",
            "options": ["Վիրուսները", "Բակտերիաները", "Նույն չափն են", "Կախված է տեսակից"],
            "correct": 0,
            "explanation": "Վիրուսները 10-100 անգամ փոքր են բակտերիաներից:"
        },
        {
            "question": "Հակաբիոտիկները արդյունավետ են վիրուսների դեմ?",
            "options": ["Այո", "Ոչ", "Միայն որոշների", "Միայն գրիպի"],
            "correct": 1,
            "explanation": "Հակաբիոտիկները աշխատում են միայն բակտերիաների դեմ, ոչ թե վիրուսների:"
        }
    ],
    'medium': [
        {
            "question": "Ո՞ր վիրուսն է առաջացնում COVID-19 հիվանդությունը:",
            "options": ["SARS-CoV-2", "MERS-CoV", "H1N1", "Էբոլա"],
            "correct": 0,
            "explanation": "COVID-19-ը առաջացնում է SARS-CoV-2 վիրուսը:"
        },
        {
            "question": "Ո՞ր վիրուսն է առաջացնում ՁԻԱՀ",
            "options": ["HPV", "HIV", "HBV", "HSV"],
            "correct": 1,
            "explanation": "ՄԻԱՎ-ը (HIV) առաջացնում է ՁԻԱՀ:"
        },
        {
            "question": "Ո՞ր թվականին հայտնաբերվեց COVID-19-ի առաջին դեպքը",
            "options": ["2018", "2019", "2020", "2021"],
            "correct": 1,
            "explanation": "COVID-19-ի առաջին դեպքը գրանցվել է 2019 թվականի դեկտեմբերին Ուհանում, Չինաստան:"
        },
        {
            "question": "Ինչպե՞ս է փոխանցվում գրիպի վիրուսը",
            "options": ["Օդակաթիլային", "Արյան միջոցով", "Սեռական ճանապարհով", "Մոծակների միջոցով"],
            "correct": 0,
            "explanation": "Գրիպը փոխանցվում է օդակաթիլային ճանապարհով՝ հազալով, փռշտալով:"
        },
        {
            "question": "Ո՞ր վիրուսն է փոխանցվում մոծակների միջոցով",
            "options": ["COVID-19", "ՄԻԱՎ", "Դենգե", "Գրիպ"],
            "correct": 2,
            "explanation": "Դենգե տենդը փոխանցվում է Aedes մոծակների միջոցով:"
        },
        {
            "question": "Ո՞րն է ամենամահաբեր վիրուսը պատմության մեջ",
            "options": ["COVID-19", "Էբոլա", "Իսպանական գրիպ", "ՄԻԱՎ"],
            "correct": 2,
            "explanation": "Իսպանական գրիպը (1918-1920) սպանեց 50-100 միլիոն մարդ:"
        }
    ],
    'hard': [
        {
            "question": "Ո՞ր վիրուսն ունի ամենաբարձր մահացությունը",
            "options": ["Էբոլա", "COVID-19", "ՄԻԱՎ", "Գրիպ"],
            "correct": 0,
            "explanation": "Էբոլա վիրուսի մահացությունը կազմում է 50-90%, ինչը ամենաբարձրն է ցանկում:"
        },
        {
            "question": "Ո՞ր թվականին հայտնաբերվեց ՄԻԱՎ-ը",
            "options": ["1976", "1981", "1983", "1985"],
            "correct": 2,
            "explanation": "ՄԻԱՎ-ը հայտնաբերվել է 1983 թվականին Լյուկ Մոնտանյեի և Ռոբերտ Գալլոյի կողմից:"
        },
        {
            "question": "Ո՞ր վիրուսն է առաջացնում ջրծաղիկ",
            "options": ["Varicella zoster", "Variola major", "Rhinovirus", "Adenovirus"],
            "correct": 1,
            "explanation": "Ջրծաղիկը առաջացնում է Variola major վիրուսը: Այն վերացվել է 1980 թվականին:"
        },
        {
            "question": "Ինչպե՞ս է փոխանցվում մալարիան",
            "options": ["Օդակաթիլային", "Մոծակների միջոցով", "Արյան միջոցով", "Սեռական ճանապարհով"],
            "correct": 1,
            "explanation": "Մալարիան փոխանցվում է Anopheles մոծակների միջոցով, սակայն այն առաջանում է ոչ թե վիրուսից, այլ մակաբույծից (Plasmodium):"
        },
        {
            "question": "Ո՞րն է ամենատարածված հեպատիտը աշխարհում",
            "options": ["Հեպատիտ A", "Հեպատիտ B", "Հեպատիտ C", "Հեպատիտ D"],
            "correct": 1,
            "explanation": "Հեպատիտ B-ն ամենատարածվածն է. աշխարհում մոտ 2 միլիարդ մարդ վարակված է եղել:"
        },
        {
            "question": "Ո՞ր վիրուսն է առաջացնում խոզուկ",
            "options": ["Paramyxovirus", "Orthomyxovirus", "Adenovirus", "Rhinovirus"],
            "correct": 0,
            "explanation": "Խոզուկը (պարոտիտ) առաջանում է Paramyxovirus ընտանիքի վիրուսից:"
        },
        {
            "question": "Ո՞ր թվականին սկսվեց COVID-19 համավարակը",
            "options": ["2018", "2019", "2020", "2021"],
            "correct": 1,
            "explanation": "COVID-19-ի առաջին դեպքերը գրանցվել են 2019 թվականի դեկտեմբերին:"
        },
        {
            "question": "Ո՞ր վիրուսն է առաջացնում հերպես",
            "options": ["HSV-1", "HPV", "HIV", "HBV"],
            "correct": 0,
            "explanation": "Հերպեսը առաջանում է Herpes simplex virus-ից (HSV-1 և HSV-2):"
        }
    ],
    'very_hard': [
        {
            "question": "Ո՞ր թվականին ստեղծվեց առաջին պատվաստանյութը",
            "options": ["1796", "1885", "1901", "1950"],
            "correct": 0,
            "explanation": "1796 թվականին Էդվարդ Ջենները ստեղծեց ջրծաղիկի առաջին պատվաստանյութը:"
        },
        {
            "question": "Ո՞ր վիրուսն ունի ԴՆԹ գենոմ",
            "options": ["COVID-19", "Էբոլա", "Ադենովիրուս", "ՄԻԱՎ"],
            "correct": 2,
            "explanation": "Ադենովիրուսը ԴՆԹ վիրուս է, մինչդեռ COVID-19-ը, Էբոլան և ՄԻԱՎ-ը ՌՆԹ վիրուսներ են:"
        },
        {
            "question": "Ո՞րն է ամենամեծ վիրուսը",
            "options": ["Պիթովիրուս", "Էբոլա", "COVID-19", "ՄԻԱՎ"],
            "correct": 0,
            "explanation": "Պիթովիրուսը ամենամեծ հայտնի վիրուսն է (1.5 մկմ), տեսանելի է լուսային մանրադիտակով:"
        },
        {
            "question": "Քանի՞ տեսակի հեպատիտ կա",
            "options": ["3", "4", "5", "6"],
            "correct": 2,
            "explanation": "Հիմնականում 5 տեսակ՝ A, B, C, D, E: Գոյություն ունեն նաև այլ տեսակներ (G, TTV):"
        },
        {
            "question": "Ո՞ր վիրուսն է փոխանցվում կրծողների միջոցով",
            "options": ["Hantavirus", "Ebola", "Zika", "Dengue"],
            "correct": 0,
            "explanation": "Hantavirus-ը փոխանցվում է կրծողների (մկների) արտաթորանքի միջոցով:"
        },
        {
            "question": "Ո՞ր թվականին հայտնաբերվեց Էբոլա վիրուսը",
            "options": ["1976", "1981", "1990", "2000"],
            "correct": 0,
            "explanation": "Էբոլա վիրուսը հայտնաբերվել է 1976 թվականին Կոնգոյի ԴՀ-ում և Սուդանում:"
        },
        {
            "question": "Ո՞ր վիրուսն է առաջացնում կարմրուկ",
            "options": ["Morbillivirus", "Rubivirus", "Paramyxovirus", "Orthomyxovirus"],
            "correct": 0,
            "explanation": "Կարմրուկը առաջանում է Morbillivirus ցեղի վիրուսից (Paramyxoviridae ընտանիք):"
        },
        {
            "question": "Ի՞նչ է նշանակում ՌՆԹ հապավումը",
            "options": ["Ռիբոնուկլեինաթթու", "Ռիբոնուկլեոպրոտեին", "Ռեգուլյար նուկլեինաթթու", "Ռեալ նուկլեինաթթու"],
            "correct": 0,
            "explanation": "ՌՆԹ-ն ռիբոնուկլեինաթթու է, որը վիրուսների գենետիկ նյութն է:"
        },
        {
            "question": "Ո՞ր վիրուսն է առաջացնում դեղին տենդ",
            "options": ["Flavivirus", "Ebolavirus", "Marburgvirus", "Alphavirus"],
            "correct": 0,
            "explanation": "Դեղին տենդը առաջանում է Flavivirus ցեղի վիրուսից և փոխանցվում է մոծակների միջոցով:"
        },
        {
            "question": "Ո՞ր վիրուսն է առաջացնում կատաղություն",
            "options": ["Lyssavirus", "Lentivirus", "Deltavirus", "Alphavirus"],
            "correct": 0,
            "explanation": "Կատաղությունը առաջանում է Lyssavirus ցեղի վիրուսից (Rhabdoviridae ընտանիք):"
        }
    ]
}


def get_translations(lang):
    translations = {
        'hy': {
            'title': 'Վիրուսների հանրագիտարան 2026',
            'home': '🏠 Գլխավոր',
            'map': '🗺️ Քարտեզ',
            'quiz': '🧪 Վիկտորինա',
            'leaderboard': '🏆 Ցուցակ',
            'simulator': '🧬 Սիմուլյատոր',
            'compare': '🔍 Համեմատել',
            'footer': '© 2026 Վիրուսների ուսումնասիրման հարթակ | Բոլոր իրավունքները պաշտպանված են',
            'footer_update': 'Տվյալները թարմացվել են՝ 2026 մարտի 7',
            # ===== HERO SECTION =====
            'hero_title': '🦠 ՎԻՐՈՒՍՆԵՐԻ ԱՇԽԱՐՀ',
            'hero_subtitle': 'Բացահայտիր անտեսանելի թշնամուն. 2026 թվականի ամենաթարմ տվյալներ',
            'hero_stat1': 'Մարդկային վիրուսներ',
            'hero_stat2': 'Հետազոտություններ',
            'hero_stat3': 'Պատվաստանյութեր',
            # ===== WHAT ARE VIRUSES =====
            'what_are_viruses': '🔬 Ի՞նչ են վիրուսները',
            'virus_desc1': 'Վիրուսները միկրոսկոպիկ ինֆեկցիոն ագենտներ են, որոնք կարող են վարակել բոլոր կենդանի օրգանիզմները։',
            'virus_desc2': 'Դրանք կանգնած են կենդանի և ոչ կենդանի սահմանին․ չեն կարող բազմանալ ինքնուրույն, սակայն ունեն գենետիկ նյութ։',
            'virus_desc3': '2026 թ․ հայտնի է 6590 վիրուս, որից 219-ը մարդկային։ Ամեն օր հայտնաբերվում է 2-3 նոր վիրուս։',
            'virus_fact': 'Վիրուսները 100 անգամ փոքր են բակտերիաներից',
            # ===== GALLERY =====
            'gallery': '🦠 Վիրուսների պատկերասրահ',
            # ... շարունակել բոլոր թարգմանությունները
        },
        'ru': {
            # ... նույն կառուցվածքով ռուսերեն
        },
        'en': {
            # ... նույն կառուցվածքով անգլերեն
        }
    }
    return translations.get(lang, translations['hy'])


# ================= ROUTES =================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/map")
def map():
    return render_template("map.html")

@app.route("/compare")
def compare():
    from app import virus_data
    return render_template("compare.html", viruses=virus_data)

@app.route("/simulator")
def simulator():
    return render_template("simulator.html")

@app.route("/quiz")
def quiz_choice():
    return render_template("quiz_choice.html")

@app.route("/quiz/<level>")
def quiz(level):
    if level not in questions_db:
        return redirect("/quiz")
    questions = questions_db[level]
    return render_template(
        "quiz.html",
        level=level,
        questions=questions,
        total=len(questions)
    )

@app.route("/leaderboard")
def show_leaderboard():
    scores = Score.query.order_by(Score.percent.desc(), Score.score.desc()).limit(50).all()
    # DEBUG: remove this after testing
    print("=== LEADERBOARD DATA COUNT ===")
    print(f"Number of scores: {len(scores)}")
    for s in scores:
        print(f"ID: {s.id}, Name: {s.name}, Level: {s.level}, Display: {s.level_display}, Score: {s.score}")
    leaderboard_data = [s.to_dict() for s in scores]
    print(f"First item: {leaderboard_data[0] if leaderboard_data else 'No data'}")
    return render_template("leaderboard.html", leaderboard=leaderboard_data)

# ================= SAVE SCORE =================
@app.route("/save_score", methods=['POST'])
def save_score():
    data = request.json
    new_score = Score(
        name=data['name'],
        level=data['level'],
        level_display={
            'very_easy': 'Շատ հեշտ',
            'easy': 'Հեշտ',
            'medium': 'Միջին',
            'hard': 'Բարդ',
            'very_hard': 'Շատ բարդ'
        }[data['level']],
        level_class=data['level'],
        score=data['score'],
        total=data['total'],
        percent=data['percent'],
        date=datetime.now().strftime('%d.%m.%Y %H:%M')
    )
    db.session.add(new_score)
    db.session.commit()
    return jsonify({'success': True})

@app.route("/api/chat", methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        language = data.get('language', 'hy')
        
        # System prompt based on language
        prompts = {
            'hy': "Դու վիրուսաբանության փորձագետ ես: Պատասխանիր հայերենով, հակիրճ և հստակ:",
            'ru': "Ты эксперт по вирусологии: Отвечай на русском языке, кратко и четко:",
            'en': "You are a virology expert: Answer in English, concisely and clearly:"
        }
        system_prompt = prompts.get(language, prompts['hy'])
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        reply = response.choices[0].message.content
        return jsonify({'reply': reply})
        
    except Exception as e:
        print(f"Groq error: {e}")
        return jsonify({'reply': f'❌ Error: {str(e)}'}), 500

# ================= VIRUS DATA (for compare) =================
virus_data = {
    'covid19': {
        'name': 'COVID-19',
        'full_name': 'SARS-CoV-2',
        'type': 'ՌՆԹ վիրուս',
        'discovery': '2019',
        'transmission': 'Օդակաթիլային',
        'mortality': '2-3% (տարբերակված)',
        'vaccine': '✅ Կա',
        'symptoms': 'Ջերմություն, հազ, շնչառության դժվարություն, համի/հոտի կորուստ',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/e/e5/SARS-CoV-2_%28CDC-23312%29.png'
    },
    'ebola': {
        'name': 'Էբոլա',
        'full_name': 'Ebola virus',
        'type': 'ՌՆԹ վիրուս',
        'discovery': '1976',
        'transmission': 'Արյան և մարմնական հեղուկների միջոցով',
        'mortality': '50-90%',
        'vaccine': '✅ Կա (Ervebo)',
        'symptoms': 'Ջերմություն, արյունահոսություն, փսխում, լուծ',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Ebola_Virus_-_Electron_Micrograph.tiff/lossy-page1-1200px-Ebola_Virus_-_Electron_Micrograph.tiff.jpg'
    },
    'hiv': {
        'name': 'ՄԻԱՎ',
        'full_name': 'Human Immunodeficiency Virus',
        'type': 'ՌՆԹ վիրուս (ռետրովիրուս)',
        'discovery': '1983',
        'transmission': 'Արյուն, սեռական ճանապարհ, մայրից երեխային',
        'mortality': 'Բարձր առանց բուժման (80-90%)',
        'vaccine': '❌ Չկա (կա թերապիա)',
        'symptoms': 'Իմունային անբավարարություն, վարակների նկատմամբ զգայունություն',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/1/1a/HIV-budding-Color.jpg'
    },
    'flu': {
        'name': 'Գրիպ',
        'full_name': 'Influenza virus',
        'type': 'ՌՆԹ վիրուս',
        'discovery': '1933',
        'transmission': 'Օդակաթիլային',
        'mortality': '0.1% (սեզոնային), 2-3% (H5N1)',
        'vaccine': '✅ Կա (ամեն տարի)',
        'symptoms': 'Ջերմություն, հազ, մկանացավ, հոգնածություն',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/3/32/H1N1_Influenza_Virus_Particles_%288411599236%29.jpg'
    },
    'rotavirus': {
        'name': 'Ռոտավիրուս',
        'full_name': 'Rotavirus',
        'type': 'ՌՆԹ վիրուս',
        'discovery': '1973',
        'transmission': 'Ֆեկալ-օրալ',
        'mortality': '0.1% (բարձր երեխաների մոտ)',
        'vaccine': '✅ Կա',
        'symptoms': 'Լուծ, փսխում, ջերմություն, ջրազրկում',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/f/f7/Rotavirus.jpg'
    },
    'adenovirus': {
        'name': 'Ադենովիրուս',
        'full_name': 'Adenovirus',
        'type': 'ԴՆԹ վիրուս',
        'discovery': '1953',
        'transmission': 'Օդակաթիլային, կոնտակտային',
        'mortality': 'Ցածր (<1%)',
        'vaccine': '✅ Կա (որոշ տեսակների)',
        'symptoms': 'Մրսածություն, կոկորդի ցավ, կոնյուկտիվիտ',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/b/bc/Adenovirus_transmission_electron_micrograph_B82-0142_lores.jpg'
    }
}

# ================= ERROR HANDLER =================
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# ================= CREATE DB =================
with app.app_context():
    db.create_all()


@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory('.', 'robots.txt')

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['hy', 'ru', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))



