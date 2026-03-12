from flask import Flask, render_template, request, jsonify, redirect
from datetime import datetime
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'virus-site-secret-key-2026'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ==================== PostgreSQL ԿՈՆՖԻԳՈՒՐԱՑԻԱ ====================
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== LEADERBOARD ՄՈԴԵԼ ====================
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

# ==================== Google Gemini API ====================
genai.configure(api_key=os.environ.get('GENAI_API_KEY', ''))
genai_model = genai.GenerativeModel('gemini-2.0-flash')

# ==================== ՎԻՐՈՒՍՆԵՐԻ ՏՎՅԱԼՆԵՐ ====================
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
        'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/SARS-CoV-2_%28CDC-23312%29.png/300px-SARS-CoV-2_%28CDC-23312%29.png'
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
        'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/HIV_Virion-en.png/300px-HIV_Virion-en.png'
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
        'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Rotavirus_Reconstruction.jpg/300px-Rotavirus_Reconstruction.jpg'
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
        'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Adenovirus_3D.png/300px-Adenovirus_3D.png'
    }
}

# ==================== ՎԻԿՏՈՐԻՆԱՅԻ ՀԱՐՑԵՐ ====================
questions_db = {
    'very_easy': [...],  # քո հարցերը
    'easy': [...],
    'medium': [...],
    'hard': [...],
    'very_hard': [...]
}

# ==================== ԵՐԹՈՒԹՅՈՒՆՆԵՐ ====================
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
def quiz_level(level):
    if level not in questions_db:
        return redirect("/quiz")
    questions = questions_db[level]
    level_names = {
        'very_easy': 'Շատ հեշտ',
        'easy': 'Հեշտ',
        'medium': 'Միջին',
        'hard': 'Բարդ',
        'very_hard': 'Շատ բարդ'
    }
    level_classes = {
        'very_easy': 'very-easy',
        'easy': 'easy',
        'medium': 'medium',
        'hard': 'hard',
        'very_hard': 'very-hard'
    }
    return render_template("quiz.html", 
                          level=level,
                          level_name=level_names[level],
                          level_class=level_classes[level],
                          questions=questions,
                          total=len(questions))

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
        response = genai_model.generate_content(
            f"Դու վիրուսաբանության փորձագետ ես: Պատասխանիր հայերենով, հակիրճ և հստակ: Հարց: {user_message}"
        )
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'reply': f'❌ Սխալ: {str(e)}'}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# ==================== ՏՎՅԱԼՆԵՐԻ ԲԱԶԱՅԻ ՍՏԵՂԾՈՒՄ ====================
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
