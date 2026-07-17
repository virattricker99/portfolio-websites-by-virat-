from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import re

# ============================================
# APP CONFIGURATION
# ============================================

app = Flask(__name__)

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Database Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)

# ============================================
# DATABASE MODELS
# ============================================

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'is_read': self.is_read
        }

# ============================================
# API ROUTES
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected' if db.engine else 'disconnected'
    }), 200

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('email') or not data.get('message'):
            return jsonify({'error': 'Name, email, and message are required'}), 400
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        message = ContactMessage(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),
            message=data['message']
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message sent successfully! I will get back to you soon.',
            'id': message.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/contact/messages', methods=['GET'])
def get_contact_messages():
    try:
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        return jsonify([msg.to_dict() for msg in messages]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# FRONTEND HTML (Complete Portfolio)
# ============================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Rishu Thakur - Graphic Designer & Digital Creator. Specializing in social media creatives, posters, branding, and promotional designs." />
    <title>Rishu Thakur | Graphic Designer & Digital Creator</title>

    <!-- Bootstrap 5 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" />
    <!-- Google Font: Poppins -->
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet" />
    <!-- Font Awesome 6 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" />
    <!-- AOS -->
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet" />

    <style>
        :root {
            --bg-primary: #f8f9fa;
            --bg-secondary: #ffffff;
            --bg-card: #ffffff;
            --text-primary: #1a1a2e;
            --text-secondary: #4a4a6a;
            --text-muted: #6c757d;
            --border-color: rgba(0, 0, 0, 0.08);
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
            --shadow-hover: 0 16px 48px rgba(0, 0, 0, 0.15);
            --glass-bg: rgba(255, 255, 255, 0.72);
            --glass-border: rgba(255, 255, 255, 0.3);
            --gradient-primary: linear-gradient(135deg, #6c5ce7, #a29bfe);
            --navbar-bg: rgba(255, 255, 255, 0.85);
            --card-bg: #ffffff;
            --input-bg: #f1f2f6;
            --input-border: #dfe6e9;
            --footer-bg: #1a1a2e;
            --footer-text: #dfe6e9;
            --whatsapp-color: #25d366;
            --scroll-top-bg: #6c5ce7;
            --scroll-top-color: #fff;
            --transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }

        [data-theme="dark"] {
            --bg-primary: #0f0f1a;
            --bg-secondary: #1a1a2e;
            --bg-card: #1e1e36;
            --text-primary: #f0f0f5;
            --text-secondary: #c8c8e0;
            --text-muted: #8888aa;
            --border-color: rgba(255, 255, 255, 0.06);
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            --shadow-hover: 0 16px 48px rgba(0, 0, 0, 0.6);
            --glass-bg: rgba(26, 26, 46, 0.78);
            --glass-border: rgba(255, 255, 255, 0.08);
            --navbar-bg: rgba(15, 15, 26, 0.9);
            --card-bg: #1e1e36;
            --input-bg: #2a2a4a;
            --input-border: #3a3a5a;
            --footer-bg: #0a0a12;
            --footer-text: #b0b0d0;
            --scroll-top-bg: #a29bfe;
            --scroll-top-color: #0f0f1a;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; scroll-padding-top: 80px; }
        body {
            font-family: 'Poppins', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            transition: var(--transition);
            overflow-x: hidden;
            line-height: 1.7;
        }
        a { text-decoration: none; color: inherit; }
        a:hover { color: #6c5ce7; }
        img { max-width: 100%; height: auto; display: block; }

        .section-title {
            font-weight: 700;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            position: relative;
            display: inline-block;
        }
        .section-title::after {
            content: '';
            position: absolute;
            bottom: -8px;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 4px;
            background: var(--gradient-primary);
            border-radius: 4px;
        }
        .section-subtitle {
            color: var(--text-secondary);
            font-weight: 400;
            font-size: 1.1rem;
            margin-top: 0.75rem;
        }
        .section-padding { padding: 100px 0 80px; }
        .gradient-text {
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        #loader {
            position: fixed;
            inset: 0;
            z-index: 99999;
            background: var(--bg-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 20px;
            transition: opacity 0.8s ease, visibility 0.8s ease;
        }
        #loader.hidden { opacity: 0; visibility: hidden; pointer-events: none; }
        .loader-spinner {
            width: 60px;
            height: 60px;
            border: 4px solid var(--border-color);
            border-top: 4px solid #6c5ce7;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loader-text { font-weight: 600; font-size: 1.1rem; color: var(--text-secondary); letter-spacing: 2px; }

        #scrollTopBtn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 999;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--scroll-top-bg);
            color: var(--scroll-top-color);
            border: none;
            font-size: 1.4rem;
            box-shadow: 0 4px 20px rgba(108, 92, 231, 0.4);
            cursor: pointer;
            opacity: 0;
            visibility: hidden;
            transform: translateY(40px);
            transition: var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        #scrollTopBtn.visible { opacity: 1; visibility: visible; transform: translateY(0); }
        #scrollTopBtn:hover { transform: translateY(-4px) scale(1.05); box-shadow: 0 8px 30px rgba(108, 92, 231, 0.6); }

        .whatsapp-float {
            position: fixed;
            bottom: 100px;
            right: 30px;
            z-index: 998;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: var(--whatsapp-color);
            color: #fff;
            font-size: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 24px rgba(37, 211, 102, 0.4);
            transition: var(--transition);
            animation: pulse-whatsapp 2s infinite;
        }
        .whatsapp-float:hover { transform: scale(1.1) translateY(-4px); color: #fff; box-shadow: 0 8px 36px rgba(37, 211, 102, 0.6); }
        @keyframes pulse-whatsapp {
            0%, 100% { box-shadow: 0 4px 24px rgba(37, 211, 102, 0.4); }
            50% { box-shadow: 0 4px 40px rgba(37, 211, 102, 0.7); }
        }

        .navbar-custom {
            background: var(--navbar-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.06);
            transition: var(--transition);
            padding: 12px 0;
            border-bottom: 1px solid var(--border-color);
        }
        .navbar-custom .navbar-brand { font-weight: 700; font-size: 1.5rem; color: var(--text-primary); letter-spacing: -0.5px; }
        .navbar-custom .navbar-brand span { color: #6c5ce7; }
        .navbar-custom .nav-link {
            font-weight: 500;
            font-size: 0.95rem;
            color: var(--text-secondary) !important;
            padding: 8px 16px !important;
            transition: var(--transition);
            position: relative;
        }
        .navbar-custom .nav-link:hover, .navbar-custom .nav-link.active { color: #6c5ce7 !important; }
        .navbar-custom .nav-link::after {
            content: '';
            position: absolute;
            bottom: 4px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 2px;
            background: var(--gradient-primary);
            transition: var(--transition);
            border-radius: 2px;
        }
        .navbar-custom .nav-link:hover::after, .navbar-custom .nav-link.active::after { width: 60%; }

        .theme-toggle {
            background: var(--input-bg);
            border: none;
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            color: var(--text-primary);
            transition: var(--transition);
            cursor: pointer;
            border: 1px solid var(--border-color);
        }
        .theme-toggle:hover { transform: rotate(20deg) scale(1.05); background: var(--gradient-primary); color: #fff; }
        .navbar-toggler { border: none; padding: 8px; font-size: 1.4rem; color: var(--text-primary); }
        .navbar-toggler:focus { box-shadow: none; }

        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            position: relative;
            overflow: hidden;
            background: var(--bg-primary);
            padding: 120px 0 80px;
        }
        .hero::before {
            content: '';
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 20% 80%, rgba(108, 92, 231, 0.08) 0%, transparent 60%),
                radial-gradient(circle at 80% 20%, rgba(253, 121, 168, 0.06) 0%, transparent 50%);
            pointer-events: none;
        }
        .hero-shapes {
            position: absolute;
            inset: 0;
            pointer-events: none;
            overflow: hidden;
        }
        .hero-shapes .shape {
            position: absolute;
            border-radius: 50%;
            opacity: 0.12;
            animation: float-shape 20s infinite alternate ease-in-out;
        }
        .hero-shapes .shape:nth-child(1) {
            width: 300px;
            height: 300px;
            background: #6c5ce7;
            top: -80px;
            right: -60px;
            animation-delay: 0s;
        }
        .hero-shapes .shape:nth-child(2) {
            width: 200px;
            height: 200px;
            background: #fd79a8;
            bottom: -40px;
            left: -40px;
            animation-delay: -4s;
        }
        .hero-shapes .shape:nth-child(3) {
            width: 150px;
            height: 150px;
            background: #00b894;
            top: 40%;
            right: 10%;
            animation-delay: -8s;
        }
        @keyframes float-shape {
            0% { transform: translate(0, 0) scale(1) rotate(0deg); }
            33% { transform: translate(30px, -30px) scale(1.05) rotate(5deg); }
            66% { transform: translate(-20px, 20px) scale(0.95) rotate(-3deg); }
            100% { transform: translate(10px, -10px) scale(1.02) rotate(2deg); }
        }

        .hero-content { position: relative; z-index: 2; }
        .hero-badge {
            display: inline-block;
            padding: 6px 20px;
            background: var(--glass-bg);
            backdrop-filter: blur(8px);
            border: 1px solid var(--glass-border);
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 20px;
        }
        .hero h1 { font-size: 4.2rem; font-weight: 800; line-height: 1.1; margin-bottom: 10px; letter-spacing: -2px; }
        .hero h1 .highlight {
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero .typing-wrapper {
            font-size: 1.6rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 20px;
            min-height: 60px;
        }
        .hero .typing-wrapper .typed-text {
            color: #6c5ce7;
            border-right: 3px solid #6c5ce7;
            padding-right: 6px;
            animation: blink-caret 0.8s step-end infinite;
        }
        @keyframes blink-caret { 50% { border-color: transparent; } }
        .hero p { font-size: 1.1rem; color: var(--text-secondary); max-width: 540px; margin-bottom: 30px; line-height: 1.8; }
        .hero-buttons .btn { padding: 12px 34px; font-weight: 600; border-radius: 50px; transition: var(--transition); font-size: 0.95rem; }
        .btn-primary-gradient {
            background: var(--gradient-primary);
            color: #fff;
            border: none;
            box-shadow: 0 4px 20px rgba(108, 92, 231, 0.35);
        }
        .btn-primary-gradient:hover { transform: translateY(-3px); box-shadow: 0 8px 32px rgba(108, 92, 231, 0.5); color: #fff; }
        .btn-outline-gradient {
            background: transparent;
            color: var(--text-primary);
            border: 2px solid var(--border-color);
        }
        .btn-outline-gradient:hover { border-color: #6c5ce7; color: #6c5ce7; transform: translateY(-3px); background: rgba(108, 92, 231, 0.05); }

        .hero-image-wrapper { position: relative; display: flex; justify-content: center; align-items: center; }
        .hero-image {
            width: 380px;
            height: 380px;
            border-radius: 50%;
            border: 4px solid var(--glass-border);
            box-shadow: var(--shadow);
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 8rem;
            color: rgba(255, 255, 255, 0.6);
            transition: var(--transition);
            position: relative;
        }
        .hero-image:hover { transform: scale(1.02); box-shadow: var(--shadow-hover); }
        .hero-image-ring {
            position: absolute;
            inset: -12px;
            border-radius: 50%;
            border: 2px solid var(--border-color);
            animation: spin-ring 20s linear infinite;
        }
        .hero-image-ring::after {
            content: '';
            position: absolute;
            top: -6px;
            left: 50%;
            transform: translateX(-50%);
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #6c5ce7;
        }
        @keyframes spin-ring { to { transform: rotate(360deg); } }

        .about-image-placeholder {
            width: 100%;
            max-width: 400px;
            aspect-ratio: 1/1;
            border-radius: 20px;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 6rem;
            color: rgba(255, 255, 255, 0.5);
            box-shadow: var(--shadow);
            transition: var(--transition);
            margin: 0 auto;
        }
        .about-image-placeholder:hover { transform: scale(1.02) rotate(-2deg); box-shadow: var(--shadow-hover); }

        .skill-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 28px 20px;
            text-align: center;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
            transition: var(--transition);
            height: 100%;
            position: relative;
            overflow: hidden;
        }
        .skill-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-primary);
            transform: scaleX(0);
            transition: var(--transition);
        }
        .skill-card:hover::before { transform: scaleX(1); }
        .skill-card:hover { transform: translateY(-8px); box-shadow: var(--shadow-hover); }
        .skill-card .icon {
            font-size: 2.8rem;
            margin-bottom: 14px;
            display: inline-block;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .skill-card h5 { font-weight: 600; font-size: 1.05rem; margin-bottom: 6px; color: var(--text-primary); }
        .skill-card p { font-size: 0.85rem; color: var(--text-muted); margin: 0; }

        .progress-skill { margin-bottom: 18px; }
        .progress-skill .label {
            display: flex;
            justify-content: space-between;
            font-weight: 500;
            font-size: 0.95rem;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        .progress-skill .progress {
            height: 8px;
            border-radius: 8px;
            background: var(--progress-bg);
            overflow: visible;
            position: relative;
        }
        .progress-skill .progress-bar {
            border-radius: 8px;
            background: var(--gradient-primary);
            width: 0%;
            transition: width 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            position: relative;
            height: 100%;
        }
        .progress-skill .progress-bar .tooltip-progress {
            position: absolute;
            right: -10px;
            top: -24px;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-primary);
            background: var(--bg-card);
            padding: 2px 10px;
            border-radius: 6px;
            box-shadow: var(--shadow);
            opacity: 0;
            transition: var(--transition);
        }
        .progress-skill .progress-bar.animated .tooltip-progress { opacity: 1; }

        .tool-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 30px 20px;
            text-align: center;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
            transition: var(--transition);
            height: 100%;
        }
        .tool-card:hover { transform: translateY(-6px) scale(1.02); box-shadow: var(--shadow-hover); }
        .tool-card .icon { font-size: 3.6rem; margin-bottom: 12px; display: inline-block; }
        .tool-card h5 { font-weight: 600; font-size: 1.1rem; color: var(--text-primary); }
        .tool-card .level {
            font-size: 0.85rem;
            color: var(--text-muted);
            background: var(--input-bg);
            padding: 4px 16px;
            border-radius: 50px;
            display: inline-block;
            margin-top: 6px;
        }

        .service-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 32px 24px;
            text-align: center;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
            transition: var(--transition);
            height: 100%;
            position: relative;
            overflow: hidden;
        }
        .service-card::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-primary);
            transform: scaleX(0);
            transform-origin: center;
            transition: var(--transition);
        }
        .service-card:hover::after { transform: scaleX(1); }
        .service-card:hover { transform: translateY(-8px); box-shadow: var(--shadow-hover); }
        .service-card .icon {
            font-size: 2.6rem;
            margin-bottom: 14px;
            display: inline-block;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .service-card h5 { font-weight: 600; font-size: 1.05rem; color: var(--text-primary); }
        .service-card p { font-size: 0.9rem; color: var(--text-muted); margin: 0; }

        .portfolio-filter .btn {
            border-radius: 50px;
            padding: 8px 24px;
            font-weight: 500;
            font-size: 0.9rem;
            transition: var(--transition);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            background: transparent;
            margin: 4px;
        }
        .portfolio-filter .btn:hover, .portfolio-filter .btn.active {
            background: var(--gradient-primary);
            color: #fff;
            border-color: transparent;
            box-shadow: 0 4px 20px rgba(108, 92, 231, 0.3);
        }

        .portfolio-item {
            border-radius: 16px;
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: var(--transition);
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            cursor: pointer;
        }
        .portfolio-item:hover { transform: translateY(-6px); box-shadow: var(--shadow-hover); }
        .portfolio-item .img-wrap {
            position: relative;
            overflow: hidden;
            aspect-ratio: 4/3;
            background: var(--input-bg);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 4rem;
            color: var(--text-muted);
        }
        .portfolio-item .img-wrap img { width: 100%; height: 100%; object-fit: cover; transition: var(--transition); }
        .portfolio-item:hover .img-wrap img { transform: scale(1.05); }
        .portfolio-item .img-wrap .overlay {
            position: absolute;
            inset: 0;
            background: rgba(108, 92, 231, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: var(--transition);
            backdrop-filter: blur(4px);
        }
        .portfolio-item:hover .img-wrap .overlay { opacity: 1; }
        .portfolio-item .img-wrap .overlay i { font-size: 3rem; color: #fff; transform: scale(0.6); transition: var(--transition); }
        .portfolio-item:hover .img-wrap .overlay i { transform: scale(1); }
        .portfolio-item .info { padding: 18px 20px 20px; }
        .portfolio-item .info h5 { font-weight: 600; font-size: 1.05rem; color: var(--text-primary); margin-bottom: 2px; }
        .portfolio-item .info .category { font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }

        .lightbox-overlay {
            position: fixed;
            inset: 0;
            z-index: 9999;
            background: rgba(0, 0, 0, 0.88);
            backdrop-filter: blur(12px);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            visibility: hidden;
            transition: var(--transition);
            padding: 40px;
        }
        .lightbox-overlay.active { opacity: 1; visibility: visible; }
        .lightbox-overlay .lightbox-content {
            max-width: 800px;
            width: 100%;
            background: var(--bg-card);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
            transform: scale(0.9);
            transition: var(--transition);
        }
        .lightbox-overlay.active .lightbox-content { transform: scale(1); }
        .lightbox-overlay .lightbox-content .img-wrap {
            aspect-ratio: 4/3;
            background: var(--input-bg);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 6rem;
            color: var(--text-muted);
        }
        .lightbox-overlay .lightbox-content .img-wrap img { width: 100%; height: 100%; object-fit: cover; }
        .lightbox-overlay .lightbox-content .body { padding: 24px 28px 28px; }
        .lightbox-overlay .lightbox-content .body h4 { font-weight: 600; color: var(--text-primary); }
        .lightbox-overlay .lightbox-content .body .category { color: var(--text-muted); font-size: 0.9rem; }
        .lightbox-close {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: var(--transition);
            z-index: 10;
        }
        .lightbox-close:hover { background: rgba(255, 255, 255, 0.25); transform: rotate(90deg); }

        .process-step {
            display: flex;
            gap: 20px;
            align-items: flex-start;
            padding: 16px 0;
            position: relative;
            padding-left: 20px;
            border-left: 3px solid var(--border-color);
        }
        .process-step:last-child { border-left-color: transparent; }
        .process-step .step-num {
            flex-shrink: 0;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: var(--gradient-primary);
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.1rem;
            box-shadow: 0 4px 16px rgba(108, 92, 231, 0.3);
        }
        .process-step .step-content h5 { font-weight: 600; font-size: 1.05rem; color: var(--text-primary); margin-bottom: 2px; }
        .process-step .step-content p { font-size: 0.9rem; color: var(--text-muted); margin: 0; }

        .timeline-item {
            position: relative;
            padding-left: 30px;
            padding-bottom: 30px;
            border-left: 3px solid var(--border-color);
        }
        .timeline-item:last-child { border-left-color: transparent; padding-bottom: 0; }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -9px;
            top: 6px;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--gradient-primary);
            border: 3px solid var(--bg-primary);
            box-shadow: 0 0 0 4px rgba(108, 92, 231, 0.2);
        }
        .timeline-item .date {
            font-size: 0.8rem;
            font-weight: 600;
            color: #6c5ce7;
            background: rgba(108, 92, 231, 0.1);
            padding: 2px 14px;
            border-radius: 50px;
            display: inline-block;
            margin-bottom: 4px;
        }
        .timeline-item h5 { font-weight: 600; font-size: 1.05rem; color: var(--text-primary); margin-bottom: 2px; }
        .timeline-item p { font-size: 0.9rem; color: var(--text-muted); margin: 0; }

        .feature-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 28px 20px;
            text-align: center;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
            transition: var(--transition);
            height: 100%;
        }
        .feature-card:hover { transform: translateY(-6px); box-shadow: var(--shadow-hover); }
        .feature-card .icon {
            font-size: 2.4rem;
            margin-bottom: 12px;
            display: inline-block;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .feature-card h5 { font-weight: 600; font-size: 1rem; color: var(--text-primary); margin-bottom: 2px; }
        .feature-card p { font-size: 0.85rem; color: var(--text-muted); margin: 0; }

        .testimonial-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 30px 28px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
            transition: var(--transition);
            height: 100%;
        }
        .testimonial-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
        .testimonial-card .stars { color: #fdcb6e; font-size: 1rem; letter-spacing: 2px; margin-bottom: 10px; }
        .testimonial-card .quote { font-size: 0.95rem; color: var(--text-secondary); font-style: italic; line-height: 1.7; margin-bottom: 16px; }
        .testimonial-card .profile { display: flex; align-items: center; gap: 14px; }
        .testimonial-card .profile .avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-weight: 600;
            font-size: 1.1rem;
            flex-shrink: 0;
        }
        .testimonial-card .profile .name { font-weight: 600; font-size: 0.95rem; color: var(--text-primary); margin-bottom: 0; }
        .testimonial-card .profile .role { font-size: 0.8rem; color: var(--text-muted); margin: 0; }

        .pricing-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 36px 28px 32px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
            transition: var(--transition);
            text-align: center;
            height: 100%;
            position: relative;
            overflow: hidden;
        }
        .pricing-card:hover { transform: translateY(-6px); box-shadow: var(--shadow-hover); }
        .pricing-card.popular { border-color: #6c5ce7; box-shadow: 0 8px 32px rgba(108, 92, 231, 0.2); }
        .pricing-card.popular::before {
            content: 'Popular';
            position: absolute;
            top: 16px;
            right: -28px;
            background: var(--gradient-primary);
            color: #fff;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 4px 32px;
            transform: rotate(45deg);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .pricing-card .price { font-size: 2.8rem; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
        .pricing-card .price span { font-size: 1rem; font-weight: 400; color: var(--text-muted); }
        .pricing-card .plan-name { font-weight: 600; font-size: 1.2rem; color: var(--text-primary); }
        .pricing-card .features { list-style: none; padding: 0; margin: 16px 0 24px; text-align: left; }
        .pricing-card .features li { padding: 6px 0; font-size: 0.9rem; color: var(--text-secondary); display: flex; align-items: center; gap: 10px; }
        .pricing-card .features li i { color: #6c5ce7; font-size: 1rem; }
        .pricing-card .btn { border-radius: 50px; padding: 12px 32px; font-weight: 600; width: 100%; }

        .accordion-custom .accordion-item {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px !important;
            margin-bottom: 12px;
            overflow: hidden;
        }
        .accordion-custom .accordion-button {
            background: var(--bg-card);
            color: var(--text-primary);
            font-weight: 600;
            padding: 18px 24px;
            border: none;
            box-shadow: none;
            font-size: 1rem;
        }
        .accordion-custom .accordion-button:not(.collapsed) { background: var(--bg-card); color: #6c5ce7; box-shadow: none; }
        .accordion-custom .accordion-button:focus { box-shadow: none; border-color: transparent; }
        .accordion-custom .accordion-body { padding: 0 24px 20px; color: var(--text-secondary); font-size: 0.95rem; background: var(--bg-card); }
        .accordion-custom .accordion-button::after {
            background-image: none;
            content: '\\f078';
            font-family: 'Font Awesome 6 Free';
            font-weight: 900;
            font-size: 0.8rem;
            color: var(--text-muted);
            transition: var(--transition);
        }
        .accordion-custom .accordion-button:not(.collapsed)::after { transform: rotate(180deg); color: #6c5ce7; }

        .contact-form .form-control {
            background: var(--input-bg);
            border: 1px solid var(--input-border);
            border-radius: 12px;
            padding: 14px 18px;
            font-size: 0.95rem;
            color: var(--text-primary);
            transition: var(--transition);
        }
        .contact-form .form-control:focus {
            border-color: #6c5ce7;
            box-shadow: 0 0 0 4px rgba(108, 92, 231, 0.12);
            background: var(--input-bg);
        }
        .contact-form .form-control::placeholder { color: var(--text-muted); }
        .contact-form .btn-submit {
            padding: 14px 40px;
            border-radius: 50px;
            background: var(--gradient-primary);
            color: #fff;
            border: none;
            font-weight: 600;
            font-size: 1rem;
            transition: var(--transition);
            box-shadow: 0 4px 24px rgba(108, 92, 231, 0.35);
        }
        .contact-form .btn-submit:hover { transform: translateY(-3px); box-shadow: 0 8px 36px rgba(108, 92, 231, 0.5); color: #fff; }

        .contact-info-item {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 14px 0;
            border-bottom: 1px solid var(--border-color);
        }
        .contact-info-item:last-child { border-bottom: none; }
        .contact-info-item .icon {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 1.2rem;
            flex-shrink: 0;
        }
        .contact-info-item .info .label { font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }
        .contact-info-item .info .value { font-weight: 500; color: var(--text-primary); }
        .contact-info-item .info .value a { color: var(--text-primary); transition: var(--transition); }
        .contact-info-item .info .value a:hover { color: #6c5ce7; }

        .footer {
            background: var(--footer-bg);
            color: var(--footer-text);
            padding: 60px 0 0;
        }
        .footer h5 { font-weight: 700; font-size: 1.1rem; color: #fff; margin-bottom: 18px; }
        .footer p, .footer a { color: var(--footer-text); font-size: 0.9rem; transition: var(--transition); }
        .footer a:hover { color: #a29bfe; padding-left: 4px; }
        .footer .social-links a {
            display: inline-block;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.06);
            text-align: center;
            line-height: 40px;
            font-size: 1.1rem;
            transition: var(--transition);
            margin-right: 8px;
            color: var(--footer-text);
        }
        .footer .social-links a:hover { background: var(--gradient-primary); color: #fff; transform: translateY(-3px); }
        .footer .footer-bottom {
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            padding: 20px 0;
            margin-top: 40px;
            font-size: 0.85rem;
            text-align: center;
            color: rgba(255, 255, 255, 0.4);
        }
        .footer .footer-bottom span { color: #a29bfe; }

        @media (max-width: 991.98px) {
            .hero h1 { font-size: 3rem; }
            .hero .typing-wrapper { font-size: 1.2rem; min-height: 48px; }
            .hero-image { width: 280px; height: 280px; font-size: 6rem; }
            .section-title { font-size: 2rem; }
            .section-padding { padding: 70px 0 50px; }
        }
        @media (max-width: 767.98px) {
            .hero { padding: 100px 0 50px; text-align: center; }
            .hero h1 { font-size: 2.4rem; }
            .hero .typing-wrapper { font-size: 1rem; min-height: 40px; }
            .hero p { font-size: 0.95rem; margin-left: auto; margin-right: auto; }
            .hero-buttons .btn { padding: 10px 24px; font-size: 0.85rem; }
            .hero-image { width: 220px; height: 220px; font-size: 4rem; margin-top: 30px; }
            .hero-image-ring { inset: -8px; }
            .section-title { font-size: 1.7rem; }
            .section-padding { padding: 50px 0 30px; }
            .pricing-card .price { font-size: 2.2rem; }
            .whatsapp-float { width: 48px; height: 48px; font-size: 1.6rem; bottom: 90px; right: 16px; }
            #scrollTopBtn { width: 42px; height: 42px; font-size: 1.1rem; bottom: 16px; right: 16px; }
        }
        @media (max-width: 575.98px) {
            .hero h1 { font-size: 2rem; }
            .hero .typing-wrapper { font-size: 0.9rem; min-height: 36px; }
            .hero-image { width: 180px; height: 180px; font-size: 3rem; }
            .portfolio-filter .btn { padding: 6px 16px; font-size: 0.8rem; }
            .testimonial-card { padding: 20px; }
        }
    </style>
</head>
<body>

    <!-- LOADER -->
    <div id="loader">
        <div class="loader-spinner"></div>
        <div class="loader-text">Loading...</div>
    </div>

    <!-- SCROLL TO TOP -->
    <button id="scrollTopBtn" aria-label="Scroll to top">
        <i class="fas fa-arrow-up"></i>
    </button>

    <!-- FLOATING WHATSAPP -->
    <a href="https://wa.me/919592851314?text=Hi%20Rishu%2C%20I%20found%20your%20portfolio%20and%20would%20like%20to%20discuss%20a%20project." target="_blank" class="whatsapp-float" aria-label="Chat on WhatsApp">
        <i class="fab fa-whatsapp"></i>
    </a>

    <!-- LIGHTBOX -->
    <div class="lightbox-overlay" id="lightbox">
        <button class="lightbox-close" id="lightboxClose"><i class="fas fa-times"></i></button>
        <div class="lightbox-content">
            <div class="img-wrap" id="lightboxImage">
                <i class="fas fa-image"></i>
            </div>
            <div class="body">
                <h4 id="lightboxTitle">Project Name</h4>
                <p class="category" id="lightboxCategory">Category</p>
            </div>
        </div>
    </div>

    <!-- NAVBAR -->
    <nav class="navbar navbar-expand-lg navbar-custom fixed-top" id="mainNav">
        <div class="container">
            <a class="navbar-brand" href="#home">Rishu <span>Thakur</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu" aria-controls="navMenu" aria-expanded="false" aria-label="Toggle navigation">
                <i class="fas fa-bars"></i>
            </button>
            <div class="collapse navbar-collapse" id="navMenu">
                <ul class="navbar-nav ms-auto align-items-lg-center gap-1">
                    <li class="nav-item"><a class="nav-link active" href="#home">Home</a></li>
                    <li class="nav-item"><a class="nav-link" href="#about">About</a></li>
                    <li class="nav-item"><a class="nav-link" href="#skills">Skills</a></li>
                    <li class="nav-item"><a class="nav-link" href="#services">Services</a></li>
                    <li class="nav-item"><a class="nav-link" href="#portfolio">Portfolio</a></li>
                    <li class="nav-item"><a class="nav-link" href="#experience">Experience</a></li>
                    <li class="nav-item"><a class="nav-link" href="#contact">Contact</a></li>
                    <li class="nav-item">
                        <button class="theme-toggle ms-lg-2" id="themeToggle" aria-label="Toggle theme">
                            <i class="fas fa-moon"></i>
                        </button>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- HERO -->
    <section class="hero" id="home">
        <div class="hero-shapes">
            <div class="shape"></div>
            <div class="shape"></div>
            <div class="shape"></div>
        </div>
        <div class="container">
            <div class="row align-items-center g-5">
                <div class="col-lg-6 hero-content">
                    <div class="hero-badge">
                        <i class="fas fa-palette me-2"></i> Graphic Designer
                    </div>
                    <h1>I'm <span class="highlight">Rishu Thakur</span></h1>
                    <div class="typing-wrapper">
                        <span class="typed-text" id="typedText"></span>
                    </div>
                    <p>
                        Creative designer specializing in social media creatives, posters, branding,
                        and promotional designs that help businesses grow.
                    </p>
                    <div class="hero-buttons d-flex flex-wrap gap-3">
                        <a href="#portfolio" class="btn btn-primary-gradient">
                            <i class="fas fa-eye me-2"></i> View Portfolio
                        </a>
                        <a href="#contact" class="btn btn-outline-gradient">
                            <i class="fas fa-paper-plane me-2"></i> Hire Me
                        </a>
                    </div>
                </div>
                <div class="col-lg-6 text-center">
                    <div class="hero-image-wrapper">
                        <div class="hero-image-ring"></div>
                        <div class="hero-image" style="overflow:hidden; padding:0; background: transparent;">
                            <img src="https://i.ibb.co/fzzsVSdq/file-00000000949c720b931c888810bd71a3.png" 
                                 alt="Rishu Thakur - Graphic Designer" 
                                 style="width:100%; height:100%; object-fit:cover; border-radius:50%;">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- ABOUT -->
    <section class="section-padding" id="about" style="background: var(--bg-secondary);">
        <div class="container">
            <div class="row align-items-center g-5">
                <div class="col-lg-5 text-center" data-aos="fade-right" data-aos-duration="800">
                    <div class="about-image-placeholder" style="overflow:hidden; padding:0; background: transparent;">
                        <img src="https://i.ibb.co/cSHZzgdz/file-000000004af871fabfa6c0c3adcd24bb.png" 
                             alt="Rishu Thakur - About Me" 
                             style="width:100%; height:100%; object-fit:cover; border-radius:20px;">
                    </div>
                </div>
                <div class="col-lg-7" data-aos="fade-left" data-aos-duration="800">
                    <h2 class="section-title text-start">About <span class="gradient-text">Me</span></h2>
                    <p class="section-subtitle text-start" style="margin-top: 12px;">
                        Hi, I'm Rishu Thakur, a creative and passionate Graphic Designer &amp; Digital Creator.
                    </p>
                    <p style="color: var(--text-secondary); margin-top: 16px;">
                        I specialize in creating eye-catching designs such as social media creatives, posters,
                        and branding materials. I focus on delivering clean, modern, and professional designs
                        that help businesses grow their online presence.
                    </p>
                    <p style="color: var(--text-secondary);">
                        I continuously improve my skills and stay updated with the latest design trends.
                    </p>
                    <div class="row g-3 mt-3">
                        <div class="col-6 col-sm-4">
                            <div class="d-flex align-items-center gap-2">
                                <i class="fas fa-check-circle text-primary" style="color: #6c5ce7;"></i>
                                <span style="font-weight: 500; font-size: 0.9rem; color: var(--text-primary);">Creative</span>
                            </div>
                        </div>
                        <div class="col-6 col-sm-4">
                            <div class="d-flex align-items-center gap-2">
                                <i class="fas fa-check-circle text-primary" style="color: #6c5ce7;"></i>
                                <span style="font-weight: 500; font-size: 0.9rem; color: var(--text-primary);">Professional</span>
                            </div>
                        </div>
                        <div class="col-6 col-sm-4">
                            <div class="d-flex align-items-center gap-2">
                                <i class="fas fa-check-circle text-primary" style="color: #6c5ce7;"></i>
                                <span style="font-weight: 500; font-size: 0.9rem; color: var(--text-primary);">Detail-Oriented</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- SKILLS -->
    <section class="section-padding" id="skills">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">My <span class="gradient-text">Skills</span></h2>
                <p class="section-subtitle">Expertise &amp; proficiency in design tools and techniques</p>
            </div>
            <div class="row g-4 mt-4">
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="500" data-aos-delay="0">
                    <div class="skill-card">
                        <div class="icon"><i class="fas fa-paint-brush"></i></div>
                        <h5>Graphic Designing</h5>
                        <p>Creative visual design</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="500" data-aos-delay="100">
                    <div class="skill-card">
                        <div class="icon"><i class="fas fa-hashtag"></i></div>
                        <h5>Social Media Post Design</h5>
                        <p>Engaging social creatives</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="500" data-aos-delay="200">
                    <div class="skill-card">
                        <div class="icon"><i class="fas fa-poster"></i></div>
                        <h5>Poster &amp; Banner Design</h5>
                        <p>Eye-catching posters</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="500" data-aos-delay="300">
                    <div class="skill-card">
                        <div class="icon"><i class="fas fa-building"></i></div>
                        <h5>Branding &amp; Visual Identity</h5>
                        <p>Brand identity design</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="500" data-aos-delay="400">
                    <div class="skill-card">
                        <div class="icon"><i class="fas fa-pen-fancy"></i></div>
                        <h5>Canva Designing</h5>
                        <p>Advanced Canva expertise</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="500" data-aos-delay="500">
                    <div class="skill-card">
                        <div class="icon"><i class="fas fa-edit"></i></div>
                        <h5>Photoshop Editing</h5>
                        <p>Basic photo editing</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="500" data-aos-delay="600">
                    <div class="skill-card">
                        <div class="icon"><i class="fas fa-layer-group"></i></div>
                        <h5>Layout &amp; Composition</h5>
                        <p>Structured layouts</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="500" data-aos-delay="700">
                    <div class="skill-card">
                        <div class="icon"><i class="fas fa-palette"></i></div>
                        <h5>Color Theory &amp; Typography</h5>
                        <p>Color &amp; font mastery</p>
                    </div>
                </div>
            </div>
            <div class="row mt-5 g-4" data-aos="fade-up" data-aos-duration="800">
                <div class="col-md-6">
                    <div class="progress-skill">
                        <div class="label"><span>Graphic Design</span><span>90%</span></div>
                        <div class="progress"><div class="progress-bar" data-width="90"><span class="tooltip-progress">90%</span></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>Social Media Design</span><span>88%</span></div>
                        <div class="progress"><div class="progress-bar" data-width="88"><span class="tooltip-progress">88%</span></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>Poster &amp; Banner Design</span><span>85%</span></div>
                        <div class="progress"><div class="progress-bar" data-width="85"><span class="tooltip-progress">85%</span></div></div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="progress-skill">
                        <div class="label"><span>Canva</span><span>92%</span></div>
                        <div class="progress"><div class="progress-bar" data-width="92"><span class="tooltip-progress">92%</span></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>Photoshop</span><span>65%</span></div>
                        <div class="progress"><div class="progress-bar" data-width="65"><span class="tooltip-progress">65%</span></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>Branding &amp; Identity</span><span>75%</span></div>
                        <div class="progress"><div class="progress-bar" data-width="75"><span class="tooltip-progress">75%</span></div></div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- TOOLS -->
    <section class="section-padding" id="tools" style="background: var(--bg-secondary);">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">Tools I <span class="gradient-text">Use</span></h2>
                <p class="section-subtitle">Professional design tools I work with daily</p>
            </div>
            <div class="row g-4 mt-4 justify-content-center">
                <div class="col-md-4" data-aos="flip-up" data-aos-duration="600" data-aos-delay="0">
                    <div class="tool-card">
                        <div class="icon"><i class="fab fa-canva" style="color: #00c4cc;"></i></div>
                        <h5>Canva</h5>
                        <span class="level">Advanced</span>
                    </div>
                </div>
                <div class="col-md-4" data-aos="flip-up" data-aos-duration="600" data-aos-delay="100">
                    <div class="tool-card">
                        <div class="icon"><i class="fas fa-cube" style="color: #31a8ff;"></i></div>
                        <h5>Adobe Photoshop</h5>
                        <span class="level">Basic</span>
                    </div>
                </div>
                <div class="col-md-4" data-aos="flip-up" data-aos-duration="600" data-aos-delay="200">
                    <div class="tool-card">
                        <div class="icon"><i class="fas fa-bezier-curve" style="color: #a259ff;"></i></div>
                        <h5>Figma</h5>
                        <span class="level">Professional</span>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- SERVICES -->
    <section class="section-padding" id="services">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">My <span class="gradient-text">Services</span></h2>
                <p class="section-subtitle">What I can do for you</p>
            </div>
            <div class="row g-4 mt-4">
                <div class="col-6 col-md-4" data-aos="flip-left" data-aos-duration="500" data-aos-delay="0">
                    <div class="service-card">
                        <div class="icon"><i class="fab fa-instagram"></i></div>
                        <h5>Instagram Post Design</h5>
                        <p>Eye-catching social posts</p>
                    </div>
                </div>
                <div class="col-6 col-md-4" data-aos="flip-left" data-aos-duration="500" data-aos-delay="100">
                    <div class="service-card">
                        <div class="icon"><i class="fas fa-poster"></i></div>
                        <h5>Poster Design</h5>
                        <p>Creative &amp; professional posters</p>
                    </div>
                </div>
                <div class="col-6 col-md-4" data-aos="flip-left" data-aos-duration="500" data-aos-delay="200">
                    <div class="service-card">
                        <div class="icon"><i class="fas fa-chart-line"></i></div>
                        <h5>Business Ads</h5>
                        <p>Promotional ad designs</p>
                    </div>
                </div>
                <div class="col-6 col-md-4" data-aos="flip-left" data-aos-duration="500" data-aos-delay="300">
                    <div class="service-card">
                        <div class="icon"><i class="fas fa-bullhorn"></i></div>
                        <h5>Promotional Creatives</h5>
                        <p>Engaging promo materials</p>
                    </div>
                </div>
                <div class="col-6 col-md-4" data-aos="flip-left" data-aos-duration="500" data-aos-delay="400">
                    <div class="service-card">
                        <div class="icon"><i class="fab fa-youtube"></i></div>
                        <h5>YouTube Thumbnails</h5>
                        <p>Click-worthy thumbnails</p>
                    </div>
                </div>
                <div class="col-6 col-md-4" data-aos="flip-left" data-aos-duration="500" data-aos-delay="500">
                    <div class="service-card">
                        <div class="icon"><i class="fas fa-tag"></i></div>
                        <h5>Logo Design (Basic)</h5>
                        <p>Simple &amp; clean logos</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 mx-auto" data-aos="flip-left" data-aos-duration="500" data-aos-delay="600">
                    <div class="service-card">
                        <div class="icon"><i class="fas fa-bullseye"></i></div>
                        <h5>Social Media Branding</h5>
                        <p>Consistent brand presence</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- PORTFOLIO -->
    <section class="section-padding" id="portfolio" style="background: var(--bg-secondary);">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">My <span class="gradient-text">Portfolio</span></h2>
                <p class="section-subtitle">Some of my recent design projects</p>
            </div>
            <div class="portfolio-filter text-center mt-4" data-aos="fade-up" data-aos-duration="600" data-aos-delay="100">
                <button class="btn active" data-filter="all">All</button>
                <button class="btn" data-filter="social">Social Media</button>
                <button class="btn" data-filter="posters">Posters</button>
                <button class="btn" data-filter="branding">Branding</button>
                <button class="btn" data-filter="thumbnails">Thumbnails</button>
                <button class="btn" data-filter="logos">Logos</button>
            </div>
            <div class="row g-4 mt-3" id="portfolioGrid"></div>
        </div>
    </section>

    <!-- WORK PROCESS -->
    <section class="section-padding" id="process">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">My Work <span class="gradient-text">Process</span></h2>
                <p class="section-subtitle">How I bring your vision to life</p>
            </div>
            <div class="row g-4 mt-4 justify-content-center">
                <div class="col-md-6 col-lg-4" data-aos="fade-up" data-aos-duration="500" data-aos-delay="0">
                    <div class="process-step">
                        <div class="step-num">1</div>
                        <div class="step-content">
                            <h5>Understanding Client Requirements</h5>
                            <p>I listen carefully to your needs and goals.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 col-lg-4" data-aos="fade-up" data-aos-duration="500" data-aos-delay="100">
                    <div class="process-step">
                        <div class="step-num">2</div>
                        <div class="step-content">
                            <h5>Research &amp; Planning</h5>
                            <p>I research trends and plan the design approach.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 col-lg-4" data-aos="fade-up" data-aos-duration="500" data-aos-delay="200">
                    <div class="process-step">
                        <div class="step-num">3</div>
                        <div class="step-content">
                            <h5>Initial Design Concepts</h5>
                            <p>I create initial concepts for your review.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 col-lg-4" data-aos="fade-up" data-aos-duration="500" data-aos-delay="300">
                    <div class="process-step">
                        <div class="step-num">4</div>
                        <div class="step-content">
                            <h5>Revisions &amp; Improvements</h5>
                            <p>I refine the design based on your feedback.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 col-lg-4" data-aos="fade-up" data-aos-duration="500" data-aos-delay="400">
                    <div class="process-step">
                        <div class="step-num">5</div>
                        <div class="step-content">
                            <h5>Final High-Quality Delivery</h5>
                            <p>I deliver the final polished design files.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- EXPERIENCE -->
    <section class="section-padding" id="experience" style="background: var(--bg-secondary);">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">My <span class="gradient-text">Experience</span></h2>
                <p class="section-subtitle">Design journey &amp; professional growth</p>
            </div>
            <div class="row g-4 mt-4">
                <div class="col-lg-6" data-aos="fade-right" data-aos-duration="600">
                    <div class="timeline-item">
                        <span class="date">2023 – Present</span>
                        <h5>Social Media Creative Designs</h5>
                        <p>Creating engaging social media visuals for brands.</p>
                    </div>
                    <div class="timeline-item">
                        <span class="date">2022 – 2023</span>
                        <h5>Branding Concepts</h5>
                        <p>Developed branding materials for startups.</p>
                    </div>
                </div>
                <div class="col-lg-6" data-aos="fade-left" data-aos-duration="600">
                    <div class="timeline-item">
                        <span class="date">2021 – 2022</span>
                        <h5>Promotional Design Projects</h5>
                        <p>Designed promotional creatives for campaigns.</p>
                    </div>
                    <div class="timeline-item">
                        <span class="date">2020 – Present</span>
                        <h5>Continuous Learning &amp; Skill Development</h5>
                        <p>Staying updated with the latest design trends.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- EDUCATION -->
    <section class="section-padding" id="education">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">My <span class="gradient-text">Education</span></h2>
                <p class="section-subtitle">Academic background</p>
            </div>
            <div class="row justify-content-center mt-4">
                <div class="col-lg-6" data-aos="flip-up" data-aos-duration="600">
                    <div class="p-4 rounded-4 text-center" style="background: var(--bg-card); box-shadow: var(--shadow); border: 1px solid var(--border-color);">
                        <i class="fas fa-graduation-cap" style="font-size: 2.8rem; color: #6c5ce7; margin-bottom: 12px;"></i>
                        <h5 style="font-weight: 600; color: var(--text-primary);">12th (Arts Stream)</h5>
                        <p style="color: var(--text-muted); margin: 0;">Punjab Board</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- WHY CHOOSE ME -->
    <section class="section-padding" id="why-me" style="background: var(--bg-secondary);">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">Why Choose <span class="gradient-text">Me</span></h2>
                <p class="section-subtitle">What sets me apart</p>
            </div>
            <div class="row g-4 mt-4">
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="400" data-aos-delay="0">
                    <div class="feature-card">
                        <div class="icon"><i class="fas fa-paint-brush"></i></div>
                        <h5>Clean &amp; Modern Designs</h5>
                        <p>Minimalist &amp; professional visuals</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="400" data-aos-delay="100">
                    <div class="feature-card">
                        <div class="icon"><i class="fas fa-bolt"></i></div>
                        <h5>Quick Response</h5>
                        <p>Fast &amp; reliable communication</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="400" data-aos-delay="200">
                    <div class="feature-card">
                        <div class="icon"><i class="fas fa-tag"></i></div>
                        <h5>Affordable Pricing</h5>
                        <p>Quality designs at fair rates</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="400" data-aos-delay="300">
                    <div class="feature-card">
                        <div class="icon"><i class="fas fa-smile"></i></div>
                        <h5>Client Satisfaction</h5>
                        <p>100% satisfaction guaranteed</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="400" data-aos-delay="400">
                    <div class="feature-card">
                        <div class="icon"><i class="fas fa-clock"></i></div>
                        <h5>On-Time Delivery</h5>
                        <p>Projects delivered on schedule</p>
                    </div>
                </div>
                <div class="col-6 col-md-4 col-lg-3" data-aos="zoom-in" data-aos-duration="400" data-aos-delay="500">
                    <div class="feature-card">
                        <div class="icon"><i class="fas fa-comments"></i></div>
                        <h5>Professional Communication</h5>
                        <p>Clear &amp; transparent dialogue</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- TESTIMONIALS -->
    <section class="section-padding" id="testimonials">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">Client <span class="gradient-text">Testimonials</span></h2>
                <p class="section-subtitle">What my clients say about my work</p>
            </div>
            <div class="row g-4 mt-4">
                <div class="col-md-4" data-aos="flip-left" data-aos-duration="600" data-aos-delay="0">
                    <div class="testimonial-card">
                        <div class="stars"><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i></div>
                        <p class="quote">"Rishu created stunning social media posts for our brand. Highly professional and creative!"</p>
                        <div class="profile">
                            <div class="avatar">AK</div>
                            <div>
                                <p class="name">Ananya Kumar</p>
                                <p class="role">Social Media Manager</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4" data-aos="flip-left" data-aos-duration="600" data-aos-delay="100">
                    <div class="testimonial-card">
                        <div class="stars"><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i></div>
                        <p class="quote">"The poster designs were exactly what we needed. Rishu understood our vision perfectly."</p>
                        <div class="profile">
                            <div class="avatar">RS</div>
                            <div>
                                <p class="name">Rahul Singh</p>
                                <p class="role">Business Owner</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4" data-aos="flip-left" data-aos-duration="600" data-aos-delay="200">
                    <div class="testimonial-card">
                        <div class="stars"><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i></div>
                        <p class="quote">"Amazing work on our branding materials. Rishu is a talented designer with great attention to detail."</p>
                        <div class="profile">
                            <div class="avatar">PM</div>
                            <div>
                                <p class="name">Priya Mehta</p>
                                <p class="role">Marketing Head</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- PRICING -->
    <section class="section-padding" id="pricing" style="background: var(--bg-secondary);">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">Pricing <span class="gradient-text">Plans</span></h2>
                <p class="section-subtitle">Choose a plan that fits your needs</p>
            </div>
            <div class="row g-4 mt-4 justify-content-center">
                <div class="col-md-4" data-aos="flip-up" data-aos-duration="600" data-aos-delay="0">
                    <div class="pricing-card">
                        <h5 class="plan-name">Basic</h5>
                        <div class="price">₹999 <span>/ project</span></div>
                        <ul class="features">
                            <li><i class="fas fa-check"></i> 1 Social Media Post</li>
                            <li><i class="fas fa-check"></i> 1 Revision</li>
                            <li><i class="fas fa-check"></i> 2 Design Concepts</li>
                            <li><i class="fas fa-check"></i> 48hr Delivery</li>
                        </ul>
                        <a href="#contact" class="btn btn-outline-gradient">Get Started</a>
                    </div>
                </div>
                <div class="col-md-4" data-aos="flip-up" data-aos-duration="600" data-aos-delay="100">
                    <div class="pricing-card popular">
                        <h5 class="plan-name">Standard</h5>
                        <div class="price">₹2,499 <span>/ project</span></div>
                        <ul class="features">
                            <li><i class="fas fa-check"></i> 5 Social Media Posts</li>
                            <li><i class="fas fa-check"></i> 3 Revisions</li>
                            <li><i class="fas fa-check"></i> 5 Design Concepts</li>
                            <li><i class="fas fa-check"></i> 24hr Delivery</li>
                            <li><i class="fas fa-check"></i> Brand Guideline</li>
                        </ul>
                        <a href="#contact" class="btn btn-primary-gradient">Get Started</a>
                    </div>
                </div>
                <div class="col-md-4" data-aos="flip-up" data-aos-duration="600" data-aos-delay="200">
                    <div class="pricing-card">
                        <h5 class="plan-name">Premium</h5>
                        <div class="price">₹4,999 <span>/ project</span></div>
                        <ul class="features">
                            <li><i class="fas fa-check"></i> 10+ Social Media Posts</li>
                            <li><i class="fas fa-check"></i> Unlimited Revisions</li>
                            <li><i class="fas fa-check"></i> 10+ Design Concepts</li>
                            <li><i class="fas fa-check"></i> 12hr Delivery</li>
                            <li><i class="fas fa-check"></i> Full Branding Package</li>
                            <li><i class="fas fa-check"></i> Priority Support</li>
                        </ul>
                        <a href="#contact" class="btn btn-outline-gradient">Get Started</a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- FAQ -->
    <section class="section-padding" id="faq">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">Frequently Asked <span class="gradient-text">Questions</span></h2>
                <p class="section-subtitle">Everything you need to know</p>
            </div>
            <div class="row justify-content-center mt-4">
                <div class="col-lg-8" data-aos="fade-up" data-aos-duration="800">
                    <div class="accordion accordion-custom" id="faqAccordion">
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#faq1">
                                    What services do you offer?
                                </button>
                            </h2>
                            <div id="faq1" class="accordion-collapse collapse show" data-bs-parent="#faqAccordion">
                                <div class="accordion-body">I offer social media post design, poster design, business ads, promotional creatives, YouTube thumbnails, basic logo design, and social media branding.</div>
                            </div>
                        </div>
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faq2">
                                    How long does a project take?
                                </button>
                            </h2>
                            <div id="faq2" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                                <div class="accordion-body">Project timelines vary based on complexity. Typically, a single design takes 24-48 hours, while larger projects may take 3-7 days.</div>
                            </div>
                        </div>
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faq3">
                                    What is your revision policy?
                                </button>
                            </h2>
                            <div id="faq3" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                                <div class="accordion-body">I offer revisions based on the package you choose. Basic packages include 1-2 revisions, while premium packages include unlimited revisions.</div>
                            </div>
                        </div>
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faq4">
                                    Do you provide source files?
                                </button>
                            </h2>
                            <div id="faq4" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                                <div class="accordion-body">Yes, I provide source files (Canva, Photoshop, or Figma) along with high-resolution exports upon project completion.</div>
                            </div>
                        </div>
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#faq5">
                                    How do I get started?
                                </button>
                            </h2>
                            <div id="faq5" class="accordion-collapse collapse" data-bs-parent="#faqAccordion">
                                <div class="accordion-body">Simply reach out via the contact form, WhatsApp, or Instagram. I'll get back to you within a few hours to discuss your project.</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- CONTACT -->
    <section class="section-padding" id="contact" style="background: var(--bg-secondary);">
        <div class="container">
            <div class="text-center" data-aos="fade-up" data-aos-duration="600">
                <h2 class="section-title">Get In <span class="gradient-text">Touch</span></h2>
                <p class="section-subtitle">Have a project? Let's talk!</p>
            </div>
            <div class="row g-5 mt-3">
                <div class="col-lg-6" data-aos="fade-right" data-aos-duration="600">
                    <form class="contact-form" id="contactForm">
                        <div class="row g-3">
                            <div class="col-12">
                                <input type="text" class="form-control" placeholder="Your Full Name" required />
                            </div>
                            <div class="col-12">
                                <input type="email" class="form-control" placeholder="Your Email Address" required />
                            </div>
                            <div class="col-12">
                                <input type="tel" class="form-control" placeholder="Your Phone Number" />
                            </div>
                            <div class="col-12">
                                <textarea class="form-control" rows="5" placeholder="Tell me about your project..." required></textarea>
                            </div>
                            <div class="col-12">
                                <button type="submit" class="btn btn-submit w-100 w-sm-auto">
                                    <i class="fas fa-paper-plane me-2"></i> Send Message
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="col-lg-6" data-aos="fade-left" data-aos-duration="600">
                    <div class="p-4 rounded-4" style="background: var(--bg-card); box-shadow: var(--shadow); border: 1px solid var(--border-color);">
                        <h5 style="font-weight: 600; margin-bottom: 20px; color: var(--text-primary);">Contact Information</h5>
                        <div class="contact-info-item">
                            <div class="icon"><i class="fab fa-instagram"></i></div>
                            <div class="info">
                                <div class="label">Instagram</div>
                                <div class="value"><a href="https://instagram.com/rishu_designs_467" target="_blank">@rishu_designs_467</a></div>
                            </div>
                        </div>
                        <div class="contact-info-item">
                            <div class="icon"><i class="fab fa-whatsapp"></i></div>
                            <div class="info">
                                <div class="label">WhatsApp</div>
                                <div class="value">
                                    <a href="https://wa.me/919592851314?text=Hi%20Rishu%2C%20I%20found%20your%20portfolio%20and%20would%20like%20to%20discuss%20a%20project." target="_blank">+91 9592851314</a>
                                </div>
                            </div>
                        </div>
                        <div class="contact-info-item">
                            <div class="icon"><i class="fas fa-envelope"></i></div>
                            <div class="info">
                                <div class="label">Email</div>
                                <div class="value"><a href="mailto:nrishu106@gmail.com">nrushu106@gmail.com</a></div>
                            </div>
                        </div>
                        <div class="mt-4">
                            <a href="https://wa.me/919592851314?text=Hi%20Rishu%2C%20I%20found%20your%20portfolio%20and%20would%20like%20to%20discuss%20a%20project." target="_blank" class="btn btn-success w-100" style="border-radius: 50px; padding: 14px; font-weight: 600;">
                                <i class="fab fa-whatsapp me-2"></i> Chat on WhatsApp
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- FOOTER -->
    <footer class="footer">
        <div class="container">
            <div class="row g-4">
                <div class="col-md-4">
                    <h5>Rishu Thakur</h5>
                    <p style="max-width: 280px;">Creative graphic designer specializing in social media creatives, posters, branding, and promotional designs.</p>
                    <div class="social-links mt-3">
                        <a href="#" aria-label="Instagram"><i class="fab fa-instagram"></i></a>
                        <a href="#" aria-label="WhatsApp"><i class="fab fa-whatsapp"></i></a>
                        <a href="#" aria-label="Behance"><i class="fab fa-behance"></i></a>
                        <a href="#" aria-label="Dribbble"><i class="fab fa-dribbble"></i></a>
                    </div>
                </div>
                <div class="col-6 col-md-2">
                    <h5>Quick Links</h5>
                    <ul class="list-unstyled">
                        <li><a href="#home">Home</a></li>
                        <li><a href="#about">About</a></li>
                        <li><a href="#skills">Skills</a></li>
                        <li><a href="#services">Services</a></li>
                        <li><a href="#portfolio">Portfolio</a></li>
                    </ul>
                </div>
                <div class="col-6 col-md-2">
                    <h5>Services</h5>
                    <ul class="list-unstyled">
                        <li><a href="#services">Poster Design</a></li>
                        <li><a href="#services">Social Media</a></li>
                        <li><a href="#services">Branding</a></li>
                        <li><a href="#services">Thumbnails</a></li>
                        <li><a href="#services">Logo Design</a></li>
                    </ul>
                </div>
                <div class="col-md-4">
                    <h5>Contact</h5>
                    <ul class="list-unstyled">
                        <li><a href="https://instagram.com/rishu_designs_467" target="_blank"><i class="fab fa-instagram me-2"></i>@rishu_designs_467</a></li>
                        <li><a href="https://wa.me/919592851314" target="_blank"><i class="fab fa-whatsapp me-2"></i>+91 9592851314</a></li>
                        <li><a href="mailto:nrishu106@gmail.com"><i class="fas fa-envelope me-2"></i>nrushu106@gmail.com</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p class="mb-0">
                    &copy; 2026 <span>Rishu Thakur</span>. All Rights Reserved. &nbsp;|&nbsp;
                    Made with <i class="fas fa-heart" style="color: #fd79a8;"></i> by Virat Rajput
                </p>
                <p class="mb-0 mt-1" style="font-size: 0.75rem; opacity: 0.5;">Premium Portfolio Website | Software Developer</p>
            </div>
        </div>
    </footer>

    <!-- BOOTSTRAP JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <!-- AOS -->
    <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>

    <!-- CUSTOM JS -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Loader
            const loader = document.getElementById('loader');
            window.addEventListener('load', function() {
                setTimeout(() => { loader.classList.add('hidden'); }, 600);
            });

            // Typing Animation
            const typedText = document.getElementById('typedText');
            const phrases = ['Graphic Designer', 'Digital Creator', 'Social Media Designer', 'Branding Specialist', 'Creative Visionary'];
            let phraseIndex = 0, charIndex = 0, isDeleting = false, typingSpeed = 80;
            function typeEffect() {
                const current = phrases[phraseIndex];
                if (!isDeleting) {
                    typedText.textContent = current.substring(0, charIndex + 1);
                    charIndex++;
                    if (charIndex === current.length) { isDeleting = true; typingSpeed = 2000; } 
                    else { typingSpeed = 80 + Math.random() * 40; }
                } else {
                    typedText.textContent = current.substring(0, charIndex - 1);
                    charIndex--;
                    if (charIndex === 0) { isDeleting = false; phraseIndex = (phraseIndex + 1) % phrases.length; typingSpeed = 400; } 
                    else { typingSpeed = 40 + Math.random() * 30; }
                }
                setTimeout(typeEffect, typingSpeed);
            }
            typeEffect();

            // Theme Toggle
            const themeToggle = document.getElementById('themeToggle');
            const themeIcon = themeToggle.querySelector('i');
            let currentTheme = localStorage.getItem('theme') || 'dark';
            if (currentTheme === 'light') {
                document.documentElement.setAttribute('data-theme', 'light');
                themeIcon.className = 'fas fa-sun';
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                themeIcon.className = 'fas fa-moon';
            }
            themeToggle.addEventListener('click', function() {
                const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
                if (isDark) {
                    document.documentElement.setAttribute('data-theme', 'light');
                    themeIcon.className = 'fas fa-sun';
                    localStorage.setItem('theme', 'light');
                } else {
                    document.documentElement.setAttribute('data-theme', 'dark');
                    themeIcon.className = 'fas fa-moon';
                    localStorage.setItem('theme', 'dark');
                }
            });

            // Navbar Active Link
            const navLinks = document.querySelectorAll('.navbar-custom .nav-link');
            const sections = document.querySelectorAll('section[id]');
            function updateActiveLink() {
                let current = '';
                sections.forEach(section => {
                    const top = section.offsetTop - 120;
                    if (window.scrollY >= top) { current = section.getAttribute('id'); }
                });
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === '#' + current) { link.classList.add('active'); }
                });
            }
            window.addEventListener('scroll', updateActiveLink);

            // Scroll to Top
            const scrollBtn = document.getElementById('scrollTopBtn');
            window.addEventListener('scroll', function() {
                if (window.scrollY > 400) { scrollBtn.classList.add('visible'); } 
                else { scrollBtn.classList.remove('visible'); }
            });
            scrollBtn.addEventListener('click', function() { window.scrollTo({ top: 0, behavior: 'smooth' }); });

            // AOS Init
            AOS.init({ duration: 800, once: true, offset: 40, easing: 'ease-out-cubic' });

            // Portfolio Data
            const portfolioData = [
                { id: 1, title: 'Social Media Campaign', category: 'social', emoji: '📱' },
                { id: 2, title: 'Brand Poster Series', category: 'posters', emoji: '🖼️' },
                { id: 3, title: 'Brand Identity Pack', category: 'branding', emoji: '🏷️' },
                { id: 4, title: 'YouTube Thumbnail Set', category: 'thumbnails', emoji: '▶️' },
                { id: 5, title: 'Minimalist Logo', category: 'logos', emoji: '🔷' },
                { id: 6, title: 'Instagram Story Design', category: 'social', emoji: '📸' },
                { id: 7, title: 'Event Poster', category: 'posters', emoji: '🎪' },
                { id: 8, title: 'Brand Style Guide', category: 'branding', emoji: '📘' },
                { id: 9, title: 'Gaming Thumbnail', category: 'thumbnails', emoji: '🎮' },
                { id: 10, title: 'Modern Logo Design', category: 'logos', emoji: '💠' },
                { id: 11, title: 'Social Media Banner', category: 'social', emoji: '🎯' },
                { id: 12, title: 'Promotional Flyer', category: 'posters', emoji: '📄' }
            ];

            const grid = document.getElementById('portfolioGrid');
            let currentFilter = 'all';

            function renderPortfolio(filter) {
                const filtered = filter === 'all' ? portfolioData : portfolioData.filter(p => p.category === filter);
                grid.innerHTML = '';
                filtered.forEach(item => {
                    const col = document.createElement('div');
                    col.className = 'col-6 col-md-4 col-lg-3';
                    col.dataset.category = item.category;
                    col.innerHTML = `
                        <div class="portfolio-item" data-id="${item.id}">
                            <div class="img-wrap">
                                <span style="font-size: 3rem;">${item.emoji}</span>
                                <div class="overlay">
                                    <i class="fas fa-search-plus"></i>
                                </div>
                            </div>
                            <div class="info">
                                <h5>${item.title}</h5>
                                <span class="category">${item.category.charAt(0).toUpperCase() + item.category.slice(1)}</span>
                            </div>
                        </div>
                    `;
                    grid.appendChild(col);
                    col.querySelector('.portfolio-item').addEventListener('click', function() {
                        openLightbox(item.title, item.category, item.emoji);
                    });
                });
            }
            renderPortfolio('all');

            document.querySelectorAll('.portfolio-filter .btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.portfolio-filter .btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    currentFilter = this.dataset.filter;
                    renderPortfolio(currentFilter);
                });
            });

            // Lightbox
            const lightbox = document.getElementById('lightbox');
            const lightboxClose = document.getElementById('lightboxClose');
            const lightboxImage = document.getElementById('lightboxImage');
            const lightboxTitle = document.getElementById('lightboxTitle');
            const lightboxCategory = document.getElementById('lightboxCategory');

            function openLightbox(title, category, emoji) {
                lightboxImage.innerHTML = `<span style="font-size: 5rem;">${emoji}</span>`;
                lightboxTitle.textContent = title;
                lightboxCategory.textContent = category.charAt(0).toUpperCase() + category.slice(1);
                lightbox.classList.add('active');
                document.body.style.overflow = 'hidden';
            }

            function closeLightbox() {
                lightbox.classList.remove('active');
                document.body.style.overflow = '';
            }

            lightboxClose.addEventListener('click', closeLightbox);
            lightbox.addEventListener('click', function(e) { if (e.target === this) closeLightbox(); });
            document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeLightbox(); });

            // Skill Progress Bars
            const progressBars = document.querySelectorAll('.progress-bar');
            let progressAnimated = false;

            function animateProgress() {
                if (progressAnimated) return;
                const rect = document.querySelector('.progress-skill')?.getBoundingClientRect();
                if (!rect) return;
                if (rect.top < window.innerHeight - 60) {
                    progressBars.forEach(bar => {
                        const width = bar.dataset.width || '0';
                        bar.style.width = width + '%';
                        bar.classList.add('animated');
                    });
                    progressAnimated = true;
                }
            }
            window.addEventListener('scroll', animateProgress);
            setTimeout(animateProgress, 800);

            // Smooth Scroll for Nav Links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function(e) {
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        e.preventDefault();
                        const offsetTop = target.offsetTop - 70;
                        window.scrollTo({ top: offsetTop, behavior: 'smooth' });
                        const navCollapse = document.getElementById('navMenu');
                        if (navCollapse.classList.contains('show')) {
                            const bsCollapse = bootstrap.Collapse.getInstance(navCollapse);
                            if (bsCollapse) bsCollapse.hide();
                        }
                    }
                });
            });

            // Contact Form with Backend API
            document.getElementById('contactForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const btn = this.querySelector('.btn-submit');
                const original = btn.innerHTML;
                
                const formData = {
                    name: this.querySelector('input[type="text"]').value,
                    email: this.querySelector('input[type="email"]').value,
                    phone: this.querySelector('input[type="tel"]').value,
                    message: this.querySelector('textarea').value
                };
                
                btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Sending...';
                btn.disabled = true;
                
                fetch('/api/contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        btn.innerHTML = '<i class="fas fa-check me-2"></i> Message Sent!';
                        btn.style.background = 'linear-gradient(135deg, #00b894, #00a381)';
                        this.reset();
                    } else {
                        btn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i> Error!';
                        btn.style.background = 'linear-gradient(135deg, #e17055, #d63031)';
                        alert(data.error || 'Something went wrong. Please try again.');
                    }
                    setTimeout(() => {
                        btn.innerHTML = original;
                        btn.style.background = '';
                        btn.disabled = false;
                    }, 3000);
                })
                .catch(() => {
                    btn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i> Error!';
                    btn.style.background = 'linear-gradient(135deg, #e17055, #d63031)';
                    alert('Network error. Please try again.');
                    setTimeout(() => {
                        btn.innerHTML = original;
                        btn.style.background = '';
                        btn.disabled = false;
                    }, 3000);
                });
            });

            console.log('🚀 Rishu Thakur Portfolio loaded successfully!');
            console.log('💡 Made with ❤️ by Virat Rajput');
        });
    </script>

</body>
</html>
'''

# ============================================
# FRONTEND ROUTE
# ============================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# ============================================
# CREATE TABLES
# ============================================

with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)