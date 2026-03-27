from flask import Flask, render_template, request, jsonify, redirect, session
from datetime import datetime
from groq import Groq
from flask_sqlalchemy import SQLAlchemy
import os

# ===== TRANSLATIONS DICTIONARY =====
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
        # Facts
        'facts_title': '🧠 10 ՓԱՍՏ, ՈՐ ՉԳԻՏԵԻՐ',
        # Phages
        'phage_title': '🧪 Բակտերիոֆագեր. վիրուսներ, որոնք որսում են բակտերիաներ',
        'phage_what': 'Ի՞նչ են բակտերիոֆագերը',
        'phage_what_text': 'Բակտերիոֆագերը (ֆագեր) վիրուսներ են, որոնք հատուկ վարակում են բակտերիաները։ Դրանք ամենատարածված կենսաբանական օբյեկտներն են Երկրի վրա.',
        'phage_structure': 'Կառուցվածքը',
        'phage_structure_text': 'Ֆագերն ունեն բարդ կառուցվածք՝ գլխիկ, պոչ և պոչի թելիկներ։',
        'phage_work': 'Ինչպես են աշխատում',
        'phage_work_text': 'Ֆագերը կպչում են բակտերիայի մակերեսին, ներարկում իրենց ԴՆԹ-ն, և բակտերիան սկսում է արտադրել նոր ֆագեր։',
        'phage_therapy': 'Ֆագային թերապիա',
        'phage_therapy_text': 'Օգտագործվում է բակտերիալ ինֆեկցիաների բուժման համար, հատկապես հակաբիոտիկակայուն բակտերիաների դեմ։',
        # Timeline
        'timeline_title': '📜 Պատմական ամենամահաբեր համաճարակները',
        # Map
        'map_title': '🗺️ Համաշխարհային վիրուսային բռնկումներ (2026)',
        'map_desc': 'Քարտեզում ներկայացված են <strong>1,000+ ակտիվ բռնկումներ</strong> 150+ երկրներից։',
        'high_risk': 'Բարձր ռիսկ (100+ դեպք)',
        'medium_risk': 'Միջին ռիսկ (20-99 դեպք)',
        'low_risk': 'Ցածր ռիսկ (1-19 դեպք)',
        'active_outbreaks': 'Ակտիվ բռնկումներ',
        'countries': 'Երկրներ',
        'total_cases': 'Ընդհանուր դեպքեր',
        'total_deaths': 'Ընդհանուր մահեր',
        # Armenian map
        'armenia_map_title': '🇦🇲 Հայաստանի և Հայկական լեռնաշխարհի քարտեզ (2026)',
        'armenia_map_desc': 'Քարտեզում ներկայացված են <strong>350+ բնակավայրեր</strong> Հայաստանից, Արցախից, Վրաստանից, Ադրբեջանից, Իրանից և Թուրքիայի հայկական պատմական տարածքներից։',
        'regions': 'Տարածաշրջաններ',
        'all': 'Բոլորը',
        'armenia': 'Հայաստան',
        'artsakh': 'Արցախ',
        'georgia': 'Վրաստան',
        'azerbaijan': 'Ադրբեջան',
        'turkey': 'Թուրքիա',
        'iran': 'Իրան',
        'historical': 'Պատմական',
        'settlements': 'Բնակավայրեր',
        'cities': 'Քաղաքներ',
        'villages': 'Գյուղեր',
        'historical_sites': 'Պատմական վայրեր',
        # Quiz
        'quiz_title': '🧪 Վիրուսաբանական վիկտորինա',
        'quiz_desc': 'Ստուգիր գիտելիքներդ վիրուսների մասին',
        'select_level': 'Ընտրիր դժվարության մակարդակ',
        'very_easy': 'Շատ հեշտ',
        'easy': 'Հեշտ',
        'medium': 'Միջին',
        'hard': 'Բարդ',
        'very_hard': 'Շատ բարդ',
        'your_name': 'Ձեր անունը',
        'start_quiz': 'Սկսել վիկտորինան',
        # Simulator
        'simulator_title': '🧬 Վիրուսային սիմուլյատոր',
        'simulator_desc': 'Դիտեք, թե ինչպես է վիրուսը տարածվում բջիջների միջև:',
        'infection_rate': '🦠 Վարակման արագություն',
        'mortality_rate': '💀 Մահացություն (%)',
        'vaccinated': '💉 Պատվաստվածներ (%)',
        'initial_infected': '🦠 Սկզբնական վարակվածներ',
        'healthy': '🟢 Առողջ',
        'infected': '🔴 Վարակված',
        'recovered': '🟡 Ապաքինված',
        'dead': '⚫ Մահացած',
        'start': '▶ Սկսել',
        'stop': '⏸️ Կանգնեցնել',
        'reset': '🔄 Վերականգնել',
        # Compare
        'compare_title': '🦠 Վիրուսների համեմատման գործիք',
        'compare_desc': 'Ընտրիր երկու վիրուս և տես դրանց տարբերությունները',
        'first_virus': '🔬 Առաջին վիրուս',
        'second_virus': '🔬 Երկրորդ վիրուս',
        'select': '-- Ընտրիր --',
        'criteria': 'Չափանիշ',
        'image': '🖼️ Պատկեր',
        'full_name': '📛 Լրիվ անուն',
        'type': '🧬 Տեսակ',
        'discovery': '📅 Հայտնաբերման տարեթիվ',
        'transmission': '🔄 Փոխանցման ձև',
        'mortality': '💀 Մահացություն',
        'vaccine': '💉 Պատվաստանյութ',
        'symptoms': '🤒 Ախտանիշներ',
        # Chatbot
        'chatbot_title': '🦠 Վիրուսային օգնական',
        'chatbot_welcome': 'Բարև, ես վիրուսային օգնականն եմ:',
        'chatbot_placeholder': 'Գրիր հարցդ...',
        'chatbot_thinking': '⏳ Մտածում եմ...',
        'chatbot_error': '❌ Ցանցային սխալ',
        # Errors
        '404_title': '404 - Էջը չի գտնվել',
        '404_message': 'Ցավոք, այս էջը գոյություն չունի:',
        '404_back': '🏠 Վերադառնալ գլխավոր'
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
        # Facts
        'facts_title': '🧠 10 ФАКТОВ, КОТОРЫХ ВЫ НЕ ЗНАЛИ',
        # Phages
        'phage_title': '🧪 Бактериофаги — вирусы, охотящиеся на бактерии',
        'phage_what': 'Что такое бактериофаги',
        'phage_what_text': 'Бактериофаги (фаги) — это вирусы, которые заражают бактерии. Они являются самыми распространенными биологическими объектами на Земле.',
        'phage_structure': 'Строение',
        'phage_structure_text': 'Фаги имеют сложное строение: головка, хвост и хвостовые нити.',
        'phage_work': 'Как работают',
        'phage_work_text': 'Фаги прикрепляются к поверхности бактерии, впрыскивают свою ДНК, и бактерия начинает производить новые фаги.',
        'phage_therapy': 'Фаговая терапия',
        'phage_therapy_text': 'Используется для лечения бактериальных инфекций, особенно когда бактерии устойчивы к антибиотикам.',
        # Timeline
        'timeline_title': '📜 Самые смертоносные пандемии в истории',
        # Map
        'map_title': '🗺️ Всемирные вирусные вспышки (2026)',
        'map_desc': 'На карте представлены <strong>1,000+ активных вспышек</strong> в 150+ странах.',
        'high_risk': 'Высокий риск (100+ случаев)',
        'medium_risk': 'Средний риск (20-99 случаев)',
        'low_risk': 'Низкий риск (1-19 случаев)',
        'active_outbreaks': 'Активных вспышек',
        'countries': 'Стран',
        'total_cases': 'Всего случаев',
        'total_deaths': 'Всего смертей',
        # Armenian map
        'armenia_map_title': '🇦🇲 Карта Армении и Армянского нагорья (2026)',
        'armenia_map_desc': 'На карте представлены <strong>350+ населенных пунктов</strong> из Армении, Арцаха, Грузии, Азербайджана, Ирана и исторических армянских территорий Турции.',
        'regions': 'Регионы',
        'all': 'Все',
        'armenia': 'Армения',
        'artsakh': 'Арцах',
        'georgia': 'Грузия',
        'azerbaijan': 'Азербайджан',
        'turkey': 'Турция',
        'iran': 'Иран',
        'historical': 'Исторические',
        'settlements': 'Населенных пунктов',
        'cities': 'Городов',
        'villages': 'Деревень',
        'historical_sites': 'Исторических мест',
        # Quiz
        'quiz_title': '🧪 Вирусологическая викторина',
        'quiz_desc': 'Проверь свои знания о вирусах',
        'select_level': 'Выбери уровень сложности',
        'very_easy': 'Очень легкий',
        'easy': 'Легкий',
        'medium': 'Средний',
        'hard': 'Сложный',
        'very_hard': 'Очень сложный',
        'your_name': 'Ваше имя',
        'start_quiz': 'Начать викторину',
        # Simulator
        'simulator_title': '🧬 Вирусный симулятор',
        'simulator_desc': 'Наблюдайте, как вирус распространяется между клетками.',
        'infection_rate': '🦠 Скорость заражения',
        'mortality_rate': '💀 Смертность (%)',
        'vaccinated': '💉 Вакцинированные (%)',
        'initial_infected': '🦠 Начально зараженные',
        'healthy': '🟢 Здоровые',
        'infected': '🔴 Зараженные',
        'recovered': '🟡 Выздоровевшие',
        'dead': '⚫ Умершие',
        'start': '▶ Старт',
        'stop': '⏸️ Стоп',
        'reset': '🔄 Сброс',
        # Compare
        'compare_title': '🦠 Инструмент сравнения вирусов',
        'compare_desc': 'Выбери два вируса и увидишь их различия',
        'first_virus': '🔬 Первый вирус',
        'second_virus': '🔬 Второй вирус',
        'select': '-- Выбери --',
        'criteria': 'Критерий',
        'image': '🖼️ Изображение',
        'full_name': '📛 Полное название',
        'type': '🧬 Тип',
        'discovery': '📅 Год открытия',
        'transmission': '🔄 Путь передачи',
        'mortality': '💀 Смертность',
        'vaccine': '💉 Вакцина',
        'symptoms': '🤒 Симптомы',
        # Chatbot
        'chatbot_title': '🦠 Вирусный помощник',
        'chatbot_welcome': 'Привет, я вирусный помощник:',
        'chatbot_placeholder': 'Напишите ваш вопрос...',
        'chatbot_thinking': '⏳ Думаю...',
        'chatbot_error': '❌ Ошибка сети',
        # Errors
        '404_title': '404 - Страница не найдена',
        '404_message': 'К сожалению, эта страница не существует.',
        '404_back': '🏠 Вернуться на главную'
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
        # Facts
        'facts_title': '🧠 10 FACTS YOU DIDN\'T KNOW',
        # Phages
        'phage_title': '🧪 Bacteriophages - viruses that hunt bacteria',
        'phage_what': 'What are bacteriophages',
        'phage_what_text': 'Bacteriophages (phages) are viruses that specifically infect bacteria. They are the most common biological objects on Earth.',
        'phage_structure': 'Structure',
        'phage_structure_text': 'Phages have a complex structure: a head, a tail, and tail fibers.',
        'phage_work': 'How they work',
        'phage_work_text': 'Phages attach to the bacterial surface, inject their DNA, and the bacteria starts producing new phages.',
        'phage_therapy': 'Phage therapy',
        'phage_therapy_text': 'Used to treat bacterial infections, especially when bacteria are resistant to antibiotics.',
        # Timeline
        'timeline_title': '📜 Deadliest pandemics in history',
        # Map
        'map_title': '🗺️ Global Viral Outbreaks (2026)',
        'map_desc': 'The map shows <strong>1,000+ active outbreaks</strong> in 150+ countries.',
        'high_risk': 'High risk (100+ cases)',
        'medium_risk': 'Medium risk (20-99 cases)',
        'low_risk': 'Low risk (1-19 cases)',
        'active_outbreaks': 'Active outbreaks',
        'countries': 'Countries',
        'total_cases': 'Total cases',
        'total_deaths': 'Total deaths',
        # Armenian map
        'armenia_map_title': '🇦🇲 Map of Armenia and Armenian Highlands (2026)',
        'armenia_map_desc': 'The map shows <strong>350+ settlements</strong> from Armenia, Artsakh, Georgia, Azerbaijan, Iran, and historical Armenian territories of Turkey.',
        'regions': 'Regions',
        'all': 'All',
        'armenia': 'Armenia',
        'artsakh': 'Artsakh',
        'georgia': 'Georgia',
        'azerbaijan': 'Azerbaijan',
        'turkey': 'Turkey',
        'iran': 'Iran',
        'historical': 'Historical',
        'settlements': 'Settlements',
        'cities': 'Cities',
        'villages': 'Villages',
        'historical_sites': 'Historical sites',
        # Quiz
        'quiz_title': '🧪 Virology Quiz',
        'quiz_desc': 'Test your knowledge about viruses',
        'select_level': 'Select difficulty level',
        'very_easy': 'Very Easy',
        'easy': 'Easy',
        'medium': 'Medium',
        'hard': 'Hard',
        'very_hard': 'Very Hard',
        'your_name': 'Your name',
        'start_quiz': 'Start Quiz',
        # Simulator
        'simulator_title': '🧬 Virus Simulator',
        'simulator_desc': 'Watch how a virus spreads between cells.',
        'infection_rate': '🦠 Infection rate',
        'mortality_rate': '💀 Mortality (%)',
        'vaccinated': '💉 Vaccinated (%)',
        'initial_infected': '🦠 Initial infected',
        'healthy': '🟢 Healthy',
        'infected': '🔴 Infected',
        'recovered': '🟡 Recovered',
        'dead': '⚫ Dead',
        'start': '▶ Start',
        'stop': '⏸️ Stop',
        'reset': '🔄 Reset',
        # Compare
        'compare_title': '🦠 Virus Comparison Tool',
        'compare_desc': 'Select two viruses and see their differences',
        'first_virus': '🔬 First virus',
        'second_virus': '🔬 Second virus',
        'select': '-- Select --',
        'criteria': 'Criteria',
        'image': '🖼️ Image',
        'full_name': '📛 Full name',
        'type': '🧬 Type',
        'discovery': '📅 Discovery year',
        'transmission': '🔄 Transmission',
        'mortality': '💀 Mortality',
        'vaccine': '💉 Vaccine',
        'symptoms': '🤒 Symptoms',
        # Chatbot
        'chatbot_title': '🦠 Virus Assistant',
        'chatbot_welcome': 'Hello, I\'m your virus assistant:',
        'chatbot_placeholder': 'Type your question...',
        'chatbot_thinking': '⏳ Thinking...',
        'chatbot_error': '❌ Network error',
        # Errors
        '404_title': '404 - Page Not Found',
        '404_message': 'Sorry, this page does not exist.',
        '404_back': '🏠 Back to Home'
    }
}

app = Flask(__name__)
app.secret_key = "virus-secret-2026"

# ===== DATABASE =====
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL', 'sqlite:///scores.db').replace('postgres://', 'postgresql://')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ===== GROQ =====
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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

@app.context_processor
def inject_lang():
    lang = get_lang()
    return {'lang': lang}

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['hy', 'ru', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

# ===== SCORE MODEL =====
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

# ===== ROUTES =====
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/map")
def map_page():
    return render_template("map.html")

@app.route("/quiz")
def quiz_choice():
    return render_template("quiz_choice.html")

@app.route("/quiz/<level>")
def quiz(level):
    return render_template("quiz.html", level=level)

@app.route("/leaderboard")
def show_leaderboard():
    scores = Score.query.order_by(Score.percent.desc(), Score.score.desc()).limit(50).all()
    return render_template("leaderboard.html", leaderboard=[s.to_dict() for s in scores])

@app.route("/compare")
def compare():
    return render_template("compare.html")

@app.route("/simulator")
def simulator():
    return render_template("simulator.html")

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
        
        return jsonify({'reply': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'reply': f'❌ Error: {str(e)}'}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
