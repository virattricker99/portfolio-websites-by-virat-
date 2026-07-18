import os
import sys
import re
from datetime import datetime

from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# ============================================
# APP INITIALIZATION
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

# Fix for Render PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
elif not DATABASE_URL:
    DATABASE_URL = 'sqlite:///portfolio.db'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
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
# HTML TEMPLATE
# ============================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rishu Thakur | Graphic Designer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        :root {
            --bg-primary: #f8f9fa;
            --bg-secondary: #ffffff;
            --text-primary: #1a1a2e;
            --gradient-primary: linear-gradient(135deg, #6c5ce7, #a29bfe);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow-x: hidden;
        }
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 120px 0 80px;
            background: var(--bg-primary);
        }
        .hero h1 { font-size: 4.2rem; font-weight: 800; }
        .hero h1 .highlight {
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .section-title {
            font-weight: 700;
            font-size: 2.5rem;
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
        .gradient-text {
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .section-padding { padding: 100px 0 80px; }
        .btn-primary-gradient {
            background: var(--gradient-primary);
            color: #fff;
            border: none;
            padding: 12px 34px;
            border-radius: 50px;
            font-weight: 600;
            transition: 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        .btn-primary-gradient:hover { transform: translateY(-3px); color: #fff; box-shadow: 0 8px 30px rgba(108,92,231,0.4); }
        .btn-outline-gradient {
            background: transparent;
            color: var(--text-primary);
            border: 2px solid #dee2e6;
            padding: 12px 34px;
            border-radius: 50px;
            font-weight: 600;
            transition: 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        .btn-outline-gradient:hover { border-color: #6c5ce7; color: #6c5ce7; transform: translateY(-3px); }
        .whatsapp-float {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 999;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #25d366;
            color: #fff;
            font-size: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 24px rgba(37,211,102,0.4);
            transition: 0.3s;
            animation: pulse 2s infinite;
            text-decoration: none;
        }
        .whatsapp-float:hover { transform: scale(1.1); color: #fff; }
        @keyframes pulse {
            0%, 100% { box-shadow: 0 4px 24px rgba(37,211,102,0.4); }
            50% { box-shadow: 0 4px 40px rgba(37,211,102,0.7); }
        }
        .skill-card {
            background: #fff;
            border-radius: 16px;
            padding: 28px 20px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.08);
            transition: 0.3s;
            height: 100%;
            border: 1px solid rgba(0,0,0,0.06);
        }
        .skill-card:hover { transform: translateY(-8px); box-shadow: 0 16px 48px rgba(0,0,0,0.12); }
        .skill-card .icon {
            font-size: 2.8rem;
            display: inline-block;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .skill-card h5 { font-weight: 600; font-size: 1.05rem; margin-top: 12px; }
        .skill-card p { font-size: 0.85rem; color: #6c757d; }
        .service-card {
            background: #fff;
            border-radius: 16px;
            padding: 32px 24px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.08);
            transition: 0.3s;
            height: 100%;
            border: 1px solid rgba(0,0,0,0.06);
        }
        .service-card:hover { transform: translateY(-8px); box-shadow: 0 16px 48px rgba(0,0,0,0.12); }
        .service-card .icon {
            font-size: 2.6rem;
            display: inline-block;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .service-card h5 { font-weight: 600; font-size: 1.05rem; margin-top: 12px; }
        .service-card p { font-size: 0.9rem; color: #6c757d; }
        .footer {
            background: #1a1a2e;
            color: #dfe6e9;
            padding: 60px 0 0;
        }
        .footer h5 { font-weight: 700; font-size: 1.1rem; color: #fff; margin-bottom: 18px; }
        .footer a { color: #dfe6e9; transition: 0.3s; text-decoration: none; }
        .footer a:hover { color: #a29bfe; padding-left: 4px; }
        .footer .footer-bottom {
            border-top: 1px solid rgba(255,255,255,0.06);
            padding: 20px 0;
            margin-top: 40px;
            text-align: center;
            font-size: 0.85rem;
            color: rgba(255,255,255,0.4);
        }
        .footer .footer-bottom span { color: #a29bfe; }
        .hero-image {
            width: 350px;
            height: 350px;
            border-radius: 50%;
            border: 4px solid #6c5ce7;
            overflow: hidden;
            margin: 0 auto;
        }
        .hero-image img { width: 100%; height: 100%; object-fit: cover; }
        .contact-form .form-control {
            background: #f1f2f6;
            border: 1px solid #dfe6e9;
            border-radius: 12px;
            padding: 14px 18px;
        }
        .contact-form .form-control:focus {
            border-color: #6c5ce7;
            box-shadow: 0 0 0 4px rgba(108,92,231,0.12);
        }
        .contact-info-item {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 14px 0;
            border-bottom: 1px solid rgba(0,0,0,0.08);
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
        .navbar-custom {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(16px);
            box-shadow: 0 2px 20px rgba(0,0,0,0.06);
            padding: 12px 0;
        }
        .navbar-custom .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
            color: var(--text-primary);
        }
        .navbar-custom .navbar-brand span { color: #6c5ce7; }
        .navbar-custom .nav-link {
            font-weight: 500;
            font-size: 0.95rem;
            color: var(--text-secondary) !important;
            padding: 8px 16px !important;
            transition: 0.3s;
        }
        .navbar-custom .nav-link:hover { color: #6c5ce7 !important; }
        @media (max-width: 768px) {
            .hero h1 { font-size: 2.4rem; }
            .hero { text-align: center; padding: 100px 0 50px; }
            .section-title { font-size: 1.7rem; }
            .hero-image { width: 220px; height: 220px; }
            .whatsapp-float { width: 50px; height: 50px; font-size: 1.6rem; bottom: 20px; right: 20px; }
        }
    </style>
</head>
<body>

    <!-- NAVBAR -->
    <nav class="navbar navbar-expand-lg navbar-custom fixed-top">
        <div class="container">
            <a class="navbar-brand" href="#home">Rishu <span>Thakur</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navMenu">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link active" href="#home">Home</a></li>
                    <li class="nav-item"><a class="nav-link" href="#about">About</a></li>
                    <li class="nav-item"><a class="nav-link" href="#skills">Skills</a></li>
                    <li class="nav-item"><a class="nav-link" href="#services">Services</a></li>
                    <li class="nav-item"><a class="nav-link" href="#contact">Contact</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- HERO -->
    <section class="hero" id="home">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <div class="badge bg-primary bg-opacity-10 text-primary px-4 py-2 rounded-pill mb-3">
                        <i class="fas fa-palette me-2"></i> Graphic Designer
                    </div>
                    <h1>I'm <span class="highlight">Rishu Thakur</span></h1>
                    <p class="fs-5 text-muted">Graphic Designer & Digital Creator</p>
                    <p class="text-muted">Creative designer specializing in social media creatives, posters, branding, and promotional designs that help businesses grow.</p>
                    <div class="d-flex gap-3 flex-wrap">
                        <a href="#contact" class="btn btn-primary-gradient"><i class="fas fa-paper-plane me-2"></i> Hire Me</a>
                        <a href="#contact" class="btn btn-outline-gradient"><i class="fas fa-envelope me-2"></i> Contact</a>
                    </div>
                </div>
                <div class="col-lg-6 text-center">
                    <div class="hero-image">
                        <img src="https://i.ibb.co/fzzsVSdq/file-00000000949c720b931c888810bd71a3.png" alt="Rishu Thakur">
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- ABOUT -->
    <section class="section-padding" id="about" style="background:#fff;">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-5 text-center">
                    <div class="rounded-4 overflow-hidden shadow" style="max-width:400px;margin:0 auto;">
                        <img src="https://i.ibb.co/cSHZzgdz/file-000000004af871fabfa6c0c3adcd24bb.png" alt="About" style="width:100%;height:100%;object-fit:cover;">
                    </div>
                </div>
                <div class="col-lg-7">
                    <h2 class="section-title text-start">About <span class="gradient-text">Me</span></h2>
                    <p class="text-muted mt-3">Hi, I'm Rishu Thakur, a creative and passionate Graphic Designer &amp; Digital Creator.</p>
                    <p class="text-muted">I specialize in creating eye-catching designs such as social media creatives, posters, and branding materials. I focus on delivering clean, modern, and professional designs that help businesses grow their online presence.</p>
                    <p class="text-muted">I continuously improve my skills and stay updated with the latest design trends.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- SKILLS -->
    <section class="section-padding" id="skills">
        <div class="container">
            <div class="text-center">
                <h2 class="section-title">My <span class="gradient-text">Skills</span></h2>
                <p class="text-muted">Expertise in design tools and techniques</p>
            </div>
            <div class="row g-4 mt-4">
                <div class="col-6 col-md-3"><div class="skill-card"><div class="icon"><i class="fas fa-paint-brush"></i></div><h5>Graphic Design</h5><p>Creative visual design</p></div></div>
                <div class="col-6 col-md-3"><div class="skill-card"><div class="icon"><i class="fas fa-hashtag"></i></div><h5>Social Media</h5><p>Engaging social creatives</p></div></div>
                <div class="col-6 col-md-3"><div class="skill-card"><div class="icon"><i class="fas fa-poster"></i></div><h5>Poster Design</h5><p>Eye-catching posters</p></div></div>
                <div class="col-6 col-md-3"><div class="skill-card"><div class="icon"><i class="fas fa-building"></i></div><h5>Branding</h5><p>Brand identity design</p></div></div>
                <div class="col-6 col-md-3"><div class="skill-card"><div class="icon"><i class="fas fa-pen-fancy"></i></div><h5>Canva</h5><p>Advanced Canva expertise</p></div></div>
                <div class="col-6 col-md-3"><div class="skill-card"><div class="icon"><i class="fas fa-edit"></i></div><h5>Photoshop</h5><p>Basic photo editing</p></div></div>
                <div class="col-6 col-md-3"><div class="skill-card"><div class="icon"><i class="fas fa-layer-group"></i></div><h5>Layout</h5><p>Structured layouts</p></div></div>
                <div class="col-6 col-md-3"><div class="skill-card"><div class="icon"><i class="fas fa-palette"></i></div><h5>Typography</h5><p>Color &amp; font mastery</p></div></div>
            </div>
        </div>
    </section>

    <!-- SERVICES -->
    <section class="section-padding" id="services" style="background:#fff;">
        <div class="container">
            <div class="text-center">
                <h2 class="section-title">My <span class="gradient-text">Services</span></h2>
                <p class="text-muted">What I can do for you</p>
            </div>
            <div class="row g-4 mt-4">
                <div class="col-6 col-md-4"><div class="service-card"><div class="icon"><i class="fab fa-instagram"></i></div><h5>Instagram Post</h5><p>Eye-catching social posts</p></div></div>
                <div class="col-6 col-md-4"><div class="service-card"><div class="icon"><i class="fas fa-poster"></i></div><h5>Poster Design</h5><p>Creative &amp; professional posters</p></div></div>
                <div class="col-6 col-md-4"><div class="service-card"><div class="icon"><i class="fas fa-chart-line"></i></div><h5>Business Ads</h5><p>Promotional ad designs</p></div></div>
                <div class="col-6 col-md-4"><div class="service-card"><div class="icon"><i class="fas fa-bullhorn"></i></div><h5>Promotional</h5><p>Engaging promo materials</p></div></div>
                <div class="col-6 col-md-4"><div class="service-card"><div class="icon"><i class="fab fa-youtube"></i></div><h5>Thumbnails</h5><p>Click-worthy thumbnails</p></div></div>
                <div class="col-6 col-md-4"><div class="service-card"><div class="icon"><i class="fas fa-tag"></i></div><h5>Logo Design</h5><p>Simple &amp; clean logos</p></div></div>
            </div>
        </div>
    </section>

    <!-- CONTACT -->
    <section class="section-padding" id="contact">
        <div class="container">
            <div class="text-center">
                <h2 class="section-title">Get In <span class="gradient-text">Touch</span></h2>
                <p class="text-muted">Have a project? Let's talk!</p>
            </div>
            <div class="row g-5 mt-3">
                <div class="col-lg-6">
                    <form class="contact-form" id="contactForm">
                        <div class="mb-3">
                            <input type="text" class="form-control" placeholder="Your Full Name" id="name" required>
                        </div>
                        <div class="mb-3">
                            <input type="email" class="form-control" placeholder="Your Email Address" id="email" required>
                        </div>
                        <div class="mb-3">
                            <input type="tel" class="form-control" placeholder="Your Phone Number" id="phone">
                        </div>
                        <div class="mb-3">
                            <textarea class="form-control" rows="5" placeholder="Tell me about your project..." id="message" required></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary-gradient w-100">
                            <i class="fas fa-paper-plane me-2"></i> Send Message
                        </button>
                    </form>
                </div>
                <div class="col-lg-6">
                    <div class="card border-0 shadow p-4">
                        <h5 class="fw-bold">Contact Information</h5>
                        <div class="contact-info-item">
                            <div class="icon"><i class="fab fa-instagram"></i></div>
                            <div><small class="text-muted">Instagram</small><br><a href="https://instagram.com/rishu_designs_467" target="_blank" style="color:var(--text-primary);text-decoration:none;">@rishu_designs_467</a></div>
                        </div>
                        <div class="contact-info-item">
                            <div class="icon"><i class="fab fa-whatsapp"></i></div>
                            <div><small class="text-muted">WhatsApp</small><br><a href="https://wa.me/919592851314?text=Hi%20Rishu%2C%20I%20found%20your%20portfolio%20and%20would%20like%20to%20discuss%20a%20project." target="_blank" style="color:var(--text-primary);text-decoration:none;">+91 9592851314</a></div>
                        </div>
                        <div class="contact-info-item">
                            <div class="icon"><i class="fas fa-envelope"></i></div>
                            <div><small class="text-muted">Email</small><br><a href="mailto:nrishu106@gmail.com" style="color:var(--text-primary);text-decoration:none;">nrushu106@gmail.com</a></div>
                        </div>
                        <div class="mt-4">
                            <a href="https://wa.me/919592851314?text=Hi%20Rishu%2C%20I%20found%20your%20portfolio%20and%20would%20like%20to%20discuss%20a%20project." target="_blank" class="btn btn-success w-100" style="border-radius:50px;padding:14px;font-weight:600;">
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
                    <p class="text-muted">Creative graphic designer specializing in social media creatives, posters, branding, and promotional designs.</p>
                </div>
                <div class="col-6 col-md-2">
                    <h5>Quick Links</h5>
                    <ul class="list-unstyled">
                        <li><a href="#home">Home</a></li>
                        <li><a href="#about">About</a></li>
                        <li><a href="#skills">Skills</a></li>
                        <li><a href="#services">Services</a></li>
                    </ul>
                </div>
                <div class="col-6 col-md-2">
                    <h5>Services</h5>
                    <ul class="list-unstyled">
                        <li><a href="#services">Poster Design</a></li>
                        <li><a href="#services">Social Media</a></li>
                        <li><a href="#services">Branding</a></li>
                        <li><a href="#services">Thumbnails</a></li>
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
                <p class="mb-0">&copy; 2026 <span>Rishu Thakur</span>. All Rights Reserved. &nbsp;|&nbsp; Made with ❤️ by Virat Rajput</p>
            </div>
        </div>
    </footer>

    <!-- WHATSAPP FLOATING -->
    <a href="https://wa.me/919592851314?text=Hi%20Rishu%2C%20I%20found%20your%20portfolio%20and%20would%20like%20to%20discuss%20a%20project." target="_blank" class="whatsapp-float">
        <i class="fab fa-whatsapp"></i>
    </a>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Navbar active link
            const navLinks = document.querySelectorAll('.navbar-custom .nav-link');
            const sections = document.querySelectorAll('section[id]');
            
            function updateActiveLink() {
                let current = '';
                sections.forEach(section => {
                    const top = section.offsetTop - 120;
                    if (window.scrollY >= top) {
                        current = section.getAttribute('id');
                    }
                });
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === '#' + current) {
                        link.classList.add('active');
                    }
                });
            }
            window.addEventListener('scroll', updateActiveLink);
            updateActiveLink();

            // Smooth scroll
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function(e) {
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        e.preventDefault();
                        const offsetTop = target.offsetTop - 70;
                        window.scrollTo({ top: offsetTop, behavior: 'smooth' });
                    }
                });
            });

            // Contact Form
            document.getElementById('contactForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const btn = this.querySelector('button[type="submit"]');
                const original = btn.innerHTML;
                
                const data = {
                    name: document.getElementById('name').value,
                    email: document.getElementById('email').value,
                    phone: document.getElementById('phone').value,
                    message: document.getElementById('message').value
                };
                
                btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Sending...';
                btn.disabled = true;
                
                fetch('/api/contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        btn.innerHTML = '<i class="fas fa-check me-2"></i> Message Sent!';
                        btn.style.background = '#00b894';
                        this.reset();
                    } else {
                        btn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i> Error!';
                        btn.style.background = '#e17055';
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
                    btn.style.background = '#e17055';
                    alert('Network error. Please try again.');
                    setTimeout(() => {
                        btn.innerHTML = original;
                        btn.style.background = '';
                        btn.disabled = false;
                    }, 3000);
                });
            });
        });
    </script>
</body>
</html>'''

# ============================================
# FRONTEND ROUTE
# ============================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# ============================================
# CREATE TABLES & ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# APPLICATION ENTRY POINT
# ============================================

# This is the key fix - gunicorn looks for this variable
# Make sure this is at the bottom of the file

# Create tables if they don't exist
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"⚠️ Database creation warning: {e}")

# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)