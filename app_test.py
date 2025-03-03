from flask import Flask, request, jsonify, send_file
from bot_test import generate_response, detect_language, process_fallback, apply_entities
import random

app = Flask(__name__)

@app.route("/")
def index():
    return send_file(r"C:\Users\ahmad\OneDrive\سطح المكتب\Test Bot\Template\index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = ""
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        use_lang = data.get("lang", None)
        
        # اكتشاف اللغة إذا لم يتم تحديدها
        if not use_lang:
            use_lang = detect_language(user_message) if user_message else 'en'
            
        # معالجة الرسائل الفارغة
        if not user_message:
            return jsonify({
                "response": process_fallback(use_lang),
                "confidence": 0.0
            })
        
        # توليد الرد مع مستوى الثقة
        response, confidence = generate_response(user_message, use_lang)
        
        return jsonify({
            "response": response,
            "confidence": confidence,
            "detected_lang": use_lang
        })
    
    except Exception as e:
        # التعامل مع الأخطاء بلغة محددة
        error_lang = use_lang if 'use_lang' in locals() else 'en'
        error_msg = {
            'en': "Could not process your request",
            'ar': "تعذر معالجة طلبك"
        }.get(error_lang, "Processing error")
        
        return jsonify({
            "response": f"⚠️ {error_msg}",
            "error": str(e) if app.debug else None
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
