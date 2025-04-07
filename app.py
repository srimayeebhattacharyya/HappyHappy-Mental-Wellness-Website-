from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from datetime import datetime
from flask_session import Session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = 'mithi-123'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

DATABASE = 'happyhappy.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/GetStarted')
def GetStarted():
    return render_template('GetStarted.html')

@app.route('/auth', methods=['POST'])
def auth():
    username = request.form['username']
    password = request.form['password']
    action = request.form['action']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    if action == 'login':
        if result and result['password'] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "❌ Invalid username or password."
    elif action == 'signup':
        if result:
            return "⚠️ Username already taken. Try another one."
        else:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            session['username'] = username
            return redirect(url_for('index'))

@app.route('/Home')
def Home():
    return render_template('index.html')

@app.route('/Selfhelp')
def Selfhelp():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))
    return render_template('Self-help.html')

@app.route('/submit_mood', methods=['POST'])
def submit_mood():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    mood = request.form['mood']
    note = request.form['note']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO moods (username, mood, note) VALUES (?, ?, ?)", (session['username'], mood, note))
    conn.commit()
    return redirect(url_for('show_moods'))

@app.route('/show_moods')
def show_moods():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mood, note FROM moods WHERE username = ? ORDER BY id DESC", (session['username'],))
    moods = cursor.fetchall()
    return render_template('moods.html', moods=moods)

@app.route('/Stories', methods=['GET', 'POST'])
def Stories():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        title = request.form['title']
        story = request.form['story']
        username = session['username']
        cursor.execute("INSERT INTO stories (username, name, title, story, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (username, name, title, story, datetime.now()))
        conn.commit()

    cursor.execute("SELECT name, title, story FROM stories ORDER BY timestamp DESC")
    all_stories = cursor.fetchall()
    return render_template('Stories.html', stories=all_stories)

@app.route('/Contact', methods=['GET', 'POST'])
def Contact():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)", (name, email, message))
        conn.commit()
        return redirect(url_for('index'))

    return render_template('Contact.html')

@app.route('/save-journal', methods=['POST'])
def save_journal():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    entry = request.form['entry']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO journals (username, entry, timestamp) VALUES (?, ?, ?)",
                   (session['username'], entry, datetime.now()))
    conn.commit()
    return redirect(url_for('journal'))

@app.route('/journal')
def journal():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT entry, timestamp FROM journals WHERE username = ? ORDER BY timestamp DESC", (session['username'],))
    entries = cursor.fetchall()
    return render_template('journal.html', entries=entries)

@app.route('/Trynow')
def Trynow():
    return render_template('Trynow.html')

@app.route('/breathing_done', methods=['POST'])
def breathing_done():
    if 'username' not in session:
        return jsonify({'status': 'unauthorized'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO breathing_sessions (username, timestamp) VALUES (?, ?)", (session['username'], datetime.now()))
    conn.commit()
    return jsonify({'status': 'success'})

affirmation_list = [
    "You are strong and capable.",
    "Every day is a fresh start.",
    "You deserve happiness.",
    "You are enough, just as you are.",
    "Your mind is calm and your heart is strong.",
    "You are growing every single day.",
    "Kindness flows from you naturally.",
    "You are loved more than you know.",
    "Your feelings are valid.",
    "Peace begins with you."
]

@app.route('/save_affirmation', methods=['POST'])
def save_affirmation():
    if 'username' not in session:
        return jsonify({'status': 'unauthorized'}), 401

    data = request.get_json()
    affirmation = data.get('affirmation')

    if not affirmation:
        return jsonify({'status': 'error', 'message': 'No affirmation provided'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO affirmations (username, affirmation) VALUES (?, ?)", (session['username'], affirmation))
    conn.commit()
    return jsonify({'status': 'success'})

@app.route('/Affirmations')
def affirmations():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))
    return render_template('affirmations.html', affirmations=affirmation_list, logged_in=True)

# -------- Chatbot Logic -------- #
def bot_reply(history):
    last_msg = history[-1]['content'].lower()

    if any(word in last_msg for word in ["sad", "depressed", "down", "unhappy", "hopeless"]):
        return random.choice([
            "I'm really sorry you're feeling this way. Want to talk about what's making you feel down?",
            "You're not alone. I'm here to listen, no judgment.",
            "It's okay to feel sad sometimes. Want to try a breathing exercise?"
        ])
    elif any(word in last_msg for word in ["happy", "excited", "joy", "glad", "cheerful"]):
        return random.choice([
            "That's awesome! Want to share what made you feel this way?",
            "I love hearing happy news. Let’s celebrate your joy! 🎉",
            "Yay! Positive vibes are the best vibes!"
        ])
    elif any(word in last_msg for word in ["anxious", "nervous", "panic", "afraid", "worried"]):
        return random.choice([
            "Anxiety can be tough. Want to try a short mindfulness technique?",
            "You're safe here. Just take a deep breath with me — inhale… exhale…",
            "Would writing down your thoughts help you feel better?"
        ])
    elif "breathe" in last_msg:
        return "Here’s a quick breathing trick: Inhale for 4… Hold for 4… Exhale for 4… Repeat 💛"
    elif "thank" in last_msg:
        return "Anytime! I’m really glad to be here with you."
    elif "bye" in last_msg or "goodbye" in last_msg:
        return "Take care, Mithi 🌼 Come back anytime you need me!"
    else:
        return random.choice([
            "I'm here for you. Want to tell me more?",
            "Tell me anything that's on your mind.",
            "Would journaling help you right now?"
        ])

@app.route("/chatbot", methods=["POST"])
def chatbot():
    user_msg = request.json.get("message", "").lower()

    if "hello" in user_msg or "hi" in user_msg:
        reply = "Hello! 😊 How are you feeling today?"
    elif "sad" in user_msg or "upset" in user_msg:
        reply = "I'm really sorry to hear that. Want to talk about it?"
    elif "happy" in user_msg:
        reply = "That's wonderful! Keep smiling 🌟"
    elif "anxious" in user_msg or "nervous" in user_msg or "worried" in user_msg:
        reply = "It’s okay to feel anxious. I'm here for you. Would you like to try a calming exercise or journaling?"
    elif "bye" in user_msg or "goodbye" in user_msg:
        reply = "Take care 🌸 Remember, you're not alone."
    else:
        history = [{"role": "user", "content": user_msg}]
        reply = bot_reply(history)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS chatbot_conversations (user_msg TEXT, bot_reply TEXT)")
    cursor.execute("INSERT INTO chatbot_conversations (user_msg, bot_reply) VALUES (?, ?)", (user_msg, reply))
    conn.commit()
    return jsonify({"reply": reply})

@app.route("/chatbot", methods=["GET"])
def chatbot_page():
    return render_template("chatbot.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('GetStarted'))

if __name__ == '__main__':
    app.run(debug=True)