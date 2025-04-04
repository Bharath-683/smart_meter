from flask import Flask, request, render_template, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

# Database config
DB_CONFIG = {
    'host': 'mysql-2610e868-sms-server.b.aivencloud.com',
    'port': 26823,
    'user': 'avnadmin',
    'password': 'AVNS_4VfJgQaGIu2viesZ0AB',
    'database': 'defaultdb'  # Use your actual DB name
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/api/sms', methods=['POST'])
def receive_sms():
    data = request.get_json()
    sender_id = data.get('sender_id')
    message = data.get('message')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sms_logs (sender_id, message) VALUES (%s, %s)", (sender_id, message))
    conn.commit()
    cursor.close()
    conn.close()

    return 'SMS Stored', 200

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sms_logs ORDER BY created_at DESC")
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', messages=messages)

@app.route('/send/<sender_id>', methods=['POST'])
def send_back(sender_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM sms_logs WHERE sender_id = %s ORDER BY created_at DESC LIMIT 1", (sender_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        message = result[0]
        print(f"📤 Sending SMS to {sender_id}: {message}")  # Simulate SMS sending
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
