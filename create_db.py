import sqlite3

conn = sqlite3.connect('happyhappy.db')
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS moods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    mood TEXT,
    note TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    name TEXT,
    title TEXT,
    story TEXT,
    timestamp TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    message TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    entry TEXT,
    timestamp TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS breathing_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    timestamp TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS affirmations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    affirmation TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chatbot_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_msg TEXT,
    bot_reply TEXT
)""")

conn.commit()
conn.close()
print("✅ Database and tables created!")
