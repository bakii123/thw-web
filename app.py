from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import requests
import os
import sqlite3
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-super-secret-key-change-this')
CORS(app, supports_credentials=True)

# Hugging Face API Configuration (deprecated - using local AI fallback)
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HF_TOKEN = os.getenv('HF_TOKEN')  # set in .env

# Translation dictionaries for multi-language support
TRANSLATIONS = {
    'en': {
        'app_title': 'Soul Companion',
        'tagline': 'Find peace through conversation',
        'login': 'Login',
        'signup': 'Sign Up',
        'enter': 'Enter Conversation',
        'create_account': 'Create Account',
        'pricing': 'Premium: $9.99/month for unlimited',
        'share': 'Share what\'s on your mind...',
        'anonymous': 'Anonymous',
        'guest': 'Guest',
        'upgrade': 'Upgrade',
        'logout': 'Logout',
        'premium': 'Premium 🌟',
        'dr_elara': 'Dr. Elara',
        'typing': 'Dr. Elara is typing...',
        'privacy': 'Welcome to your private, safe space. I\'m here to listen to you without judgment. To better understand your inner world and provide appropriate support, would you allow me to ask you a few simple questions first? Everything you share here will remain completely confidential between us.',
        'thanks': 'Thank you for sharing so deeply with me. I hear you, and I want you to know that what you\'re feeling is valid.',
        'paywall': 'You\'ve viewed your initial assessment. To continue receiving personalized insights and support, please upgrade to Premium.',
        'unlock': 'Unlock Full Session',
    },
    'ar': {
        'app_title': 'رفيق الروح',
        'tagline': 'ابحث عن السلام من خلال المحادثة',
        'login': 'دخول',
        'signup': 'اشتراك',
        'enter': 'ادخل المحادثة',
        'create_account': 'إنشاء حساب',
        'pricing': 'برميوم: 9.99 دولار/الشهر غير محدود',
        'share': 'شارك ما في بالك...',
        'anonymous': 'مجهول',
        'guest': 'ضيف',
        'upgrade': 'ترقية',
        'logout': 'تسجيل الخروج',
        'premium': 'برميوم 🌟',
        'dr_elara': 'د. إيلارا',
        'typing': 'د. إيلارا تكتب...',
        'privacy': 'أهلاً بك في مساحتك الخاصة والآمنة. أنا هنا لأسمعك دون إطلاق أحكام. لكي أستطيع فهم عالمك الداخلي وتقديم الدعم المناسب لك، هل تسمح لي بأن أطرح عليك بعض الأسئلة البسيطة أولاً؟ كل ما ستشاركه هنا سيبقى سرياً تماماً بيننا.',
        'thanks': 'شكراً لك على مشاركتك العميقة معي. أسمعك وأريد أن تعرف أن مشاعرك صحيحة.',
        'paywall': 'لقد رأيت تقييمك الأولي. للاستمرار في تلقي رؤى شخصية ودعم، يرجى الترقية إلى Premium.',
        'unlock': 'فتح الجلسة الكاملة',
    },
    'fr': {
        'app_title': 'Compagnon de l\'Âme',
        'tagline': 'Trouvez la paix par la conversation',
        'login': 'Connexion',
        'signup': 'S\'inscrire',
        'enter': 'Entrer en conversation',
        'create_account': 'Créer un compte',
        'pricing': 'Premium: 9,99 $/mois illimité',
        'share': 'Partagez ce qui vous préoccupe...',
        'anonymous': 'Anonyme',
        'guest': 'Invité',
        'upgrade': 'Mettre à niveau',
        'logout': 'Déconnexion',
        'premium': 'Premium 🌟',
        'dr_elara': 'Dr. Elara',
        'typing': 'Dr. Elara écrit...',
        'privacy': 'Bienvenue dans votre espace privé et sûr. Je suis ici pour vous écouter sans jugement. Pour mieux comprendre votre monde intérieur et vous offrir un soutien approprié, me permettriez-vous de vous poser d\'abord quelques questions simples? Tout ce que vous partagez ici restera complètement confidentiel entre nous.',
        'thanks': 'Merci de partager si profondément avec moi. Je vous entends et je veux que vous sachiez que vos sentiments sont valides.',
        'paywall': 'Vous avez consulté votre évaluation initiale. Pour continuer à recevoir des insights personnalisés et un soutien, veuillez passer à Premium.',
        'unlock': 'Déverrouiller la session complète',
    }
}

# Advice message translations
ADVICE_TRANSLATIONS = {
    'en': {
        'thanks': 'Thank you for sharing so deeply with me. I hear you, and I want you to know that what you\'re feeling is valid.',
        'sad_intro': 'I notice you\'re experiencing some sadness or low mood. This is common, and there are concrete steps you can take:',
        'sad_tips': [
            '• Start with small, achievable goals each day (even 5 minutes of activity helps)',
            '• Try to maintain basic routines: meals, hygiene, brief time outside',
            '• Connect with at least one person you trust, even briefly',
            '• Consider if professional support (therapist/counselor) might help long-term'
        ],
        'anxiety_intro': 'Anxiety and stress can feel overwhelming. Here are immediate tools:',
        'anxiety_tips': [
            '• Try the 5-4-3-2-1 grounding technique: name 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste',
            '• Deep breathing: inhale 4 counts, hold 4, exhale 4 (repeat 5 times)',
            '• Limit caffeine and social media—both can amplify anxiety',
            '• Physical movement, even a short walk, reduces nervous energy'
        ],
        'sleep_intro': 'Sleep disruption often worsens everything else. Try:',
        'sleep_tips': [
            '• A consistent bedtime, even on weekends',
            '• No screens 30 minutes before bed',
            '• Keep your room cool and dark',
            '• If racing thoughts occur, try journaling before bed'
        ],
        'reminders': 'Important Reminders:',
        'reminder_tips': [
            '• I\'m an AI companion, not a replacement for licensed mental health care',
            '• If you have safety concerns, please contact a crisis line (988 in US)',
            '• Progress takes time—be patient and compassionate with yourself',
            '• You deserve support, and reaching out (like you did here) is strength'
        ],
        'continue': 'Feel free to continue our conversation with any questions or concerns.'
    },
    'ar': {
        'thanks': 'شكراً لك على مشاركتك العميقة معي. أسمعك وأريد أن تعرف أن مشاعرك صحيحة.',
        'sad_intro': 'لاحظت أنك تعاني من بعض الحزن أو انخفاض المزاج. هذا شائع وهناك خطوات ملموسة يمكنك اتخاذها:',
        'sad_tips': [
            '• ابدأ بأهداف صغيرة وقابلة للتحقيق كل يوم (حتى 5 دقائق من النشاط تساعد)',
            '• حاول الحفاظ على روتين أساسي: الطعام والنظافة والوقت في الخارج',
            '• تواصل مع شخص واحد على الأقل تثق به، حتى لو كان بإيجاز',
            '• فكر فيما إذا كان الدعم المهني (معالج/استشاري) قد يساعد على المدى الطويل'
        ],
        'anxiety_intro': 'يمكن أن تبدو القلق والضغط ساحقة. إليك بعض الأدوات الفورية:',
        'anxiety_tips': [
            '• جرب تقنية 5-4-3-2-1: سمّ 5 أشياء تراها، 4 تلمسها، 3 تسمعها، 2 تشمها، 1 تتذوقها',
            '• التنفس العميق: خذ نفساً لمدة 4 عدات، احبسه 4 عدات، أخرجه 4 عدات (كرر 5 مرات)',
            '• قلل الكافيين ووسائل التواصل - كلاهما يضخم القلق',
            '• الحركة البدنية حتى المشي القصير تقلل الطاقة العصبية'
        ],
        'sleep_intro': 'اضطراب النوم غالباً يسوء كل شيء. حاول:',
        'sleep_tips': [
            '• وقت نوم ثابت، حتى في نهاية الأسبوع',
            '• لا شاشات لمدة 30 دقيقة قبل النوم',
            '• اجعل غرفتك باردة ومظلمة',
            '• إذا حدثت أفكار متسارعة، جرب كتابة اليوميات قبل النوم'
        ],
        'reminders': 'تذكيرات مهمة:',
        'reminder_tips': [
            '• أنا رفيق ذكاء اصطناعي، وليس بديلاً عن رعاية الصحة العقلية المرخصة',
            '• إذا كان لديك مخاوف أمان، يرجى الاتصال بخط الأزمات',
            '• التقدم يستغرق وقتاً - كن صبوراً ولطيفاً مع نفسك',
            '• تستحق الدعم والوصول إليه (كما فعلت هنا) هو قوة'
        ],
        'continue': 'لا تتردد في متابعة محادثتنا مع أي أسئلة أو مخاوف.'
    },
    'fr': {
        'thanks': 'Merci de partager si profondément avec moi. Je vous entends et je veux que vous sachiez que vos sentiments sont valides.',
        'sad_intro': 'Je remarque que vous éprouvez une certaine tristesse ou une baisse d\'humeur. C\'est courant et il y a des mesures concrètes que vous pouvez prendre:',
        'sad_tips': [
            '• Commencez par des objectifs petits et réalisables chaque jour (même 5 minutes d\'activité aident)',
            '• Essayez de maintenir les routines de base: repas, hygiène, temps dehors',
            '• Connectez-vous avec au moins une personne de confiance, même brièvement',
            '• Considérez si le soutien professionnel (thérapeute/conseiller) pourrait aider à long terme'
        ],
        'anxiety_intro': 'L\'anxiété et le stress peuvent sembler accablants. Voici quelques outils immédiats:',
        'anxiety_tips': [
            '• Essayez la technique 5-4-3-2-1: nommez 5 choses que vous voyez, 4 que vous touchez, 3 que vous entendez, 2 que vous sentez, 1 que vous goûtez',
            '• Respiration profonde: inspirez 4 comptes, retenez 4, expirez 4 (répétez 5 fois)',
            '• Limitez la caféine et les médias sociaux - les deux amplifient l\'anxiété',
            '• Le mouvement physique, même une courte promenade, réduit l\'énergie nerveuse'
        ],
        'sleep_intro': 'La perturbation du sommeil aggrave souvent tout. Essayez:',
        'sleep_tips': [
            '• Une heure de coucher régulière, même le week-end',
            '• Pas d\'écrans 30 minutes avant le coucher',
            '• Gardez votre chambre fraîche et sombre',
            '• Si des pensées qui s\'accélèrent surviennent, essayez de tenir un journal avant le coucher'
        ],
        'reminders': 'Rappels importants:',
        'reminder_tips': [
            '• Je suis un compagnon IA, pas un remplaçant des soins de santé mentale agréés',
            '• Si vous avez des préoccupations de sécurité, veuillez contacter une ligne d\'écoute',
            '• Les progrès prennent du temps - soyez patient et compatissant envers vous-même',
            '• Vous méritez du soutien et atteindre (comme vous l\'avez fait ici) est une force'
        ],
        'continue': 'N\'hésitez pas à poursuivre notre conversation avec toute question ou préoccupation.'
    }
}

def generate_local_advice(intake_answers, lang='en'):
    """Generate personalized psychiatric advice using HF API with full intake context."""
    
    # Build comprehensive user profile from all answers
    user_profile = []
    intake_questions = INTAKE_QUESTIONS_DICT.get(lang, INTAKE_QUESTIONS_DICT['en'])
    
    for i, question in enumerate(intake_questions):
        answer_data = intake_answers.get(str(i), {})
        answer = answer_data.get('answer', '').strip()
        if answer:
            user_profile.append(f"Q: {question}\nA: {answer}")
    
    user_context = "\n\n".join(user_profile)
    
    # Create language-specific system and user prompts
    if lang == 'ar':
        system_prompt = (
            "أنت د. إيلارا، متخصصة نفسية عاطفية واحترافية وسرية للغاية. "
            "بناءً على إجابات المريض، قدمي رؤى نفسية شخصية وحكيمة وعملية. "
            "اكتبي 3 فقرات فقط (كل فقرة 3-4 جمل) حول:\n"
            "1. ما فهمتِ عن حالة المريض النفسية والعاطفية.\n"
            "2. الأنماط والعوامل الرئيسية التي تؤثر على صحته النفسية.\n"
            "3. خطوات عملية وآنية وآمنة يمكنه اتخاذها فوراً.\n"
            "لا تتضمني تحذيرات أو إخلاءات مسؤولية. اجعليها شخصية وقيّمة وملهمة."
        )
        user_prompt = f"إليك إجابات المريض خلال جلستنا الأولى:\n\n{user_context}\n\nقدمي رؤيتك النفسية الشخصية الآن."
    elif lang == 'fr':
        system_prompt = (
            "Vous êtes Dr. Elara, une psychologue professionnelle, empathique et hautement confidentielle. "
            "En fonction des réponses du patient, fournissez des perspectives psychologiques personnalisées, sages et pratiques. "
            "Écrivez 3 paragraphes seulement (chaque paragraphe 3-4 phrases) couvrant:\n"
            "1. Ce que vous avez compris sur l'état psychologique et émotionnel du patient.\n"
            "2. Les modèles et facteurs clés affectant sa santé mentale.\n"
            "3. Des étapes pratiques, immédiates et sûres qu'il peut prendre maintenant.\n"
            "N'incluez pas d'avertissements ou de clauses de non-responsabilité. Rendez-la personnelle, éclairante et inspirante."
        )
        user_prompt = f"Voici les réponses du patient de notre première session:\n\n{user_context}\n\nFournissez maintenant votre perspective psychologique personnelle."
    else:  # English
        system_prompt = (
            "You are Dr. Elara, a professional, empathetic, and highly confidential psychologist. "
            "Based on the patient's answers, provide personalized psychological insights that are wise, practical, and directly actionable. "
            "Write exactly 3 paragraphs (each 3-4 sentences) covering:\n"
            "1. What you've understood about the patient's psychological and emotional state.\n"
            "2. The key patterns and factors affecting their mental health.\n"
            "3. Practical, immediate, and safe steps they can take right now.\n"
            "Do not include warnings or disclaimers. Make it personal, insightful, and inspiring."
        )
        user_prompt = f"Here are the patient's answers from our first session:\n\n{user_context}\n\nProvide your personalized psychological perspective now."
    
    # Call HF API to generate personalized response
    ai_response = get_hf_response(system_prompt, user_prompt)
    
    if ai_response:
        return ai_response.strip()
    else:
        # Fallback if API fails - still provide something meaningful
        if lang == 'ar':
            return "شكراً لك على ثقتك بي. بناءً على ما شاركته، أرى أنك تمر بفترة تحتاج إلى عناية واهتمام. الخطوة الأولى هي الاعتراف بما تشعر به، وأنت فعلت ذلك بشجاعة اليوم.\n\nأدعوك للتركيز على ما يمنحك الهدوء والسلام - سواء كان الحركة، الكتابة، أو التواصل مع شخص تثق به. التغيير الحقيقي يأتي من خطوات صغيرة متسقة.\n\nأنا هنا لدعمك في رحلتك نحو الشعور بتحسن. تذكر أن طلب المساعدة - مثل ما تفعله الآن - هو علامة قوة وليس ضعف."
        elif lang == 'fr':
            return "Merci de votre confiance. D'après ce que vous avez partagé, je vois que vous traversez une période qui mérite attention et soin. La première étape est de reconnaître ce que vous ressentez, et vous l'avez fait avec courage aujourd'hui.\n\nJe vous encourage à vous concentrer sur ce qui vous apporte calme et paix - que ce soit le mouvement, l'écriture, ou parler à quelqu'un de confiance. Le vrai changement vient de petites étapes cohérentes.\n\nJe suis là pour vous soutenir dans votre chemin vers une meilleure santé mentale. Rappelez-vous que chercher de l'aide - comme vous le faites maintenant - est un signe de force, pas de faiblesse."
        else:
            return "Thank you for trusting me with your thoughts. From what you've shared, I can see you're navigating a meaningful journey. The fact that you're here, reflecting and opening up, shows real courage and self-awareness.\n\nFocus on what brings you moments of peace—whether that's movement, creating, or connecting with someone you trust. Real change builds from small, consistent steps forward.\n\nI'm here to support you through this. Remember, seeking help and reflection—like you're doing right now—is a profound act of strength. You deserve that support."

# In-memory guest counters (non-persistent)
GUEST_COUNTS = {}

# Intake questions in multiple languages (10 core categories)
INTAKE_QUESTIONS_DICT = {
    'en': [
        "What brought you here today? What's on your mind?",
        "How long have you been experiencing these feelings or concerns?",
        "How would you describe your mood most days?",
        "How are you sleeping? Is sleep an issue for you right now?",
        "What are the biggest stresses or challenges in your life right now?",
        "How do you usually cope with stress? What helps you feel better?",
        "How is your relationship with family and friends?",
        "Do you feel supported by the people around you, or do you often feel lonely?",
        "Have you ever had thoughts about harming yourself or others?",
        "What changes would you most like to see in your life right now?"
    ],
    'ar': [
        "ما الذي أحضرك هنا اليوم؟ ما الذي يشغل بالك؟",
        "منذ متى تعاني من هذه المشاعر أو المخاوف؟",
        "كيف تصف مزاجك معظم الأيام؟",
        "كيف يكون نومك؟ هل النوم مشكلة بالنسبة لك الآن؟",
        "ما أكبر الضغوطات أو التحديات في حياتك الآن؟",
        "كيف تتعامل عادة مع الضغوط؟ ما الذي يساعدك على الشعور بتحسن؟",
        "كيف هي علاقتك مع عائلتك وأصدقائك؟",
        "هل تشعر بالدعم من الناس من حولك أم أنك تشعر بالوحدة غالباً؟",
        "هل فكرت من قبل في إيذاء نفسك أو الآخرين؟",
        "ما التغييرات التي تود رؤيتها في حياتك الآن؟"
    ],
    'fr': [
        "Qu'est-ce qui vous a conduit ici aujourd'hui? Qu'y a-t-il dans votre esprit?",
        "Depuis combien de temps éprouvez-vous ces sentiments ou ces préoccupations?",
        "Comment décriveriez-vous votre humeur la plupart du temps?",
        "Comment est votre sommeil? Le sommeil est-il un problème pour vous en ce moment?",
        "Quels sont les plus grands stress ou défis dans votre vie en ce moment?",
        "Comment gérez-vous généralement le stress? Qu'est-ce qui vous aide à vous sentir mieux?",
        "Comment est votre relation avec votre famille et vos amis?",
        "Vous sentez-vous soutenu par les gens autour de vous ou vous sentez-vous souvent seul?",
        "Avez-vous jamais pensé à vous faire du mal ou à faire du mal à autrui?",
        "Quels changements aimeriez-vous le plus voir dans votre vie en ce moment?"
    ]
}

# Keep the default English questions for backward compatibility
INTAKE_QUESTIONS = INTAKE_QUESTIONS_DICT['en']

def init_db():
    conn = sqlite3.connect('soul_companion.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password_hash TEXT NOT NULL,
                 messages_used INTEGER DEFAULT 0,
                 is_premium BOOLEAN DEFAULT FALSE,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    conn.commit()
    conn.close()

init_db()

def get_hf_response(system_prompt, user_prompt):
    """Call Hugging Face Inference API or use local fallback for AI response."""
    if not HF_TOKEN:
        return None  # Signal to use local fallback
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    full_prompt = f"System:\n{system_prompt}\n\nUser:\n{user_prompt}\n\nAssistant:\n"
    
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True,
            "return_full_text": False
        }
    }
    
    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
                return result[0]['generated_text'].strip()
            if isinstance(result, dict) and 'generated_text' in result:
                return result['generated_text'].strip()
        return None  # Fallback to local
    except Exception as e:
        print(f"HF API Error: {e}")
        return None  # Fallback to local


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/user_status')
def user_status():
    # Return basic session info and current phase if set
    if 'user_id' in session:
        user_id = session['user_id']
        conn = sqlite3.connect('soul_companion.db')
        c = conn.cursor()
        c.execute("SELECT username, messages_used, is_premium FROM users WHERE id = ?", (user_id,))
        r = c.fetchone()
        conn.close()
        if r:
            return jsonify({
                'logged_in': True,
                'user_id': user_id,
                'username': r[0],
                'messages_used': r[1],
                'is_premium': bool(r[2]),
                'phase': session.get('phase', 'questioning' if session.get('intake_index') else 'advice'),
                'can_message': r[2] or r[1] < 5
            })
    # not logged in; client can use guest mode
    return jsonify({'logged_in': False, 'phase': session.get('phase', None)})


@app.route('/api/start_intake', methods=['POST'])
def start_intake():
    # Initialize intake state in session
    data = request.json or {}
    lang = data.get('language', 'en')
    
    session['phase'] = 'questioning'
    session['intake_index'] = 0
    session['intake_answers'] = {}
    session['language'] = lang
    
    # Get translations
    trans = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    
    # Return the privacy promise and first question
    privacy = trans['privacy']
    intake_q = INTAKE_QUESTIONS_DICT.get(lang, INTAKE_QUESTIONS_DICT['en'])
    first_q = intake_q[0]
    
    return jsonify({'privacy': privacy, 'first_question': first_q, 'index': 0, 'total': len(intake_q)})


@app.route('/api/next_question')
def next_question():
    # Returns current question during intake or indicates completion
    if session.get('phase') != 'questioning':
        return jsonify({'done': True})
    
    lang = session.get('language', 'en')
    intake_q = INTAKE_QUESTIONS_DICT.get(lang, INTAKE_QUESTIONS_DICT['en'])
    
    idx = session.get('intake_index', 0)
    if idx >= len(intake_q):
        return jsonify({'done': True})
    return jsonify({'question': intake_q[idx], 'index': idx, 'total': len(intake_q)})


@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json or {}
    answer = data.get('answer', '').strip()
    
    lang = session.get('language', 'en')
    intake_q = INTAKE_QUESTIONS_DICT.get(lang, INTAKE_QUESTIONS_DICT['en'])
    
    if session.get('phase') != 'questioning':
        return jsonify({'error': 'Not in intake phase'}), 400
    idx = session.get('intake_index', 0)
    if idx >= len(intake_q):
        return jsonify({'done': True})

    # store answer
    answers = session.get('intake_answers', {})
    answers[str(idx)] = {'question': intake_q[idx], 'answer': answer}
    session['intake_answers'] = answers
    session['intake_index'] = idx + 1

    # if finished, switch to advice
    if session['intake_index'] >= len(intake_q):
        session['phase'] = 'advice'
        # Generate advice in the selected language
        advice = generate_local_advice(answers, lang)
        return jsonify({'done': True, 'advice': advice})

    # else return next question
    next_q = intake_q[session['intake_index']]
    return jsonify({'next_question': next_q, 'index': session['intake_index'], 'total': len(intake_q)})


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    user_message = data.get('message', '')
    guest_id = data.get('guest_id')

    if not user_message or not user_message.strip():
        return jsonify({'error': 'Message cannot be empty'}), 400

    # If user is in intake phase, instruct to answer questions via submit_answer
    if session.get('phase') == 'questioning':
        return jsonify({'error': 'Please complete the intake questions first', 'phase': 'questioning'}), 400

    # If logged in, use DB limits
    if 'user_id' in session:
        user_id = session['user_id']
        is_premium = session.get('is_premium', False)
        lang = session.get('language', 'en')
        conn = sqlite3.connect('soul_companion.db')
        c = conn.cursor()
        c.execute("SELECT messages_used FROM users WHERE id = ?", (user_id,))
        r = c.fetchone()
        messages_used = r[0] if r else 0
        
        # Check if user is in advice phase and is not premium - trigger paywall
        if session.get('phase') == 'advice' and not is_premium:
            conn.close()
            trans = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
            return jsonify({
                'paywall': True,
                'message': trans['paywall'],
                'unlock_text': trans['unlock'],
                'phase': 'paywall'
            }), 402
        
        if not is_premium and messages_used >= 5:
            conn.close()
            return jsonify({'error': 'Message limit reached', 'messages_used': messages_used}), 402

        # System prompt with empathetic, professional psychiatrist persona
        if lang == 'ar':
            system_prompt = (
                "أنت د. إيلارا، مستشارة نفسية احترافية وعاطفية وسرية. تكوني دائماً داعمة وهادئة وتقدمين خطوات صغيرة آمنة وفعالة. "
                "تضمني إخلاء مسؤولية قصيرة بأنك رفيق ذكاء اصطناعي وليستِ معالجة مرخصة."
            )
        elif lang == 'fr':
            system_prompt = (
                "Vous êtes Dr. Elara, une conseillère psychologique professionnelle, empathique et confidentielle. "
                "Soyez toujours valorisante, calme et proposez des mesures petites et sûres. Incluez un petit avertissement que vous êtes une compagne IA, pas une clinicienne agréée."
            )
        else:
            system_prompt = (
                "You are Dr. Elara, a professional, empathetic, and confidential mental health companion. "
                "Always be validating, calm, and provide small, safe, actionable steps. Include a short disclaimer that you are an AI companion, not a licensed clinician."
            )
        
        advice_input = ''
        # include intake answers if available
        answers = session.get('intake_answers')
        if answers:
            summary = '\n\n'.join([f"{v['question']}\n{v['answer']}" for k,v in answers.items()])
            advice_input = f"User intake:\n{summary}\n\nUser message:\n{user_message}"
        else:
            advice_input = user_message

        ai_resp = get_hf_response(system_prompt, advice_input)
        if not ai_resp:
            # Fallback response if API fails
            ai_resp = "I appreciate you sharing that with me. That sounds challenging. What specific aspect would you like to explore further? Remember, I'm here to listen and offer support."

        if not is_premium:
            c.execute("UPDATE users SET messages_used = messages_used + 1 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'response': ai_resp, 'messages_used': messages_used + 1 if not is_premium else 0, 'is_premium': is_premium})

    # Guest path
    if not guest_id:
        return jsonify({'error': 'Guest mode requires guest_id'}), 401
    
    lang = session.get('language', 'en')
    
    # Check if guest is in advice phase - trigger paywall
    if session.get('phase') == 'advice':
        trans = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
        return jsonify({
            'paywall': True,
            'message': trans['paywall'],
            'unlock_text': trans['unlock'],
            'phase': 'paywall'
        }), 402
    
    count = GUEST_COUNTS.get(guest_id, 0)
    if count >= 5:
        return jsonify({'error': 'Guest limit reached', 'messages_used': count}), 402

    if lang == 'ar':
        system_prompt = (
            "أنت د. إيلارا، مستشارة نفسية احترافية وعاطفية وسرية. كوني دائماً داعمة وهادئة وقدمي خطوات صغيرة آمنة وفعالة. "
            "أضيفي إخلاء مسؤولية قصيرة."
        )
    elif lang == 'fr':
        system_prompt = (
            "Vous êtes Dr. Elara, une conseillère psychologique professionnelle, empathique et confidentielle. "
            "Soyez valorisante, calme et proposez des mesures petites et sûres. Incluez un court avertissement."
        )
    else:
        system_prompt = (
            "You are Dr. Elara, a professional, empathetic, and confidential mental health companion. "
            "Be calm, validating, and offer small actionable steps. Include a short disclaimer."
        )
    
    ai_resp = get_hf_response(system_prompt, user_message)
    if not ai_resp:
        # Fallback response if API fails
        ai_resp = "I hear you, and what you're sharing matters. I want to support you. What's been the hardest part about this for you?"
    
    count += 1
    GUEST_COUNTS[guest_id] = count
    return jsonify({'response': ai_resp, 'messages_used': count, 'is_premium': False})


@app.route('/api/new_chat', methods=['POST'])
def new_chat():
    # Reset session state and optionally guest counter
    session.pop('phase', None)
    session.pop('intake_index', None)
    session.pop('intake_answers', None)
    data = request.json or {}
    guest_id = data.get('guest_id')
    if guest_id and guest_id in GUEST_COUNTS:
        GUEST_COUNTS.pop(guest_id, None)
    return jsonify({'message': 'New chat started'})


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    conn = sqlite3.connect('soul_companion.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return jsonify({'error': 'Username already exists'}), 400
    password_hash = generate_password_hash(password)
    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'message': 'Account created', 'user_id': user_id})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    conn = sqlite3.connect('soul_companion.db')
    c = conn.cursor()
    c.execute("SELECT id, password_hash, messages_used, is_premium FROM users WHERE username = ?", (username,))
    r = c.fetchone()
    conn.close()
    if r and check_password_hash(r[1], password):
        session['user_id'] = r[0]
        session['phase'] = session.get('phase', None)
        session['is_premium'] = bool(r[3])
        return jsonify({'message': 'Login successful', 'user_id': r[0], 'messages_used': r[2], 'is_premium': bool(r[3])})
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})


@app.route('/api/translations/<lang>')
def get_translations(lang):
    """Return UI translations for the specified language"""
    if lang not in TRANSLATIONS:
        lang = 'en'
    return jsonify({'translations': TRANSLATIONS[lang], 'language': lang})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
