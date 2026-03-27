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

# ===== TEMPORARY FIX: add t variable to all templates =====
@app.context_processor
def inject_t():
    # Create a simple dictionary with common translations
    t = {
        'home': '🏠 Գլխավոր',
        'map': '🗺️ Քարտեզ',
        'quiz': '🧪 Վիկտորինա',
        'leaderboard': '🏆 Ցուցակ',
        'simulator': '🧬 Սիմուլյատոր',
        'compare': '🔍 Համեմատել',
        'footer': '© 2026 Վիրուսների ուսումնասիրման հարթակ | Բոլոր իրավունքները պաշտպանված են',
        'footer_update': 'Տվյալները թարմացվել են՝ 2026 մարտի 7',
        'chatbot_title': '🦠 Վիրուսային օգնական',
        'chatbot_welcome': 'Բարև, ես վիրուսային օգնականն եմ:',
        'chatbot_placeholder': 'Գրիր հարցդ...',
        'chatbot_thinking': '⏳ Մտածում եմ...',
        'chatbot_error': '❌ Ցանցային սխալ',
    }
    return {'t': t}

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
