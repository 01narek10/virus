from flask import Flask, render_template, request, jsonify, redirect
from datetime import datetime
import google.generativeai as genai
import os

app = Flask(__name__)
app.secret_key = 'virus-site-secret-key-2026'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ==================== Google Gemini API Կարգավորում ====================
# ՔՈ ԲԱՆԱԼԻՆԸ (ստացիր https://aistudio.google.com/)
GENAI_API_KEY = os.environ.get('GENAI_API_KEY', '')
genai_model = genai.GenerativeModel('gemini-2.0-flash')

# ==================== ԳԼՈԲԱԼ ՑՈՒՑԱԿ ====================
leaderboard = []

# ==================== ՎԻՐՈՒՍՆԵՐԻ ՏՎՅԱԼՆԵՐ (համեմատման համար) ====================
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
        'image': 'data:image/jpeg;base64,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" alt="Rotavirus">
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
        'image': 'data:image/jpeg;base64,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" alt="Adenovirus">
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
    'hard': [],
    'very_hard': []
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
    return render_template("leaderboard.html", leaderboard=leaderboard[:50])

@app.route("/compare")
def compare():
    return render_template("compare.html", viruses=virus_data)

@app.route("/simulator")
def simulator():
    return render_template("simulator.html")

@app.route("/save_score", methods=['POST'])
def save_score():
    data = request.json
    entry = {
        'name': data['name'],
        'level': data['level'],
        'level_display': {
            'very_easy': 'Շատ հեշտ',
            'easy': 'Հեշտ',
            'medium': 'Միջին',
            'hard': 'Բարդ',
            'very_hard': 'Շատ բարդ'
        }[data['level']],
        'level_class': data['level'],
        'score': data['score'],
        'total': data['total'],
        'percent': data['percent'],
        'date': datetime.now().strftime('%d.%m.%Y %H:%M')
    }
    leaderboard.append(entry)
    leaderboard.sort(key=lambda x: (float(x['percent']), x['score']), reverse=True)
    return jsonify({'success': True})

# ==================== CHATBOT API (Google Gemini) ====================
@app.route("/api/chat", methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'reply': 'Խնդրում եմ գրել հարցը'}), 400

        # Gemini-ին հարցում
        response = genai_model.generate_content(
    f"Դու վիրուսաբանության փորձագետ ես: Պատասխանիր հայերենով, հակիրճ և հստակ: Հարց: {user_message}"
)
        
        return jsonify({'reply': response.text})
        
    except Exception as e:
        print(f"Chatbot error: {e}")  # Սերվերի կոնսոլում կտպի սխալը
        return jsonify({'reply': f'❌ Սխալ: {str(e)}'}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":

    app.run(debug=True)
