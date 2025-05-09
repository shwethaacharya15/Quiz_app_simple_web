from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from fpdf import FPDF
import os
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- Models -------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), unique=True, nullable=False)  # as username
    last_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)  # hashed password

# ---------------- Questions -------------------
questions = [
    {"question": "What does HTML stand for?", "options": ["Hyper Text Markup Language", "Hot Mail", "How to Make Lasagna"], "answer": "Hyper Text Markup Language"},
    {"question": "What does CSS stand for?", "options": ["Cascading Style Sheets", "Colorful Style Sheets", "Computer Style Sheet"], "answer": "Cascading Style Sheets"},
    {"question": "Which language is used for web apps?", "options": ["PHP", "Python", "All"], "answer": "All"},
    {"question": "What does JavaScript do?", "options": ["Controls Web Behavior", "Styles Web Pages", "Provides Content", "All of the above"], "answer": "Controls Web Behavior"},
    {"question": "What is the purpose of the 'meta' tag in HTML?", "options": ["SEO", "Internal Links", "Metadata", "None of the above"], "answer": "SEO"},
    {"question": "Which HTML element is used for links?", "options": ["<link>", "<a>", "<url>", "<href>"], "answer": "<a>"},
    {"question": "What is Bootstrap?", "options": ["CSS Framework", "JavaScript Library", "PHP Framework", "None of the above"], "answer": "CSS Framework"},
    {"question": "What is the correct syntax for a comment in CSS?", "options": ["// comment", "/* comment */", "# comment", "// comment #"], "answer": "/* comment */"},
    {"question": "Which of the following is used to fetch data from an API?", "options": ["GET", "POST", "PUT", "DELETE"], "answer": "GET"},
    {"question": "What is the use of the 'alt' attribute in the <img> tag?", "options": ["Text description of image", "Image URL", "Image height", "Image width"], "answer": "Text description of image"}
]


# ---------------- Routes -------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']

        # Check if user already exists
        existing_user = User.query.filter_by(first_name=first_name).first()
        if existing_user:
            flash('User already exists. Please log in.', 'error')
            return redirect(url_for('login'))

        # Hash the password before storing
        hashed_password = generate_password_hash(password)

        new_user = User(first_name=first_name, last_name=last_name, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registered successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        first_name = request.form['first_name']
        password = request.form['password']

        user = User.query.filter_by(first_name=first_name).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.first_name
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))  # Or any route after login
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', name=session.get('name'))


@app.route('/start_new_quiz', methods=['GET'])
def start_new_quiz():
    # Reset session data for new quiz
    session.pop('current_question', None)
    session.pop('score', None)
    session['index'] = 0  # Reset to first question
    session['score'] = 0  # Reset score

    # Redirect to the quiz page
    return redirect(url_for('quiz'))


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Initialize current index if not in session
    if 'index' not in session:
        session['index'] = 0
        session['score'] = 0

    index = session['index']

    # Handle form submission
    if request.method == 'POST':
        selected = request.form.get('option')
        correct_answer = questions[index]['answer']
        if selected == correct_answer:
            session['score'] += 1

        # Handle navigation
        if 'next' in request.form and index < len(questions) - 1:
            session['index'] += 1
        elif 'prev' in request.form and index > 0:
            session['index'] -= 1
        elif 'submit' in request.form:
            return redirect(url_for('result'))  # Redirect to score page

        return redirect(url_for('quiz'))

    index = session.get('index', 0)
    if index >= len(questions):
        return redirect(url_for('result'))  # Redirect to result page if all questions are done

    return render_template('quiz.html', question=questions[index], questions=questions, index=index, total=len(questions))


@app.route('/result')
def result():
    if 'score' not in session:
        return redirect(url_for('quiz'))
    score = session['score']
    total = len(questions)  # Total number of questions
    user = User.query.get(session['user_id'])
    return render_template('result.html', score=score, name=user.first_name, total=total)




@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists('users.db'):
            db.create_all()
    app.run(debug=True)
