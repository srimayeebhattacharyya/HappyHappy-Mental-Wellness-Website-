from flask import Flask, render_template, request, redirect, url_for,jsonify,session,flash,Response,json
import openai,traceback
import mysql.connector
from datetime import datetime
from textblob import TextBlob
from flask_session import Session
import random
app = Flask(__name__)
app.secret_key = 'mithi-123'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Srimayee20",
        database="happyhappy_db"
    )
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
    action = request.form['action']  # either 'login' or 'signup'

    conn = get_mysql_connection()
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()

    if action == 'login':
        if result and result[0] == password:
            session['username'] = username
            return redirect(url_for('index'))  # or dashboard
        else:
            return "❌ Invalid username or password."

    elif action == 'signup':
        if result:
            return "⚠️ Username already taken. Try another one."
        else:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            session['username'] = username
            return redirect(url_for('index'))

    cursor.close()
    conn.close()
    return "Something went wrong!"


@app.route('/Home')
def Home():
    return render_template('index.html')

@app.route('/Selfhelp')
def Selfhelp():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))  # Redirect to login/signup page
    return render_template('Self-help.html')

@app.route('/submit_mood', methods=['POST'])
def submit_mood():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    mood = request.form['mood']
    note = request.form['note']

    connection = get_mysql_connection()
    if connection:
        cursor = connection.cursor()
        query = "INSERT INTO moods (mood, note) VALUES (%s, %s)"
        cursor.execute(query, (mood, note))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('show_moods'))
    else:
        return "Database connection failed."

@app.route('/show_moods', methods=['GET'])
def show_moods():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    connection = get_mysql_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT mood, note FROM moods ORDER BY id DESC")
    moods = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('moods.html', moods=moods)

@app.route('/Stories', methods=['GET', 'POST'])
def Stories():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    connection = get_mysql_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        title = request.form['title']
        story = request.form['story']
        username = session['username']

        query = "INSERT INTO stories (username, name, title, story) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (username, name, title, story))
        connection.commit()

    # Fetch all stories to display
    cursor.execute("SELECT name, title, story FROM stories ORDER BY timestamp DESC")
    all_stories = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('Stories.html', stories=all_stories)


@app.route('/Contact', methods=['GET', 'POST'])
def Contact():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor()
            query = "INSERT INTO contacts (name, email, message) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, email, message))
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for('index'))
        else:
            return "Failed to connect to MySQL Database."
    return render_template('Contact.html')


@app.route('/save-journal', methods=['POST'])
def save_journal():
    if 'username' not in session:
        return redirect(url_for('GetStarted'))

    entry = request.form['entry']
    
    connection = get_mysql_connection()
    cursor = connection.cursor()
    query = "INSERT INTO journals (username, entry, timestamp) VALUES (%s, %s, %s)"
    cursor.execute(query, (session['username'], entry, datetime.now()))
    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for('journal'))


@app.route('/journal')
def journal():
    if 'username' not in session:
        print("⚠️ No username in session")
        return redirect(url_for('GetStarted'))

    username = session['username']
    print(f"✅ Logged in as: {username}")

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT entry, timestamp FROM journals WHERE username = %s ORDER BY timestamp DESC"
        cursor.execute(query, (username,))
        entries = cursor.fetchall()

        print("✅ Entries fetched:", entries[:2])  # print first 2 entries for debug

        cursor.close()
        connection.close()

        return render_template('journal.html', entries=entries)

    except Exception as e:
        print("🔥 Error fetching journal entries:", e)
        return "Error occurred while fetching journal entries."


@app.route('/Trynow')
def Trynow():
    return render_template('Trynow.html')

@app.route('/breathing_done', methods=['POST'])
def breathing_done():
    if 'username' not in session:
        return jsonify({'status': 'unauthorized'}), 401

    connection = get_mysql_connection()
    cursor = connection.cursor()
    query = "INSERT INTO breathing_sessions (username) VALUES (%s)"
    cursor.execute(query, (session['username'],))
    connection.commit()
    cursor.close()
    connection.close()
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

    conn = get_mysql_connection()
    cursor = conn.cursor()
    query = "INSERT INTO affirmations (username, affirmation) VALUES (%s, %s)"
    cursor.execute(query, (session['username'], affirmation))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'success'})

@app.route('/Affirmations')
def affirmations():
    if 'username' not in session:
        return jsonify({'status': 'unauthorized'}), 401
    return render_template('affirmations.html', logged_in=True)


def bot_reply(history):
    last_msg = history[-1]['content'].lower()

    # Emotion-based logic
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

    # --- Rule-based responses ---
    if "hello" in user_msg or "hi" in user_msg:
        bot_reply = "Hello! 😊 How are you feeling today?"
    elif "sad" in user_msg or "upset" in user_msg:
        bot_reply = "I'm really sorry to hear that. Want to talk about it?"
    elif "happy" in user_msg:
        bot_reply = "That's wonderful! Keep smiling 🌟"
    elif "anxious" in user_msg or "nervous" in user_msg:
        bot_reply = "Try some deep breathing. Would you like a breathing exercise?"
    elif "bye" in user_msg or "goodbye" in user_msg:
        bot_reply = "Take care! I'm always here when you need me. 💛"
    elif "help" in user_msg:
        bot_reply = "Sure, I can help. Are you looking for self-care tips, mood tracking, or someone to talk to?"
    elif "stress" in user_msg or "tired" in user_msg:
        bot_reply = "It’s okay to feel this way. How about taking a short walk or listening to some calming music?"
    else:
        bot_reply = "I'm here for you. Can you tell me more about how you're feeling?"

    # Save conversation to DB
    sql = "INSERT INTO chatbot_conversations (user_msg, bot_reply) VALUES (%s, %s)"
    conn = get_mysql_connection()
    cursor = conn.cursor()
    val = (user_msg, bot_reply)
    cursor.execute(sql, val)
    conn.commit()

    return jsonify({"response": bot_reply})


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
