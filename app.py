import os
import cloudinary
import cloudinary.uploader
from flask import Flask, request, jsonify, send_from_directory
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime, timedelta
import dotenv

dotenv.load_dotenv()

# ---------- App Initialization ----------
app = Flask(__name__)

# Configuration
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Extensions
mongo = PyMongo(app)
jwt = JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # restrict in production

# ---------- Helpers ----------
def serialize_doc(doc):
    if doc is None:
        return None
    doc['_id'] = str(doc['_id'])
    if 'user_id' in doc:
        doc['user_id'] = str(doc['user_id'])
    return doc

def get_user_by_email(email):
    return mongo.db.users.find_one({'email': email})

def create_user(username, email, password):
    hashed = generate_password_hash(password)
    user = {
        'username': username,
        'email': email,
        'password': hashed,
        'role': 'student',
        'created_at': datetime.utcnow()
    }
    result = mongo.db.users.insert_one(user)
    return result.inserted_id

def create_portfolio(user_id):
    portfolio = {
        'user_id': ObjectId(user_id),
        'fullName': '',
        'professionalTitle': '',
        'shortIntro': '',
        'careerObjective': '',
        'profileImage': '',
        'about': '',
        'interests': [],
        'futureGoals': '',
        'education': [],
        'skills': {'technical': [], 'tools': [], 'soft': []},
        'projects': [],
        'certificates': [],
        'achievements': [],
        'experiences': [],
        'resume': '',
        'contact': {'email': '', 'phone': '', 'linkedin': '', 'github': '', 'website': ''},
        'isPublished': False,
        'viewCount': 0
    }
    return mongo.db.portfolios.insert_one(portfolio).inserted_id

# ---------- AUTH ROUTES ----------
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Missing fields'}), 400

    if get_user_by_email(email):
        return jsonify({'message': 'Email already registered'}), 400
    if mongo.db.users.find_one({'username': username}):
        return jsonify({'message': 'Username taken'}), 400

    user_id = create_user(username, email, password)
    create_portfolio(user_id)
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = get_user_by_email(email)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(user['_id']))
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': str(user['_id']),
            'username': user['username'],
            'email': user['email'],
            'role': user.get('role', 'student')
        }
    }), 200

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify({
        'id': str(user['_id']),
        'username': user['username'],
        'email': user['email'],
        'role': user.get('role', 'student')
    }), 200

# ---------- PORTFOLIO ROUTES ----------
@app.route('/api/portfolio', methods=['GET'])
@jwt_required()
def get_my_portfolio():
    user_id = get_jwt_identity()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    if not portfolio:
        return jsonify({'message': 'Portfolio not found'}), 404
    return jsonify(serialize_doc(portfolio)), 200

@app.route('/api/portfolio', methods=['PUT'])
@jwt_required()
def update_portfolio():
    user_id = get_jwt_identity()
    data = request.get_json()
    allowed = ['fullName', 'professionalTitle', 'shortIntro', 'careerObjective',
               'about', 'interests', 'futureGoals', 'contact']
    update_fields = {k: data[k] for k in allowed if k in data}
    if update_fields:
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': update_fields}
        )
    return jsonify({'message': 'Portfolio updated'}), 200

# ---------- Education ----------
@app.route('/api/portfolio/education', methods=['POST'])
@jwt_required()
def add_education():
    user_id = get_jwt_identity()
    data = request.get_json()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    edu_list = portfolio.get('education', [])
    edu_list.append(data)
    mongo.db.portfolios.update_one(
        {'user_id': ObjectId(user_id)},
        {'$set': {'education': edu_list}}
    )
    return jsonify({'message': 'Education added'}), 201

@app.route('/api/portfolio/education/<int:index>', methods=['PUT', 'DELETE'])
@jwt_required()
def modify_education(index):
    user_id = get_jwt_identity()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    edu_list = portfolio.get('education', [])
    if index < 0 or index >= len(edu_list):
        return jsonify({'message': 'Index out of range'}), 400
    if request.method == 'PUT':
        data = request.get_json()
        edu_list[index] = data
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': {'education': edu_list}}
        )
        return jsonify({'message': 'Education updated'}), 200
    else:  # DELETE
        del edu_list[index]
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': {'education': edu_list}}
        )
        return jsonify({'message': 'Education deleted'}), 200

# ---------- Skills ----------
@app.route('/api/portfolio/skills', methods=['PUT'])
@jwt_required()
def update_skills():
    user_id = get_jwt_identity()
    data = request.get_json()
    mongo.db.portfolios.update_one(
        {'user_id': ObjectId(user_id)},
        {'$set': {'skills': data}}
    )
    return jsonify({'message': 'Skills updated'}), 200

# ---------- Projects ----------
@app.route('/api/portfolio/projects', methods=['POST'])
@jwt_required()
def add_project():
    user_id = get_jwt_identity()
    data = request.get_json()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    projects = portfolio.get('projects', [])
    projects.append(data)
    mongo.db.portfolios.update_one(
        {'user_id': ObjectId(user_id)},
        {'$set': {'projects': projects}}
    )
    return jsonify({'message': 'Project added'}), 201

@app.route('/api/portfolio/projects/<int:index>', methods=['PUT', 'DELETE'])
@jwt_required()
def modify_project(index):
    user_id = get_jwt_identity()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    projects = portfolio.get('projects', [])
    if index < 0 or index >= len(projects):
        return jsonify({'message': 'Index out of range'}), 400
    if request.method == 'PUT':
        data = request.get_json()
        projects[index] = data
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': {'projects': projects}}
        )
        return jsonify({'message': 'Project updated'}), 200
    else:
        del projects[index]
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': {'projects': projects}}
        )
        return jsonify({'message': 'Project deleted'}), 200

# ---------- Certificates ----------
@app.route('/api/portfolio/certificates', methods=['POST'])
@jwt_required()
def add_certificate():
    user_id = get_jwt_identity()
    data = request.get_json()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    certs = portfolio.get('certificates', [])
    certs.append(data)
    mongo.db.portfolios.update_one(
        {'user_id': ObjectId(user_id)},
        {'$set': {'certificates': certs}}
    )
    return jsonify({'message': 'Certificate added'}), 201

@app.route('/api/portfolio/certificates/<int:index>', methods=['PUT', 'DELETE'])
@jwt_required()
def modify_certificate(index):
    user_id = get_jwt_identity()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    certs = portfolio.get('certificates', [])
    if index < 0 or index >= len(certs):
        return jsonify({'message': 'Index out of range'}), 400
    if request.method == 'PUT':
        data = request.get_json()
        certs[index] = data
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': {'certificates': certs}}
        )
        return jsonify({'message': 'Certificate updated'}), 200
    else:
        del certs[index]
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': {'certificates': certs}}
        )
        return jsonify({'message': 'Certificate deleted'}), 200

# ---------- Achievements ----------
@app.route('/api/portfolio/achievements', methods=['POST'])
@jwt_required()
def add_achievement():
    user_id = get_jwt_identity()
    data = request.get_json()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    achievements = portfolio.get('achievements', [])
    achievements.append(data)
    mongo.db.portfolios.update_one(
        {'user_id': ObjectId(user_id)},
        {'$set': {'achievements': achievements}}
    )
    return jsonify({'message': 'Achievement added'}), 201

@app.route('/api/portfolio/achievements/<int:index>', methods=['PUT', 'DELETE'])
@jwt_required()
def modify_achievement(index):
    user_id = get_jwt_identity()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    achievements = portfolio.get('achievements', [])
    if index < 0 or index >= len(achievements):
        return jsonify({'message': 'Index out of range'}), 400
    if request.method == 'PUT':
        data = request.get_json()
        achievements[index] = data
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': {'achievements': achievements}}
        )
        return jsonify({'message': 'Achievement updated'}), 200
    else:
        del achievements[index]
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': {'achievements': achievements}}
        )
        return jsonify({'message': 'Achievement deleted'}), 200

# ---------- Experiences ----------
@app.route('/api/portfolio/experiences', methods=['POST'])
@jwt_required()
def add_experience():
    user_id = get_jwt_identity()
    data = request.get_json()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    experiences = portfolio.get('experiences', [])
    experiences.append(data)
    mongo.db.portfolios.update_one(
        {'user_id': ObjectId(user_id)},
        {'$set': {'experiences': experiences}}
    )
    return jsonify({'message': 'Experience added'}), 201

@app.route('/api/portfolio/experiences/<int:index>', methods=['PUT', 'DELETE'])
@jwt_required()
def modify_experience(index):
    user_id = get_jwt_identity()
    portfolio = mongo.db.portfolios.find_one({'user_id': ObjectId(user_id)})
    experiences = portfolio.get('experiences', [])
    if index < 0 or index >= len(experiences):
        return jsonify({'message': 'Index out of range'}), 400
    if request.method == 'PUT':
        data = request.get_json()
        experiences[index] = data
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': {'experiences': experiences}}
        )
        return jsonify({'message': 'Experience updated'}), 200
    else:
        del experiences[index]
        mongo.db.portfolios.update_one(
            {'user_id': ObjectId(user_id)},
            {'$set': {'experiences': experiences}}
        )
        return jsonify({'message': 'Experience deleted'}), 200

# ---------- FILE UPLOADS ----------
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload/profile-image', methods=['POST'])
@jwt_required()
def upload_profile_image():
    user_id = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'message': 'Invalid file'}), 400

    result = cloudinary.uploader.upload(file, folder='student_portfolio/profile')
    url = result.get('secure_url')
    mongo.db.portfolios.update_one(
        {'user_id': ObjectId(user_id)},
        {'$set': {'profileImage': url}}
    )
    return jsonify({'url': url}), 200

@app.route('/api/upload/resume', methods=['POST'])
@jwt_required()
def upload_resume():
    user_id = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'message': 'Invalid file'}), 400

    result = cloudinary.uploader.upload(file, folder='student_portfolio/resume', resource_type='auto')
    url = result.get('secure_url')
    mongo.db.portfolios.update_one(
        {'user_id': ObjectId(user_id)},
        {'$set': {'resume': url}}
    )
    return jsonify({'url': url}), 200

# ---------- HEALTH CHECK ----------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

# ---------- SERVE FRONTEND HTML ----------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Virat – Student Portfolio Hub</title>

    <!-- Bootstrap 5 + Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" />
    <!-- Font Awesome 6 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" />
    <!-- Google Fonts (Inter) -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,600;14..32,700;14..32,800&display=swap" rel="stylesheet" />
    <!-- AOS Animation -->
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet" />

    <style>
        /* ============================================================
                   ROOT VARIABLES
                   ============================================================ */
        :root {
            --primary: #0b9aff;
            --primary-dark: #0077e6;
            --primary-light: #6bc5ff;
            --primary-glow: rgba(11, 154, 255, 0.35);
            --sky-start: #e8f4ff;
            --sky-end: #b8dfff;
            --bg-light: #f8fcff;
            --bg-dark: #0c1220;
            --card-light: rgba(255, 255, 255, 0.75);
            --card-dark: rgba(18, 30, 50, 0.85);
            --text-light: #0f1a2e;
            --text-dark: #e8f0f8;
            --shadow-light: 0 20px 50px rgba(11, 154, 255, 0.10);
            --shadow-dark: 0 20px 50px rgba(0, 0, 0, 0.50);
            --border-light: rgba(11, 154, 255, 0.15);
            --border-dark: rgba(11, 154, 255, 0.20);
            --radius: 24px;
            --transition: 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }

        /* ============================================================
                   BASE
                   ============================================================ */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-light);
            color: var(--text-light);
            transition: background var(--transition), color var(--transition);
            overflow-x: hidden;
            line-height: 1.7;
        }

        body.dark-mode {
            background: var(--bg-dark);
            color: var(--text-dark);
        }

        /* scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-light);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 10px;
        }
        .dark-mode ::-webkit-scrollbar-track {
            background: var(--bg-dark);
        }

        a {
            color: var(--primary);
            text-decoration: none;
            transition: color 0.3s;
        }
        a:hover {
            color: var(--primary-dark);
        }

        /* ============================================================
                   GLASS & CARDS
                   ============================================================ */
        .glass {
            background: var(--card-light);
            backdrop-filter: blur(16px) saturate(180%);
            -webkit-backdrop-filter: blur(16px) saturate(180%);
            border: 1px solid var(--border-light);
            border-radius: var(--radius);
            box-shadow: var(--shadow-light);
            transition: background var(--transition), border var(--transition), box-shadow var(--transition);
        }

        .dark-mode .glass {
            background: var(--card-dark);
            border-color: var(--border-dark);
            box-shadow: var(--shadow-dark);
        }

        .glass-dark {
            background: rgba(11, 154, 255, 0.06);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(11, 154, 255, 0.12);
            border-radius: var(--radius);
        }

        .dark-mode .glass-dark {
            background: rgba(11, 154, 255, 0.08);
            border-color: rgba(11, 154, 255, 0.15);
        }

        /* ============================================================
                   NAVBAR
                   ============================================================ */
        .navbar-custom {
            background: rgba(255, 255, 255, 0.78);
            backdrop-filter: blur(18px) saturate(180%);
            -webkit-backdrop-filter: blur(18px) saturate(180%);
            border-bottom: 1px solid rgba(11, 154, 255, 0.08);
            transition: background var(--transition), border var(--transition);
            padding: 12px 0;
        }

        .dark-mode .navbar-custom {
            background: rgba(12, 18, 32, 0.85);
            border-bottom: 1px solid rgba(11, 154, 255, 0.10);
        }

        .navbar-brand {
            font-weight: 800;
            font-size: 1.5rem;
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.5px;
        }
        .navbar-brand i {
            -webkit-text-fill-color: var(--primary);
            margin-right: 6px;
        }

        .nav-link {
            font-weight: 600;
            font-size: 0.9rem;
            color: var(--text-light) !important;
            padding: 6px 14px !important;
            border-radius: 50px;
            transition: all 0.3s;
            position: relative;
        }
        .dark-mode .nav-link {
            color: var(--text-dark) !important;
        }
        .nav-link:hover {
            background: rgba(11, 154, 255, 0.08);
            color: var(--primary) !important;
        }
        .dark-mode .nav-link:hover {
            background: rgba(11, 154, 255, 0.12);
        }

        .theme-toggle-btn {
            background: none;
            border: none;
            font-size: 1.3rem;
            color: var(--text-light);
            padding: 6px 10px;
            border-radius: 50%;
            transition: all 0.3s;
            cursor: pointer;
        }
        .dark-mode .theme-toggle-btn {
            color: var(--text-dark);
        }
        .theme-toggle-btn:hover {
            background: rgba(11, 154, 255, 0.12);
            transform: rotate(15deg);
        }

        /* ============================================================
                   HERO
                   ============================================================ */
        .hero-section {
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 120px 0 80px;
            position: relative;
            overflow: hidden;
        }

        /* animated gradient orbs */
        .hero-orbs {
            position: absolute;
            inset: 0;
            pointer-events: none;
            z-index: 0;
        }
        .hero-orbs span {
            position: absolute;
            border-radius: 50%;
            filter: blur(90px);
            opacity: 0.30;
            animation: floatOrb 12s ease-in-out infinite alternate;
        }
        .hero-orbs span:nth-child(1) {
            width: 400px;
            height: 400px;
            background: var(--primary);
            top: -10%;
            right: -5%;
            animation-delay: 0s;
        }
        .hero-orbs span:nth-child(2) {
            width: 300px;
            height: 300px;
            background: var(--primary-light);
            bottom: -10%;
            left: -5%;
            animation-delay: 4s;
            opacity: 0.20;
        }
        .dark-mode .hero-orbs span {
            opacity: 0.18;
        }

        @keyframes floatOrb {
            0% {
                transform: translate(0, 0) scale(1);
            }
            100% {
                transform: translate(40px, -30px) scale(1.2);
            }
        }

        .hero-content {
            position: relative;
            z-index: 1;
        }

        .hero-badge {
            display: inline-block;
            background: rgba(11, 154, 255, 0.10);
            color: var(--primary);
            padding: 6px 20px;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            border: 1px solid rgba(11, 154, 255, 0.12);
            margin-bottom: 20px;
        }
        .dark-mode .hero-badge {
            background: rgba(11, 154, 255, 0.15);
        }

        .hero-name {
            font-size: 3.6rem;
            font-weight: 800;
            line-height: 1.1;
            letter-spacing: -1px;
        }
        .hero-name span {
            background: linear-gradient(135deg, var(--primary), #4facfe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-title {
            font-size: 1.4rem;
            font-weight: 400;
            color: var(--text-light);
            opacity: 0.8;
            margin-top: 8px;
        }
        .dark-mode .hero-title {
            color: var(--text-dark);
        }

        .hero-typed {
            font-weight: 600;
            color: var(--primary);
        }

        .hero-desc {
            font-size: 1.1rem;
            max-width: 540px;
            opacity: 0.85;
            margin: 20px 0 28px;
        }

        .hero-avatar {
            width: 280px;
            height: 280px;
            border-radius: 50%;
            object-fit: cover;
            border: 5px solid rgba(11, 154, 255, 0.25);
            box-shadow: 0 30px 60px rgba(11, 154, 255, 0.20);
            transition: all 0.5s;
            background: linear-gradient(135deg, var(--primary-light), var(--primary));
            padding: 5px;
        }
        .hero-avatar:hover {
            transform: scale(1.02) rotate(-2deg);
            box-shadow: 0 40px 80px rgba(11, 154, 255, 0.30);
        }
        .dark-mode .hero-avatar {
            border-color: rgba(11, 154, 255, 0.35);
        }

        /* ============================================================
                   SECTION TITLES
                   ============================================================ */
        .section-title {
            font-size: 2.4rem;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 12px;
            position: relative;
            display: inline-block;
        }
        .section-title::after {
            content: '';
            position: absolute;
            bottom: -6px;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--primary-light));
            border-radius: 10px;
        }
        .section-sub {
            color: var(--text-light);
            opacity: 0.6;
            font-size: 1rem;
        }
        .dark-mode .section-sub {
            color: var(--text-dark);
        }

        /* ============================================================
                   TIMELINE (Education / Experience)
                   ============================================================ */
        .timeline-item {
            position: relative;
            padding-left: 28px;
            padding-bottom: 28px;
            border-left: 3px solid var(--primary);
            margin-left: 6px;
        }
        .timeline-item:last-child {
            border-left: 3px solid transparent;
            padding-bottom: 0;
        }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -9px;
            top: 6px;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--primary);
            border: 3px solid var(--bg-light);
            box-shadow: 0 0 0 4px rgba(11, 154, 255, 0.20);
            transition: background var(--transition), border var(--transition);
        }
        .dark-mode .timeline-item::before {
            border-color: var(--bg-dark);
        }
        .timeline-item .badge-soft {
            background: rgba(11, 154, 255, 0.10);
            color: var(--primary);
            padding: 2px 14px;
            border-radius: 50px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .dark-mode .timeline-item .badge-soft {
            background: rgba(11, 154, 255, 0.15);
        }

        /* ============================================================
                   SKILLS
                   ============================================================ */
        .skill-tag {
            display: inline-block;
            padding: 8px 18px;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 500;
            background: rgba(11, 154, 255, 0.06);
            border: 1px solid rgba(11, 154, 255, 0.08);
            transition: all 0.3s;
            margin: 4px;
        }
        .skill-tag:hover {
            background: rgba(11, 154, 255, 0.12);
            transform: translateY(-2px);
            border-color: var(--primary);
        }
        .dark-mode .skill-tag {
            background: rgba(11, 154, 255, 0.10);
            border-color: rgba(11, 154, 255, 0.12);
        }
        .dark-mode .skill-tag:hover {
            background: rgba(11, 154, 255, 0.20);
        }

        .skill-tag-sm {
            padding: 4px 12px;
            font-size: 0.75rem;
        }

        .progress-skill {
            margin-bottom: 14px;
        }
        .progress-skill .label {
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 3px;
        }
        .progress-skill .bar {
            height: 6px;
            background: rgba(11, 154, 255, 0.10);
            border-radius: 10px;
            overflow: hidden;
        }
        .progress-skill .bar .fill {
            height: 100%;
            border-radius: 10px;
            background: linear-gradient(90deg, var(--primary), var(--primary-light));
            width: 0%;
            transition: width 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }

        /* ============================================================
                   PROJECT CARDS
                   ============================================================ */
        .project-card {
            border-radius: var(--radius);
            overflow: hidden;
            transition: all 0.4s;
            height: 100%;
            background: var(--card-light);
            border: 1px solid var(--border-light);
            box-shadow: var(--shadow-light);
            backdrop-filter: blur(8px);
        }
        .dark-mode .project-card {
            background: var(--card-dark);
            border-color: var(--border-dark);
            box-shadow: var(--shadow-dark);
        }
        .project-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 30px 60px rgba(11, 154, 255, 0.12);
            border-color: var(--primary);
        }
        .dark-mode .project-card:hover {
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.60);
        }
        .project-card .card-img-top {
            height: 200px;
            object-fit: cover;
            background: linear-gradient(135deg, var(--primary-light), var(--primary));
        }
        .project-card .tech-badge {
            font-size: 0.7rem;
            background: rgba(11, 154, 255, 0.08);
            padding: 3px 12px;
            border-radius: 50px;
            margin: 2px;
            display: inline-block;
        }
        .dark-mode .project-card .tech-badge {
            background: rgba(11, 154, 255, 0.12);
        }

        /* ============================================================
                   CERTIFICATE CARDS
                   ============================================================ */
        .cert-card {
            border-radius: var(--radius);
            overflow: hidden;
            transition: all 0.4s;
            height: 100%;
            background: var(--card-light);
            border: 1px solid var(--border-light);
            box-shadow: var(--shadow-light);
            backdrop-filter: blur(8px);
        }
        .dark-mode .cert-card {
            background: var(--card-dark);
            border-color: var(--border-dark);
            box-shadow: var(--shadow-dark);
        }
        .cert-card:hover {
            transform: scale(1.02);
            border-color: var(--primary);
        }
        .cert-card .cert-img {
            height: 150px;
            object-fit: cover;
            background: rgba(11, 154, 255, 0.05);
        }

        /* ============================================================
                   CONTACT
                   ============================================================ */
        .contact-icon-box {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 14px 18px;
            border-radius: 16px;
            background: rgba(11, 154, 255, 0.04);
            border: 1px solid rgba(11, 154, 255, 0.06);
            transition: all 0.3s;
        }
        .contact-icon-box:hover {
            background: rgba(11, 154, 255, 0.08);
            border-color: var(--primary);
        }
        .dark-mode .contact-icon-box {
            background: rgba(11, 154, 255, 0.06);
        }
        .contact-icon-box .icon {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: var(--primary);
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            flex-shrink: 0;
        }

        /* ============================================================
                   FOOTER
                   ============================================================ */
        .footer-custom {
            background: rgba(11, 154, 255, 0.02);
            border-top: 1px solid rgba(11, 154, 255, 0.06);
            padding: 40px 0 24px;
            margin-top: 60px;
            transition: background var(--transition), border var(--transition);
        }
        .dark-mode .footer-custom {
            background: rgba(11, 154, 255, 0.03);
            border-color: rgba(11, 154, 255, 0.06);
        }
        .footer-custom .heart {
            color: #ff4d6d;
        }

        /* ============================================================
                   RESPONSIVE
                   ============================================================ */
        @media (max-width: 992px) {
            .hero-name {
                font-size: 2.8rem;
            }
            .hero-avatar {
                width: 220px;
                height: 220px;
            }
        }
        @media (max-width: 768px) {
            .hero-name {
                font-size: 2.2rem;
            }
            .hero-title {
                font-size: 1.1rem;
            }
            .hero-avatar {
                width: 180px;
                height: 180px;
            }
            .section-title {
                font-size: 1.8rem;
            }
            .navbar-brand {
                font-size: 1.2rem;
            }
            .hero-section {
                padding: 100px 0 50px;
            }
        }
        @media (max-width: 576px) {
            .hero-name {
                font-size: 1.8rem;
            }
            .hero-avatar {
                width: 150px;
                height: 150px;
            }
        }

        /* ============================================================
                   UTILITY
                   ============================================================ */
        .text-gradient {
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .bg-soft-primary {
            background: rgba(11, 154, 255, 0.04);
        }
        .dark-mode .bg-soft-primary {
            background: rgba(11, 154, 255, 0.06);
        }
        .gap-2 {
            gap: 0.5rem;
        }
        .gap-3 {
            gap: 1rem;
        }

        /* floating animation for cards */
        .float-up {
            animation: floatUp 6s ease-in-out infinite;
        }
        @keyframes floatUp {
            0%,
            100% {
                transform: translateY(0px);
            }
            50% {
                transform: translateY(-8px);
            }
        }

        /* typing cursor blink */
        .cursor-blink {
            animation: blink 0.9s step-end infinite;
        }
        @keyframes blink {
            0%,
            100% {
                opacity: 1;
            }
            50% {
                opacity: 0;
            }
        }

        /* small extra styling */
        .edu-gpa-box {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 8px;
        }
        .edu-gpa-box .gpa-item {
            background: rgba(11, 154, 255, 0.06);
            padding: 2px 16px;
            border-radius: 50px;
            font-size: 0.85rem;
            border: 1px solid rgba(11, 154, 255, 0.08);
        }
        .dark-mode .edu-gpa-box .gpa-item {
            background: rgba(11, 154, 255, 0.10);
            border-color: rgba(11, 154, 255, 0.12);
        }
        .edu-gpa-box .gpa-item strong {
            color: var(--primary);
        }

        /* Modal overrides for dark mode */
        .modal-content {
            background: var(--bg-light);
            color: var(--text-light);
            border: none;
            border-radius: var(--radius);
            box-shadow: var(--shadow-light);
        }
        .dark-mode .modal-content {
            background: var(--bg-dark);
            color: var(--text-dark);
            box-shadow: var(--shadow-dark);
        }
        .modal-header {
            border-bottom-color: var(--border-light);
        }
        .dark-mode .modal-header {
            border-bottom-color: var(--border-dark);
        }
        .modal-footer {
            border-top-color: var(--border-light);
        }
        .dark-mode .modal-footer {
            border-top-color: var(--border-dark);
        }
        .btn-close {
            filter: none;
        }
        .dark-mode .btn-close {
            filter: invert(1);
        }
        .form-control {
            background: rgba(255,255,255,0.6);
            border: 1px solid var(--border-light);
            color: var(--text-light);
        }
        .dark-mode .form-control {
            background: rgba(30,41,59,0.6);
            border-color: var(--border-dark);
            color: var(--text-dark);
        }
        .form-control:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(11,154,255,0.2);
        }
        .dark-mode .form-control:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(11,154,255,0.3);
        }
        .nav-tabs .nav-link {
            color: var(--text-light);
        }
        .dark-mode .nav-tabs .nav-link {
            color: var(--text-dark);
        }
        .nav-tabs .nav-link.active {
            color: var(--primary);
            background: transparent;
            border-bottom-color: var(--primary);
        }
        .dark-mode .nav-tabs .nav-link.active {
            color: var(--primary-light);
        }
        .whatsapp-float {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
            background: #25d366;
            color: white;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            box-shadow: 0 10px 30px rgba(37, 211, 102, 0.4);
            transition: all 0.3s;
            text-decoration: none;
        }
        .whatsapp-float:hover {
            transform: scale(1.1);
            color: white;
            box-shadow: 0 15px 40px rgba(37, 211, 102, 0.5);
        }
        .dark-mode .whatsapp-float {
            box-shadow: 0 10px 30px rgba(37, 211, 102, 0.6);
        }
    </style>
</head>

<body>

    <!-- ============================================================
    NAVBAR
    ============================================================ -->
    <nav class="navbar navbar-expand-lg navbar-custom fixed-top">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="fas fa-graduation-cap"></i>StudentHub
            </a>
            <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu"
            aria-controls="navMenu" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navMenu">
            <ul class="navbar-nav ms-auto align-items-center">
                <li class="nav-item"><a class="nav-link" href="#about">About</a></li>
                <li class="nav-item"><a class="nav-link" href="#education">Education</a></li>
                <li class="nav-item"><a class="nav-link" href="#skills">Skills</a></li>
                <li class="nav-item"><a class="nav-link" href="#projects">Projects</a></li>
                <li class="nav-item"><a class="nav-link" href="#certificates">Certificates</a></li>
                <li class="nav-item"><a class="nav-link" href="#experience">Experience</a></li>
                <li class="nav-item"><a class="nav-link" href="#contact">Contact</a></li>
                <li class="nav-item">
                    <button class="btn btn-outline-primary btn-sm rounded-pill px-3 me-2" data-bs-toggle="modal" data-bs-target="#authModal">
                        <i class="fas fa-user me-1"></i>Login / Register
                    </button>
                </li>
                <li class="nav-item">
                    <button class="theme-toggle-btn" id="themeToggle" aria-label="Toggle dark mode">
                        <i class="fas fa-moon"></i>
                    </button>
                </li>
            </ul>
        </div>
    </div>
</nav>

<!-- ============================================================
AUTH MODAL (Login / Register)
============================================================ -->
<div class="modal fade" id="authModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header border-0 pb-0">
                <h5 class="modal-title fw-bold"><i class="fas fa-user-circle text-primary me-2"></i>Welcome</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <ul class="nav nav-tabs nav-fill mb-3" id="authTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="login-tab" data-bs-toggle="tab" data-bs-target="#login" type="button" role="tab">Login</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="register-tab" data-bs-toggle="tab" data-bs-target="#register" type="button" role="tab">Register</button>
                    </li>
                </ul>
                <div class="tab-content" id="authTabsContent">
                    <!-- Login Tab -->
                    <div class="tab-pane fade show active" id="login" role="tabpanel">
                        <form id="loginForm">
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" id="loginEmail" placeholder="you@example.com" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Password</label>
                                <input type="password" class="form-control" id="loginPassword" placeholder="••••••••" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100 rounded-pill">Login</button>
                            <div id="loginFeedback" class="mt-2 small"></div>
                        </form>
                    </div>
                    <!-- Register Tab -->
                    <div class="tab-pane fade" id="register" role="tabpanel">
                        <form id="registerForm">
                            <div class="mb-3">
                                <label class="form-label">Username</label>
                                <input type="text" class="form-control" id="regUsername" placeholder="Choose a username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" id="regEmail" placeholder="you@example.com" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Password</label>
                                <input type="password" class="form-control" id="regPassword" placeholder="Min 6 characters" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100 rounded-pill">Create Account</button>
                            <div id="registerFeedback" class="mt-2 small"></div>
                        </form>
                    </div>
                </div>
            </div>
            <div class="modal-footer border-0 pt-0">
                <small class="text-muted">By continuing you agree to our terms.</small>
            </div>
        </div>
    </div>
</div>

<!-- ============================================================
HERO
============================================================ -->
<section class="hero-section" id="home">
    <!-- animated orbs -->
    <div class="hero-orbs">
        <span></span>
        <span></span>
    </div>

    <div class="container hero-content">
        <div class="row align-items-center gy-5">
            <div class="col-lg-7 order-lg-1" data-aos="fade-right" data-aos-duration="800">
                <div class="hero-badge">
                    <i class="fas fa-rocket me-1"></i> Open to Opportunities
                </div>
                <h1 class="hero-name">
                    Hi, I'm <span>Virat</span>
                </h1>
                <h2 class="hero-title">
                    <span class="hero-typed" id="typedText">Full Stack Developer</span>
                    <span class="cursor-blink">|</span>
                </h2>
                <p class="hero-desc">
                    Passionate about building web applications that solve real-world problems.
                </p>
                <p class="hero-desc" style="font-size:0.95rem; opacity:0.7;">
                    <i class="fas fa-quote-left me-1 text-primary"></i>
                    To secure a challenging position in a reputable organization to expand my learnings, knowledge, and skills.
                </p>
                <div class="d-flex flex-wrap gap-3 mt-4">
                    <a href="#contact" class="btn btn-primary px-5 py-3 rounded-pill fw-semibold shadow-lg shadow-primary/20">
                        <i class="fas fa-paper-plane me-2"></i>Contact Me
                    </a>
                    <a href="#" class="btn btn-outline-primary px-5 py-3 rounded-pill fw-semibold" id="resumeBtn">
                        <i class="fas fa-file-pdf me-2"></i>Resume
                    </a>
                </div>
            </div>

            <div class="col-lg-5 order-lg-2 text-center" data-aos="fade-left" data-aos-duration="800" data-aos-delay="200">
                <img src="https://ui-avatars.com/api/?name=Virat&size=280&background=0b9aff&color=fff&bold=true&font-size=0.5"
                alt="Virat" class="hero-avatar" id="profileAvatar" />
                <div class="mt-3 d-flex justify-content-center gap-3">
                    <a href="#" class="text-primary fs-5"><i class="fab fa-linkedin"></i></a>
                    <a href="#" class="text-primary fs-5"><i class="fab fa-github"></i></a>
                    <a href="#" class="text-primary fs-5"><i class="fab fa-twitter"></i></a>
                    <a href="#" class="text-primary fs-5"><i class="fab fa-youtube"></i></a>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============================================================
ABOUT
============================================================ -->
<section id="about" class="py-5">
    <div class="container">
        <div class="text-center mb-5" data-aos="fade-up">
            <h2 class="section-title">About Me</h2>
            <p class="section-sub">Get to know me a little better</p>
        </div>

        <div class="row g-4" data-aos="fade-up" data-aos-delay="100">
            <div class="col-lg-8 mx-auto">
                <div class="glass p-4 p-md-5">
                    <p class="lead" style="font-weight: 400;">
                        I am a final-year Computer Science student with a strong interest in full-stack development.
                        I enjoy working with modern JavaScript frameworks and have experience in both frontend and backend technologies.
                    </p>
                    <hr class="my-4" style="border-color: var(--border-light);" />

                    <div class="row g-4">
                        <div class="col-md-6">
                            <h6 class="fw-bold"><i class="fas fa-heart text-primary me-2"></i>Interests</h6>
                            <div class="d-flex flex-wrap gap-2 mt-2">
                                <span class="skill-tag">Coding</span>
                                <span class="skill-tag">AI Development</span>
                                <span class="skill-tag">Cybersecurity</span>
                                <span class="skill-tag">Technology</span>
                                <span class="skill-tag">Travel</span>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6 class="fw-bold"><i class="fas fa-flag text-primary me-2"></i>Future Goals</h6>
                            <p class="mb-0" style="opacity:0.85;">
                                Become a lead developer, contribute to impactful open-source projects,
                                and grow in the fields of Fitness and Development.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============================================================
EDUCATION
============================================================ -->
<section id="education" class="py-5 bg-soft-primary">
    <div class="container">
        <div class="text-center mb-5" data-aos="fade-up">
            <h2 class="section-title">Education</h2>
            <p class="section-sub">My academic journey</p>
        </div>

        <div class="row justify-content-center" data-aos="fade-up" data-aos-delay="100">
            <div class="col-lg-8">
                <div class="glass p-4 p-md-5">

                    <!-- MCA -->
                    <div class="timeline-item">
                        <h5 class="fw-bold">SGU University</h5>
                        <p class="mb-1"><strong>Master of Computer Application (MCA)</strong></p>
                        <p class="mb-1" style="opacity:0.75;">Computer Science – Web Development & Software Engineering</p>
                        <div class="edu-gpa-box">
                            <span class="gpa-item"><strong>CGPA:</strong> 8.87</span>
                        </div>
                        <div class="mt-3 d-flex flex-wrap gap-2">
                            <span class="skill-tag skill-tag-sm">Data Structures</span>
                            <span class="skill-tag skill-tag-sm">Algorithms</span>
                            <span class="skill-tag skill-tag-sm">Web Development</span>
                            <span class="skill-tag skill-tag-sm">Database Systems</span>
                            <span class="skill-tag skill-tag-sm">Software Engineering</span>
                        </div>
                    </div>

                    <!-- BCA -->
                    <div class="timeline-item" style="border-left-color: var(--primary-light);">
                        <h5 class="fw-bold">SGU University</h5>
                        <p class="mb-1"><strong>Bachelor of Computer Applications (BCA)</strong></p>
                        <p class="mb-1" style="opacity:0.75;">Computer Applications – Programming & IT Fundamentals</p>
                        <div class="edu-gpa-box">
                            <span class="gpa-item"><strong>CGPA:</strong> 8.99</span>
                            <span class="gpa-item"><strong>SGCP:</strong> 9.88</span>
                        </div>
                        <div class="mt-3 d-flex flex-wrap gap-2">
                            <span class="skill-tag skill-tag-sm">Programming Fundamentals</span>
                            <span class="skill-tag skill-tag-sm">Database Management</span>
                            <span class="skill-tag skill-tag-sm">Networking</span>
                            <span class="skill-tag skill-tag-sm">Web Technologies</span>
                            <span class="skill-tag skill-tag-sm">Software Engineering</span>
                            <span class="skill-tag skill-tag-sm">Operating Systems</span>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============================================================
SKILLS (full page section)
============================================================ -->
<section id="skills" class="py-5">
    <div class="container">
        <div class="text-center mb-5" data-aos="fade-up">
            <h2 class="section-title">Skills</h2>
            <p class="section-sub">Technologies & tools I work with</p>
        </div>

        <div class="row g-4" data-aos="fade-up" data-aos-delay="100">

            <!-- ===== Frontend ===== -->
            <div class="col-md-4">
                <div class="glass p-4 h-100">
                    <h5 class="fw-bold mb-3"><i class="fas fa-laptop-code text-primary me-2"></i>Frontend</h5>
                    <div class="progress-skill">
                        <div class="label"><span>HTML / CSS</span><span>90%</span></div>
                        <div class="bar"><div class="fill" style="width:90%;"></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>JavaScript</span><span>85%</span></div>
                        <div class="bar"><div class="fill" style="width:85%;"></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>React / Next.js</span><span>80%</span></div>
                        <div class="bar"><div class="fill" style="width:80%;"></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>Bootstrap / jQuery</span><span>78%</span></div>
                        <div class="bar"><div class="fill" style="width:78%;"></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>Tailwind CSS</span><span>75%</span></div>
                        <div class="bar"><div class="fill" style="width:75%;"></div></div>
                    </div>
                </div>
            </div>

            <!-- ===== Backend ===== -->
            <div class="col-md-4">
                <div class="glass p-4 h-100">
                    <h5 class="fw-bold mb-3"><i class="fas fa-server text-primary me-2"></i>Backend</h5>
                    <div class="progress-skill">
                        <div class="label"><span>Node.js / Express</span><span>75%</span></div>
                        <div class="bar"><div class="fill" style="width:75%;"></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>Python (Basic → Advanced)</span><span>70%</span></div>
                        <div class="bar"><div class="fill" style="width:70%;"></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>Java (Core + DSA)</span><span>68%</span></div>
                        <div class="bar"><div class="fill" style="width:68%;"></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>C / C++</span><span>65%</span></div>
                        <div class="bar"><div class="fill" style="width:65%;"></div></div>
                    </div>
                    <div class="progress-skill">
                        <div class="label"><span>MongoDB / SQL</span><span>70%</span></div>
                        <div class="bar"><div class="fill" style="width:70%;"></div></div>
                    </div>
                </div>
            </div>

            <!-- ===== APIs & Tools ===== -->
            <div class="col-md-4">
                <div class="glass p-4 h-100">
                    <h5 class="fw-bold mb-3"><i class="fas fa-plug text-primary me-2"></i>APIs &amp; Tools</h5>
                    <div class="d-flex flex-wrap gap-2 mb-3">
                        <span class="skill-tag">REST APIs</span>
                        <span class="skill-tag">Postman</span>
                        <span class="skill-tag">GraphQL</span>
                        <span class="skill-tag">WebSockets</span>
                        <span class="skill-tag">OAuth 2.0</span>
                    </div>
                    <h6 class="fw-bold mt-3 mb-2"><i class="fas fa-tools text-primary me-2"></i>Dev Tools</h6>
                    <div class="d-flex flex-wrap gap-2">
                        <span class="skill-tag">Git / GitHub</span>
                        <span class="skill-tag">VS Code</span>
                        <span class="skill-tag">Docker</span>
                        <span class="skill-tag">AWS</span>
                        <span class="skill-tag">Linux</span>
                        <span class="skill-tag">Figma</span>
                    </div>
                    <h6 class="fw-bold mt-3 mb-2"><i class="fas fa-file-alt text-primary me-2"></i>Microsoft Office</h6>
                    <div class="d-flex flex-wrap gap-2">
                        <span class="skill-tag skill-tag-sm">Word</span>
                        <span class="skill-tag skill-tag-sm">Excel</span>
                        <span class="skill-tag skill-tag-sm">PowerPoint</span>
                        <span class="skill-tag skill-tag-sm">Outlook</span>
                    </div>
                </div>
            </div>

        </div>

        <!-- Soft Skills row (full width) -->
        <div class="row mt-4" data-aos="fade-up" data-aos-delay="150">
            <div class="col-12">
                <div class="glass p-4">
                    <h5 class="fw-bold mb-3"><i class="fas fa-users text-primary me-2"></i>Soft Skills</h5>
                    <div class="d-flex flex-wrap gap-2">
                        <span class="skill-tag">Communication</span>
                        <span class="skill-tag">Teamwork</span>
                        <span class="skill-tag">Leadership</span>
                        <span class="skill-tag">Critical Thinking</span>
                        <span class="skill-tag">Problem Solving</span>
                        <span class="skill-tag">Time Management</span>
                        <span class="skill-tag">Adaptability</span>
                        <span class="skill-tag">Collaboration</span>
                        <span class="skill-tag">Public Speaking</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============================================================
PROJECTS
============================================================ -->
<section id="projects" class="py-5 bg-soft-primary">
    <div class="container">
        <div class="text-center mb-5" data-aos="fade-up">
            <h2 class="section-title">Projects</h2>
            <p class="section-sub">Some of my recent work</p>
        </div>

        <div class="row g-4" data-aos="fade-up" data-aos-delay="100">
            <div class="col-lg-8 mx-auto">
                <div class="project-card p-0">
                    <div class="card-img-top d-flex align-items-center justify-content-center" style="background: linear-gradient(135deg, #0b9aff, #4facfe); color: #fff; font-size: 2.5rem;">
                        <i class="fas fa-shield-alt me-3"></i> AI Phishing Detection
                    </div>
                    <div class="p-4">
                        <h4 class="fw-bold">AI based Phishing Detection Tool</h4>
                        <p class="mb-2" style="opacity:0.85;">
                            Developed an AI-based system to detect phishing websites/emails using machine learning algorithms.
                            Trained and tested the model on phishing datasets to identify malicious URLs and suspicious patterns.
                        </p>
                        <ul style="opacity:0.8; padding-left:20px;">
                            <li>Implemented feature extraction techniques such as URL analysis, domain checking, and keyword detection.</li>
                            <li>Built a user-friendly interface for real-time phishing prediction and alert generation.</li>
                            <li>Improved detection accuracy by applying data preprocessing and model optimization techniques.</li>
                        </ul>
                        <div class="d-flex flex-wrap gap-2 mt-3">
                            <span class="tech-badge">Python</span>
                            <span class="tech-badge">Machine Learning</span>
                            <span class="tech-badge">Scikit-learn</span>
                            <span class="tech-badge">TensorFlow</span>
                            <span class="tech-badge">Flask</span>
                            <span class="tech-badge">Pandas</span>
                            <span class="tech-badge">HTML/CSS</span>
                        </div>
                        <div class="mt-3 d-flex gap-3">
                            <a href="#" class="btn btn-sm btn-outline-primary"><i class="fab fa-github me-1"></i>Code</a>
                            <a href="#" class="btn btn-sm btn-primary"><i class="fas fa-external-link-alt me-1"></i>Live Demo</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- small extra project placeholder -->
        <div class="row g-4 mt-2" data-aos="fade-up" data-aos-delay="200">
            <div class="col-md-6">
                <div class="project-card p-3 text-center" style="border-style: dashed;">
                    <i class="fas fa-plus-circle text-primary fs-1 mb-2" style="opacity:0.3;"></i>
                    <p class="mb-0" style="opacity:0.5;">More projects coming soon…</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="project-card p-3 text-center" style="border-style: dashed;">
                    <i class="fas fa-plus-circle text-primary fs-1 mb-2" style="opacity:0.3;"></i>
                    <p class="mb-0" style="opacity:0.5;">Stay tuned for updates</p>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============================================================
CERTIFICATES
============================================================ -->
<section id="certificates" class="py-5">
    <div class="container">
        <div class="text-center mb-5" data-aos="fade-up">
            <h2 class="section-title">Certificates</h2>
            <p class="section-sub">Credentials & achievements</p>
        </div>

        <div class="row g-4" data-aos="fade-up" data-aos-delay="100">
            <div class="col-md-4">
                <div class="cert-card p-3 text-center">
                    <div class="cert-img d-flex align-items-center justify-content-center" style="background: rgba(11,154,255,0.06);">
                        <i class="fas fa-certificate text-primary" style="font-size:3rem; opacity:0.3;"></i>
                    </div>
                    <h6 class="mt-3 fw-bold">Full Stack Web Development</h6>
                    <p class="mb-0 small" style="opacity:0.7;">Coursera · Jan 2023</p>
                    <p class="small" style="opacity:0.5;">ID: XYZ123</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="cert-card p-3 text-center">
                    <div class="cert-img d-flex align-items-center justify-content-center" style="background: rgba(11,154,255,0.06);">
                        <i class="fas fa-certificate text-primary" style="font-size:3rem; opacity:0.3;"></i>
                    </div>
                    <h6 class="mt-3 fw-bold">JavaScript Algorithms</h6>
                    <p class="mb-0 small" style="opacity:0.7;">freeCodeCamp · Jun 2022</p>
                    <p class="small" style="opacity:0.5;">ID: ABC456</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="cert-card p-3 text-center">
                    <div class="cert-img d-flex align-items-center justify-content-center" style="background: rgba(11,154,255,0.06);">
                        <i class="fas fa-certificate text-primary" style="font-size:3rem; opacity:0.3;"></i>
                    </div>
                    <h6 class="mt-3 fw-bold">Machine Learning Specialization</h6>
                    <p class="mb-0 small" style="opacity:0.7;">Stanford · Dec 2023</p>
                    <p class="small" style="opacity:0.5;">ID: ML789</p>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============================================================
EXPERIENCE
============================================================ -->
<section id="experience" class="py-5 bg-soft-primary">
    <div class="container">
        <div class="text-center mb-5" data-aos="fade-up">
            <h2 class="section-title">Experience</h2>
            <p class="section-sub">Where I've worked & learned</p>
        </div>

        <div class="row justify-content-center" data-aos="fade-up" data-aos-delay="100">
            <div class="col-lg-8">
                <div class="glass p-4 p-md-5">
                    <div class="timeline-item">
                        <h5 class="fw-bold">Full Stack Developer Intern</h5>
                        <p class="mb-1"><strong>TechVibe Solutions</strong> <span class="badge-soft ms-2">Internship</span></p>
                        <p class="mb-2" style="opacity:0.7;">Jun 2024 – Present</p>
                        <ul style="opacity:0.85; padding-left:20px;">
                            <li>Developed and maintained full-stack web applications using React and Node.js.</li>
                            <li>Collaborated with cross-functional teams to deliver features on time.</li>
                            <li>Optimized application performance and implemented responsive designs.</li>
                        </ul>
                        <p><strong>Skills gained:</strong> React, Node.js, MongoDB, Agile</p>
                    </div>

                    <div class="timeline-item">
                        <h5 class="fw-bold">Freelance Web Developer</h5>
                        <p class="mb-1"><strong>Self-Employed</strong> <span class="badge-soft ms-2">Freelancing</span></p>
                        <p class="mb-2" style="opacity:0.7;">Jan 2023 – May 2024</p>
                        <ul style="opacity:0.85; padding-left:20px;">
                            <li>Built custom websites and web apps for small businesses and startups.</li>
                            <li>Provided maintenance, hosting, and SEO services.</li>
                            <li>Delivered 10+ projects with 95% client satisfaction.</li>
                        </ul>
                        <p><strong>Skills gained:</strong> HTML/CSS, JavaScript, WordPress, Client Communication</p>
                    </div>

                    <div class="timeline-item" style="border-left-color: transparent; padding-bottom:0;">
                        <h5 class="fw-bold">Campus Ambassador</h5>
                        <p class="mb-1"><strong>Google Developer Student Clubs</strong> <span class="badge-soft ms-2">Campus Activity</span></p>
                        <p class="mb-2" style="opacity:0.7;">Sep 2023 – Present</p>
                        <ul style="opacity:0.85; padding-left:20px;">
                            <li>Organized workshops and hackathons on campus.</li>
                            <li>Mentored students in web development and cloud technologies.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============================================================
RESUME
============================================================ -->
<section id="resume" class="py-5">
    <div class="container text-center" data-aos="fade-up">
        <h2 class="section-title">Resume</h2>
        <p class="section-sub mb-4">Download my resume to learn more about my background.</p>
        <a href="#" class="btn btn-primary btn-lg px-5 py-3 rounded-pill shadow-lg shadow-primary/20" id="resumeDownloadBtn">
            <i class="fas fa-file-pdf me-2"></i>Download PDF
        </a>
    </div>
</section>

<!-- ============================================================
CONTACT
============================================================ -->
<section id="contact" class="py-5 bg-soft-primary">
    <div class="container">
        <div class="text-center mb-5" data-aos="fade-up">
            <h2 class="section-title">Contact Me</h2>
            <p class="section-sub">Let's connect and build something amazing</p>
        </div>

        <div class="row g-4" data-aos="fade-up" data-aos-delay="100">
            <!-- Contact Info -->
            <div class="col-lg-5">
                <div class="glass p-4 p-md-5 h-100">
                    <h5 class="fw-bold mb-4"><i class="fas fa-address-card text-primary me-2"></i>Get in Touch</h5>

                    <div class="contact-icon-box mb-3">
                        <div class="icon"><i class="fas fa-envelope"></i></div>
                        <div>
                            <div class="small" style="opacity:0.5;">Email</div>
                            <a href="mailto:vs0371926@gmail.com" class="fw-semibold">vs0371926@gmail.com</a>
                        </div>
                    </div>

                    <div class="contact-icon-box mb-3">
                        <div class="icon"><i class="fas fa-phone"></i></div>
                        <div>
                            <div class="small" style="opacity:0.5;">Phone</div>
                            <a href="tel:+917310927827" class="fw-semibold">+91 7310927827</a>
                        </div>
                    </div>

                    <div class="contact-icon-box mb-3">
                        <div class="icon"><i class="fas fa-map-marker-alt"></i></div>
                        <div>
                            <div class="small" style="opacity:0.5;">Location</div>
                            <span class="fw-semibold">Mumbai, Maharashtra</span>
                        </div>
                    </div>

                    <div class="contact-icon-box">
                        <div class="icon"><i class="fas fa-globe"></i></div>
                        <div>
                            <div class="small" style="opacity:0.5;">Portfolio</div>
                            <a href="#" class="fw-semibold">studenthub.dev/virat</a>
                        </div>
                    </div>

                    <hr class="my-4" style="border-color: var(--border-light);" />
                    <div class="d-flex gap-3 fs-5">
                        <a href="#" class="text-primary"><i class="fab fa-linkedin"></i></a>
                        <a href="#" class="text-primary"><i class="fab fa-github"></i></a>
                        <a href="#" class="text-primary"><i class="fab fa-twitter"></i></a>
                        <a href="#" class="text-primary"><i class="fab fa-youtube"></i></a>
                        <a href="#" class="text-primary"><i class="fab fa-instagram"></i></a>
                    </div>
                </div>
            </div>

            <!-- Contact Form -->
            <div class="col-lg-7">
                <div class="glass p-4 p-md-5">
                    <h5 class="fw-bold mb-4"><i class="fas fa-paper-plane text-primary me-2"></i>Send a Message</h5>
                    <form id="contactForm">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Full Name</label>
                                <input type="text" class="form-control" id="formName" placeholder="Your name" required />
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Email</label>
                                <input type="email" class="form-control" id="formEmail" placeholder="you@example.com" required />
                            </div>
                            <div class="col-12">
                                <label class="form-label fw-semibold">Subject</label>
                                <input type="text" class="form-control" id="formSubject" placeholder="Subject" required />
                            </div>
                            <div class="col-12">
                                <label class="form-label fw-semibold">Message</label>
                                <textarea class="form-control" id="formMessage" rows="4" placeholder="Your message..." required></textarea>
                            </div>
                            <div class="col-12">
                                <button type="submit" class="btn btn-primary w-100 py-3 rounded-pill fw-semibold">
                                    <i class="fas fa-paper-plane me-2"></i>Send Message
                                </button>
                                <div id="formFeedback" class="mt-3"></div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============================================================
FOOTER (with WhatsApp)
============================================================ -->
<footer class="footer-custom">
    <div class="container text-center">
        <p class="mb-1">
            &copy; 2026 <strong>StudentHub</strong>. All rights reserved.
        </p>
        <p class="mb-0" style="opacity:0.6; font-size:0.9rem;">
            Made with <span class="heart"><i class="fas fa-heart"></i></span> by
            <strong class="text-primary">Virat</strong> // Software Developer
        </p>
        <p class="mt-2 mb-0">
            <i class="fas fa-question-circle text-primary me-1"></i>
            Have a query? Contact me on
            <a href="https://wa.me/917310927827?text=Hi%20Virat%2C%20I%20have%20a%20question%20about%20your%20portfolio." target="_blank" class="fw-bold text-success">
                <i class="fab fa-whatsapp me-1"></i>WhatsApp
            </a>
        </p>
    </div>
</footer>

<!-- WhatsApp Floating Button (always visible) -->
<a href="https://wa.me/917310927827?text=Hi%20Virat%2C%20I%20have%20a%20question%20about%20your%20portfolio." target="_blank" class="whatsapp-float" aria-label="Chat on WhatsApp">
    <i class="fab fa-whatsapp"></i>
</a>

<!-- ============================================================
SCRIPTS
============================================================ -->
<!-- Bootstrap 5 -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js">
</script>
<!-- jQuery -->
<script src="https://code.jquery.com/jquery-3.7.1.min.js">
</script>
<!-- AOS -->
<script src="https://unpkg.com/aos@2.3.1/dist/aos.js">
</script>

<script>
    $(document).ready(function() {

        // ============================================================
        // 1. INIT AOS
        // ============================================================
        AOS.init({
            duration: 700,
            once: true,
            offset: 40,
            easing: 'ease-out-cubic'
        });

        // ============================================================
        // 2. TYPED TEXT
        // ============================================================
        const roles = [
            'Full Stack Developer',
            'Web Developer',
            'CS Student',
            'AI Enthusiast',
            'Problem Solver'
        ];
        let roleIndex = 0,
            charIndex = 0,
            isDeleting = false;
        const typedEl = document.getElementById('typedText');

        function typeEffect() {
            const current = roles[roleIndex];
            if (!isDeleting) {
                typedEl.textContent = current.substring(0, charIndex + 1);
                charIndex++;
                if (charIndex === current.length) {
                    isDeleting = true;
                    setTimeout(typeEffect, 2200);
                    return;
                }
                setTimeout(typeEffect, 80);
            } else {
                typedEl.textContent = current.substring(0, charIndex);
                charIndex--;
                if (charIndex < 0) {
                    isDeleting = false;
                    charIndex = 0;
                    roleIndex = (roleIndex + 1) % roles.length;
                    setTimeout(typeEffect, 300);
                    return;
                }
                setTimeout(typeEffect, 40);
            }
        }
        typeEffect();

        // ============================================================
        // 3. DARK MODE
        // ============================================================
        const stored = localStorage.getItem('theme');
        if (stored === 'dark') {
            $('body').addClass('dark-mode');
            $('#themeToggle i').removeClass('fa-moon').addClass('fa-sun');
        }

        $('#themeToggle').on('click', function() {
            $('body').toggleClass('dark-mode');
            const isDark = $('body').hasClass('dark-mode');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            $(this).find('i').toggleClass('fa-moon fa-sun');
        });

        // ============================================================
        // 4. CONTACT FORM
        // ============================================================
        $('#contactForm').on('submit', function(e) {
            e.preventDefault();
            const name = $('#formName').val().trim();
            const email = $('#formEmail').val().trim();
            const subject = $('#formSubject').val().trim();
            const message = $('#formMessage').val().trim();

            if (!name || !email || !subject || !message) {
                $('#formFeedback').html('<div class="alert alert-danger">All fields are required.</div>');
                return;
            }
            if (!email.includes('@')) {
                $('#formFeedback').html('<div class="alert alert-danger">Please enter a valid email.</div>');
                return;
            }

            $('#formFeedback').html('<div class="alert alert-info"><i class="fas fa-spinner fa-spin me-2"></i>Sending...</div>');
            setTimeout(() => {
                $('#formFeedback').html(
                    '<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>Your message has been sent! (Demo)</div>'
                );
                $('#contactForm')[0].reset();
            }, 1600);
        });

        // ============================================================
        // 5. RESUME BUTTON
        // ============================================================
        $('#resumeBtn, #resumeDownloadBtn').on('click', function(e) {
            e.preventDefault();
            alert('📄 Resume download will be available here. (Add your PDF link)');
        });

        // ============================================================
        // 6. SMOOTH SCROLL for nav links
        // ============================================================
        $('.nav-link').on('click', function(e) {
            const href = $(this).attr('href');
            if (href && href.startsWith('#')) {
                e.preventDefault();
                const target = $(href);
                if (target.length) {
                    $('html, body').animate({
                        scrollTop: target.offset().top - 70
                    }, 600);
                }
                const nav = $('#navMenu');
                if (nav.hasClass('show')) {
                    nav.removeClass('show');
                }
            }
        });

        // ============================================================
        // 7. AUTH MODAL (demo handlers – replace with real API calls)
        // ============================================================
        $('#loginForm').on('submit', function(e) {
            e.preventDefault();
            const email = $('#loginEmail').val().trim();
            const password = $('#loginPassword').val().trim();
            if (!email || !password) {
                $('#loginFeedback').html('<span class="text-danger">Please fill all fields.</span>');
                return;
            }
            // Replace with actual POST to /api/auth/login
            $.ajax({
                url: '/api/auth/login',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ email, password }),
                success: function(resp) {
                    $('#loginFeedback').html('<span class="text-success">Logged in successfully!</span>');
                    localStorage.setItem('access_token', resp.access_token);
                    setTimeout(() => $('#authModal').modal('hide'), 1000);
                },
                error: function(err) {
                    $('#loginFeedback').html('<span class="text-danger">' + (err.responseJSON?.message || 'Login failed') + '</span>');
                }
            });
        });

        $('#registerForm').on('submit', function(e) {
            e.preventDefault();
            const username = $('#regUsername').val().trim();
            const email = $('#regEmail').val().trim();
            const password = $('#regPassword').val().trim();
            if (!username || !email || !password || password.length < 6) {
                $('#registerFeedback').html('<span class="text-danger">Please fill all fields (password min 6 chars).</span>');
                return;
            }
            $.ajax({
                url: '/api/auth/register',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ username, email, password }),
                success: function() {
                    $('#registerFeedback').html('<span class="text-success">Account created! You can now login.</span>');
                    $('#login-tab').tab('show');
                    $('#registerForm')[0].reset();
                },
                error: function(err) {
                    $('#registerFeedback').html('<span class="text-danger">' + (err.responseJSON?.message || 'Registration failed') + '</span>');
                }
            });
        });

        // Reset feedback when modal is hidden
        $('#authModal').on('hidden.bs.modal', function() {
            $('#loginFeedback').empty();
            $('#registerFeedback').empty();
        });

    });
</script>

</body>
</html>
"""

@app.route('/')
def serve_index():
    return HTML_TEMPLATE

# ---------- RUN ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('FLASK_ENV') == 'development')