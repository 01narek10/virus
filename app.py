from flask import Flask, render_template, request, jsonify, redirect, session
from datetime import datetime
from groq import Groq
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "virus-secret-2026"

# ===== DATABASE =====
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL', 'sqlite:///scores.db').replace('postgres://', 'postgresql://')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ===== GROQ =====
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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
        
questions_db = {
    'very_easy': [
        {"question": "Վիրուսները տեսանելի են անզեն աչքով?", "options": ["Այո", "Ոչ"], "correct": 1, "explanation": "Վիրուսները շատ փոքր են:"},
        {"question": "Գրիպը վիրուսային հիվանդությո՞ւն է", "options": ["Այո", "Ոչ"], "correct": 0, "explanation": "Գրիպը առաջանում է ինֆլուենցա վիրուսից:"},
        {"question": "Պատվաստումը պաշտպանում է վիրուսներից?", "options": ["Այո", "Ոչ"], "correct": 0, "explanation": "Պատվաստումը օգնում է իմունային համակարգին:"}
    ],
    'easy': [
        {"question": "Ո՞րն է ամենատարածված վիրուսային հիվանդությունը", "options": ["Գրիպ", "Էբոլա", "COVID-19", "Կարմրուկ"], "correct": 0, "explanation": "Գրիպը ամենատարածվածն է:"},
        # ... ավելացրու քո հարցերը
    ],
    'medium': [...],
    'hard': [...],
    'very_hard': [...]
}

@app.context_processor
def inject_translations():
    # Սա ժամանակավոր լուծում է, որպեսզի t-ն աշխատի բոլոր էջերում
    t = {
        'map_title': '🗺️ Համաշխարհային վիրուսային բռնկումներ (2026)',
        'map_desc': 'Քարտեզում ներկայացված են <strong>1,000+ ակտիվ բռնկումներ</strong> 150+ երկրներից։',
        'high_risk': 'Բարձր ռիսկ (100+ դեպք)',
        'medium_risk': 'Միջին ռիսկ (20-99 դեպք)',
        'low_risk': 'Ցածր ռիսկ (1-19 դեպք)',
        'no_data': 'Տվյալներ չկան',
        'active_outbreaks': 'Ակտիվ բռնկումներ',
        'countries': 'Երկրներ',
        'total_cases': 'Ընդհանուր դեպքեր',
        'total_deaths': 'Ընդհանուր մահեր',
        'armenia_map_title': '🇦🇲 Հայաստանի և Հայկական լեռնաշխարհի քարտեզ',
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
        'home': '🏠 Գլխավոր',
        'map': '🗺️ Քարտեզ',
        'quiz': '🧪 Վիկտորինա',
        'leaderboard': '🏆 Ցուցակ',
        'simulator': '🧬 Սիմուլյատոր',
        'compare': '🔍 Համեմատել',
        'footer': '© 2026 Վիրուսների ուսումնասիրման հարթակ | Բոլոր իրավունքները պաշտպանված են',
        'footer_update': 'Տվյալները թարմացվել են՝ 2026 մարտի 7',
        # index.html-ի բանալիներ
        'hero_title': '🦠 ՎԻՐՈՒՍՆԵՐԻ ԱՇԽԱՐՀ',
        'hero_subtitle': 'Բացահայտիր անտեսանելի թշնամուն. 2026 թվականի ամենաթարմ տվյալներ',
        'hero_stat1': 'Մարդկային վիրուսներ',
        'hero_stat2': 'Հետազոտություններ',
        'hero_stat3': 'Պատվաստանյութեր',
        'what_are_viruses': '🔬 Ի՞նչ են վիրուսները',
        'virus_desc1': 'Վիրուսները միկրոսկոպիկ ինֆեկցիոն ագենտներ են, որոնք կարող են վարակել բոլոր կենդանի օրգանիզմները։',
        'virus_desc2': 'Դրանք կանգնած են կենդանի և ոչ կենդանի սահմանին․ չեն կարող բազմանալ ինքնուրույն, սակայն ունեն գենետիկ նյութ։',
        'virus_desc3': '2026 թ․ հայտնի է 6590 վիրուս, որից 219-ը մարդկային։ Ամեն օր հայտնաբերվում է 2-3 նոր վիրուս։',
        'virus_fact': 'Վիրուսները 100 անգամ փոքր են բակտերիաներից',
        'gallery': '🦠 Վիրուսների պատկերասրահ',
        'facts_title': '🧠 10 ՓԱՍՏ, ՈՐ ՉԳԻՏԵԻՐ',
        'phage_title': '🧪 Բակտերիոֆագեր. վիրուսներ, որոնք որսում են բակտերիաներ',
        'phage_what': 'Ի՞նչ են բակտերիոֆագերը',
        'phage_what_text': 'Բակտերիոֆագերը (ֆագեր) վիրուսներ են, որոնք հատուկ վարակում են բակտերիաները։ Դրանք ամենատարածված կենսաբանական օբյեկտներն են Երկրի վրա. մեկ կաթիլ ջրում կարող են լինել միլիոնավոր ֆագեր։',
        'phage_structure': 'Կառուցվածքը',
        'phage_structure_text': 'Ֆագերն ունեն բարդ կառուցվածք՝ գլխիկ (որտեղ պահվում է գենետիկ նյութը), պոչ և պոչի թելիկներ, որոնք օգնում են ճանաչել բակտերիային։',
        'phage_work': 'Ինչպես են աշխատում',
        'phage_work_text': 'Ֆագերը կպչում են բակտերիայի մակերեսին, ներարկում իրենց ԴՆԹ-ն, և բակտերիան սկսում է արտադրել նոր ֆագեր, մինչև պայթի և ազատի դրանք։',
        'phage_therapy': 'Ֆագային թերապիա',
        'phage_therapy_text': 'Օգտագործվում է բակտերիալ ինֆեկցիաների բուժման համար, հատկապես երբ բակտերիաները կայուն են հակաբիոտիկների նկատմամբ։',
        'timeline_title': '📜 Պատմական ամենամահաբեր համաճարակները (մ.թ.ա. - 2023)',
    }
    return {'t': t, 'lang': 'hy'}

# ===== VIRUS DATA FOR COMPARE =====
virus_data = {
    'covid19': {
        'name': 'COVID-19', 'full_name': 'SARS-CoV-2', 'type': 'ՌՆԹ վիրուս',
        'discovery': '2019', 'transmission': 'Օդակաթիլային', 'mortality': '2-3%',
        'vaccine': '✅ Կա', 'symptoms': 'Ջերմություն, հազ, շնչառության դժվարություն',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/SARS-CoV-2_%28CDC-23312%29.png/500px-SARS-CoV-2_%28CDC-23312%29.png'
    },
    'ebola': {
        'name': 'Էբոլա', 'full_name': 'Ebola virus', 'type': 'ՌՆԹ վիրուս',
        'discovery': '1976', 'transmission': 'Արյան միջոցով', 'mortality': '50-90%',
        'vaccine': '✅ Կա', 'symptoms': 'Արյունահոսություն, ջերմություն',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Ebola_Virus_-_Electron_Micrograph.tiff/lossy-page1-1200px-Ebola_Virus_-_Electron_Micrograph.tiff.jpg'
    },
    'hiv': {
        'name': 'ՄԻԱՎ', 'full_name': 'HIV', 'type': 'ՌՆԹ վիրուս',
        'discovery': '1983', 'transmission': 'Արյուն, սեռական', 'mortality': 'Բարձր',
        'vaccine': '❌ Չկա', 'symptoms': 'Իմունային անբավարարություն',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/1/1a/HIV-budding-Color.jpg'
    },
    'flu': {
        'name': 'Գրիպ', 'full_name': 'Influenza', 'type': 'ՌՆԹ վիրուս',
        'discovery': '1933', 'transmission': 'Օդակաթիլային', 'mortality': '0.1%',
        'vaccine': '✅ Կա', 'symptoms': 'Ջերմություն, հազ, մկանացավ',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/3/32/H1N1_Influenza_Virus_Particles_%288411599236%29.jpg'
    },
    'rotavirus': {
        'name': 'Ռոտավիրուս', 'full_name': 'Rotavirus', 'type': 'ՌՆԹ վիրուս',
        'discovery': '1973', 'transmission': 'Ֆեկալ-օրալ', 'mortality': '0.1%',
        'vaccine': '✅ Կա', 'symptoms': 'Լուծ, փսխում, ջերմություն',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/f/f7/Rotavirus.jpg'
    },
    'adenovirus': {
        'name': 'Ադենովիրուս', 'full_name': 'Adenovirus', 'type': 'ԴՆԹ վիրուս',
        'discovery': '1953', 'transmission': 'Օդակաթիլային', 'mortality': '<1%',
        'vaccine': '✅ Կա', 'symptoms': 'Մրսածություն, կոկորդի ցավ',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/b/bc/Adenovirus_transmission_electron_micrograph_B82-0142_lores.jpg'
    }
}

# ===== ROUTES =====

@app.context_processor
def inject_lang():
    lang = get_lang()
    return {'lang': lang}

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['hy', 'ru', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))
    
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
    return render_template("compare.html", viruses=virus_data)

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



