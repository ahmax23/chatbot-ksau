import spacy
import json
from fuzzywuzzy import process
from functools import lru_cache
import random

# التهيئة الأساسية
nlp_en = spacy.load("en_core_web_sm")

def load_data():
    try:
        with open("intents_test.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # معالجة البيانات مع دعم الإجراءات السريعة
        intents = {
            lang: {
                intent["intent"]: {
                    "patterns": [p[lang].lower() for p in intent["patterns"]],
                    "responses": [r[lang] for r in intent["responses"]]
                } for intent in data["intents"]
            } for lang in ["en", "ar"]
        }
        
        entities = {
    lang: {
        e["entity_type"]: [v[lang].lower() for v in e["values"]]  # التصحيح هنا
        for e in data["entities"]
    } for lang in ["en", "ar"]
}
        
        return intents, entities, data
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Critical Error: {e}")
        exit(1)

intents, entities, data = load_data()

def detect_language(text):
    """اكتشاف اللغة باستخدام الحروف العربية الأساسية"""
    ar_chars = set("ابتةثجحخدذرزسشصضطظعغفقكلمنهويأإآىءؤئ")
    ar_count = sum(1 for c in text if c in ar_chars)
    return "ar" if ar_count / len(text) > 0.3 else "en"

@lru_cache(maxsize=100)
def get_intent(user_input, lang):
    threshold = 75
    patterns = {
        pattern: intent_name
        for intent_name, intent_data in intents[lang].items()
        for pattern in intent_data["patterns"]
    }
    
    best_match, score = process.extractOne(
        user_input.lower(),
        patterns.keys(),
        scorer=process.fuzz.WRatio
    )
    return (patterns[best_match], score) if score >= threshold else ("fallback", score)

def simple_arabic_tokenizer(text):
    return text.split()  # تجزئة بسيطة بالمسافات

def get_entities(user_input, lang):
    """استخراج الكيانات بدون مكتبات خارجية"""
    if lang == "ar":
        tokens = simple_arabic_tokenizer(user_input)
        return [token for token in tokens if token in entities["ar"].get("technology", [])]
    
    doc = nlp_en(user_input)
    return [ent.text for ent in doc.ents if ent.label_ in entities["en"]]

def generate_response(user_input, lang):
    intent, confidence = get_intent(user_input.lower(), lang)
    
    if intent == "fallback":
        # الحل: أعد قيمة ثنائية بدل نص واحد
        fallback_text = process_fallback(lang)
        return fallback_text, 0.0  # أو أي قيمة ثقة تراها مناسبة
    
    response = random.choice(intents[lang][intent]["responses"])
    entities_found = get_entities(user_input, lang)
    
    # لاحظ أننا نرجع استجابة + ثقة
    return apply_entities(response, entities_found, lang), confidence

def process_fallback(lang):
    """معالجة الردود الاحتياطية"""
    fallbacks = [r[lang] for r in data["fallback_responses"]]
    return random.choice(fallbacks)

def apply_entities(response, entities, lang):
    """تطبيق الكيانات على الرد"""
    for entity in entities:
        response = response.replace(f"{{{{{entity}}}}}", entity)
    return response