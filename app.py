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
genai_client = genai.Client(api_key=GENAI_API_KEY)

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
        response = genai_client.models.generate_content(
            model='gemini-2.0-flash',  # <-- սա աշխատում է
            contents=f"Դու վիրուսաբանության փորձագետ ես: Պատասխանիր հայերենով, հակիրճ և հստակ: Հարց: {user_message}"
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