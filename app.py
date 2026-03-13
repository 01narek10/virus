from flask import Flask, render_template, request, jsonify, redirect
from datetime import datetime
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

print("=== DIAGNOSTICS ===")
print(f"GENAI_API_KEY exists: {os.environ.get('GENAI_API_KEY') is not None}")
print(f"GENAI_API_KEY length: {len(os.environ.get('GENAI_API_KEY', ''))}")
print(f"GOOGLE_API_KEY exists: {os.environ.get('GOOGLE_API_KEY') is not None}")
print("===================")

# SQLite ֆայլը persistent disk-ում
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'data', 'scores.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# Google Gemini կոնֆիգուրացիա
genai.configure(api_key=os.environ.get('GENAI_API_KEY', ''))
genai_model = genai.GenerativeModel('gemini-2.0-flash')

app.secret_key = 'virus-site-secret-key-2026'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ==================== PostgreSQL ԿՈՆՖԻԳՈՒՐԱՑԻԱ ====================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scores.db'
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

# ==================== ԵՐԹՈՒԹՅՈՒՆՆԵՐ ====================
@app.route("/health")
def health():
    return "OK", 200
    
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







