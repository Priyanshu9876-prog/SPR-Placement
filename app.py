import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env from project root (if present)
load_dotenv()

# Create Flask app
app = Flask(__name__, static_folder='frontend/static', template_folder='frontend')

# Config from environment with sensible defaults
# DATABASE_URL may be in the form "postgres://..." so we replace that prefix for SQLAlchemy
database_url = os.environ.get('DATABASE_URL', '') or 'sqlite:///spr.db'
database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS', 'False') == 'True'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-in-production')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False') == 'True'

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# ---------------- Models ----------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    dept = db.Column(db.String(80))
    year = db.Column(db.String(20))
    email = db.Column(db.String(120))
    offers = db.relationship('Offer', backref='student', cascade="all, delete-orphan")
    internships = db.relationship('Internship', backref='student', cascade="all, delete-orphan")

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(120))
    role = db.Column(db.String(120))
    ctc = db.Column(db.String(50))
    status = db.Column(db.String(50), default='Offered')  # Offered, Accepted, Declined, Joined
    date = db.Column(db.Date, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)

class Internship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(120))
    role = db.Column(db.String(120))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Ongoing')  # Ongoing, Completed
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    reports = db.relationship('Report', backref='internship', cascade="all, delete-orphan")

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    evaluation = db.Column(db.String(200))
    internship_id = db.Column(db.Integer, db.ForeignKey('internship.id'), nullable=False)

# ---------------- Serializers ----------------
def serialize_student(s):
    return {
        'id': s.id,
        'roll_no': s.roll_no,
        'name': s.name,
        'dept': s.dept,
        'year': s.year,
        'email': s.email,
        'offers': [serialize_offer(o) for o in s.offers],
        'internships': [serialize_internship(i) for i in s.internships]
    }

def serialize_offer(o):
    return {
        'id': o.id,
        'company': o.company,
        'role': o.role,
        'ctc': o.ctc,
        'status': o.status,
        'date': o.date.isoformat() if o.date else None,
        'student_id': o.student_id
    }

def serialize_internship(i):
    return {
        'id': i.id,
        'company': i.company,
        'role': i.role,
        'start_date': i.start_date.isoformat() if i.start_date else None,
        'end_date': i.end_date.isoformat() if i.end_date else None,
        'status': i.status,
        'student_id': i.student_id,
        'reports': [serialize_report(r) for r in i.reports]
    }

def serialize_report(r):
    return {
        'id': r.id,
        'date': r.date.isoformat() if r.date else None,
        'title': r.title,
        'content': r.content,
        'evaluation': r.evaluation,
        'internship_id': r.internship_id
    }

# ---------------- Routes - Students ----------------
@app.route('/api/students', methods=['GET', 'POST'])
def students():
    if request.method == 'POST':
        data = request.json or {}
        s = Student(
            roll_no=data.get('roll_no'),
            name=data.get('name'),
            dept=data.get('dept'),
            year=data.get('year'),
            email=data.get('email')
        )
        db.session.add(s)
        db.session.commit()
        return jsonify(serialize_student(s)), 201
    students = Student.query.all()
    return jsonify([serialize_student(s) for s in students])

@app.route('/api/students/<int:student_id>', methods=['GET','PUT','DELETE'])
def student_detail(student_id):
    s = Student.query.get_or_404(student_id)
    if request.method == 'GET':
        return jsonify(serialize_student(s))
    if request.method == 'PUT':
        data = request.json or {}
        s.roll_no = data.get('roll_no', s.roll_no)
        s.name = data.get('name', s.name)
        s.dept = data.get('dept', s.dept)
        s.year = data.get('year', s.year)
        s.email = data.get('email', s.email)
        db.session.commit()
        return jsonify(serialize_student(s))
    db.session.delete(s)
    db.session.commit()
    return jsonify({'message':'deleted'})

# ---------------- Routes - Offers ----------------
@app.route('/api/offers', methods=['GET', 'POST'])
def offers():
    if request.method == 'POST':
        data = request.json or {}
        o = Offer(
            company=data.get('company'),
            role=data.get('role'),
            ctc=data.get('ctc'),
            status=data.get('status','Offered'),
            date=(datetime.fromisoformat(data.get('date')).date() if data.get('date') else datetime.utcnow().date()),
            student_id=data['student_id']
        )
        db.session.add(o)
        db.session.commit()
        return jsonify(serialize_offer(o)), 201
    all_offers = Offer.query.all()
    return jsonify([serialize_offer(o) for o in all_offers])

@app.route('/api/offers/<int:offer_id>', methods=['PUT','DELETE'])
def offer_detail(offer_id):
    o = Offer.query.get_or_404(offer_id)
    if request.method == 'PUT':
        data = request.json or {}
        o.company = data.get('company', o.company)
        o.role = data.get('role', o.role)
        o.ctc = data.get('ctc', o.ctc)
        o.status = data.get('status', o.status)
        if data.get('date'):
            o.date = datetime.fromisoformat(data.get('date')).date()
        db.session.commit()
        return jsonify(serialize_offer(o))
    db.session.delete(o)
    db.session.commit()
    return jsonify({'message':'deleted'})

# ---------------- Routes - Internships ----------------
@app.route('/api/internships', methods=['GET', 'POST'])
def internships():
    if request.method == 'POST':
        data = request.json or {}
        i = Internship(
            company=data.get('company'),
            role=data.get('role'),
            start_date=(datetime.fromisoformat(data.get('start_date')).date() if data.get('start_date') else None),
            end_date=(datetime.fromisoformat(data.get('end_date')).date() if data.get('end_date') else None),
            status=data.get('status','Ongoing'),
            student_id=data['student_id']
        )
        db.session.add(i)
        db.session.commit()
        return jsonify(serialize_internship(i)), 201
    all_intern = Internship.query.all()
    return jsonify([serialize_internship(i) for i in all_intern])

@app.route('/api/internships/<int:id>', methods=['PUT','DELETE'])
def internship_detail(id):
    i = Internship.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json or {}
        i.company = data.get('company', i.company)
        i.role = data.get('role', i.role)
        if data.get('start_date'):
            i.start_date = datetime.fromisoformat(data.get('start_date')).date()
        if data.get('end_date'):
            i.end_date = datetime.fromisoformat(data.get('end_date')).date()
        i.status = data.get('status', i.status)
        db.session.commit()
        return jsonify(serialize_internship(i))
    db.session.delete(i)
    db.session.commit()
    return jsonify({'message':'deleted'})

# ---------------- Routes - Reports ----------------
@app.route('/api/reports', methods=['POST'])
def reports():
    data = request.json or {}
    r = Report(
        date=(datetime.fromisoformat(data.get('date')).date() if data.get('date') else datetime.utcnow().date()),
        title=data.get('title'),
        content=data.get('content'),
        evaluation=data.get('evaluation'),
        internship_id=data['internship_id']
    )
    db.session.add(r)
    db.session.commit()
    return jsonify(serialize_report(r)), 201

@app.route('/api/reports/<int:report_id>', methods=['PUT','DELETE'])
def report_detail(report_id):
    r = Report.query.get_or_404(report_id)
    if request.method == 'PUT':
        data = request.json or {}
        if data.get('date'):
            r.date = datetime.fromisoformat(data.get('date')).date()
        r.title = data.get('title', r.title)
        r.content = data.get('content', r.content)
        r.evaluation = data.get('evaluation', r.evaluation)
        db.session.commit()
        return jsonify(serialize_report(r))
    db.session.delete(r)
    db.session.commit()
    return jsonify({'message':'deleted'})

# ---------------- Dashboard ----------------
@app.route('/api/dashboard/summary', methods=['GET'])
def dashboard_summary():
    total_students = Student.query.count()
    total_offers = Offer.query.count()
    accepted = Offer.query.filter_by(status='Accepted').count()
    joined = Offer.query.filter_by(status='Joined').count()
    ongoing_intern = Internship.query.filter_by(status='Ongoing').count()
    return jsonify({
        'total_students': total_students,
        'total_offers': total_offers,
        'accepted_offers': accepted,
        'joined_offers': joined,
        'ongoing_internships': ongoing_intern
    })

# ---------------- Serve frontend ----------------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory('frontend', 'index.html')

if __name__ == '__main__':
    # create DB and seed sample data
    db.create_all()
    if Student.query.count() == 0:
        s1 = Student(roll_no='BT123', name='Aman Verma', dept='CSE', year='3', email='aman@example.com')
        s2 = Student(roll_no='BT124', name='Priyanshu Agarwal', dept='IT', year='3', email='priyanshu@example.com')
        db.session.add_all([s1,s2]); db.session.commit()
        o1 = Offer(company='Zomato', role='SDE Intern', ctc='6 LPA', status='Accepted', date=datetime(2025,5,10), student_id=s2.id)
        i1 = Internship(company='ABC Corp', role='Data Analyst Intern', start_date=datetime(2025,6,1), end_date=datetime(2025,8,31), status='Completed', student_id=s1.id)
        db.session.add_all([o1,i1]); db.session.commit()

    # Use debug from config
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=app.config['DEBUG'])
