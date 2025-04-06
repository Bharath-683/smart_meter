from flask import Flask, request, render_template, redirect
import mysql.connector
import os
import requests

app = Flask(__name__)

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME'),
    'port': int(os.environ.get('DB_PORT', 3306))
}

# Home page: Show all messages
@app.route('/')
def index():
    with mysql.connector.connect(**DB_CONFIG) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sms_logs ORDER BY created_at DESC")
        messages = cursor.fetchall()
    return render_template("index.html", messages=messages)

# API to receive SMS from ESP32
@app.route('/api/sms', methods=['POST'])
def receive_sms():
    data = request.json
    sender_id = data.get('sender_id')
    message = data.get('message')

    with mysql.connector.connect(**DB_CONFIG) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sms_logs (sender_id, message) VALUES (%s, %s)", (sender_id, message))
        conn.commit()

    return {"status": "Message received"}

# Handle user reply from the web form
@app.route('/reply/<int:id>', methods=['POST'])
def reply(id):
    reply_msg = request.form.get('reply_message')

    with mysql.connector.connect(**DB_CONFIG) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sms_logs WHERE id = %s", (id,))
        sms = cursor.fetchone()

        if sms:
            sender_id = sms['sender_id']

            # Save reply to the same message row
            cursor.execute("UPDATE sms_logs SET reply = %s WHERE id = %s", (reply_msg, id))
            conn.commit()

    # Try to send the reply to ESP32 (local IP or remote)
    try:
        response = requests.post(
            'http://192.168.43.72/reply',
            json={'sender_id': sender_id, 'message': reply_msg},
            timeout=5
        )
        print(f"ESP32 response: {response.text}")
    except Exception as e:
        print("ESP32 not responding:", e)

    return redirect('/')

# ESP32 polls this to get the latest reply
@app.route('/api/replies/<sender_id>', methods=['GET'])
def get_reply(sender_id):
    with mysql.connector.connect(**DB_CONFIG) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT reply FROM sms_logs
            WHERE sender_id = %s AND reply IS NOT NULL AND reply != ''
            ORDER BY created_at DESC LIMIT 1
        """, (sender_id,))
        row = cursor.fetchone()

    if row:
        return {"reply": row['reply']}
    else:
        return {"reply": ""}

if __name__ == '__main__':
    app.run(debug=True)
