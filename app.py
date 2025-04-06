from flask import Flask, request, render_template, redirect
import mysql.connector
import os
import requests

app = Flask(__name__)

# Environment variables for deployment
DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME'),
    'port': int(os.environ.get('DB_PORT', 3306))
}

@app.route('/')
def index():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sms_logs ORDER BY created_at DESC")
        messages = cursor.fetchall()
        conn.close()
        return render_template("index.html", messages=messages)
    except Exception as e:
        return f"Database error: {e}", 500

@app.route('/api/sms', methods=['POST'])
def receive_sms():
    try:
        data = request.json
        sender_id = data.get('sender_id')
        message = data.get('message')

        if not sender_id or not message:
            return {"status": "Missing sender_id or message"}, 400

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sms_logs (sender_id, message) VALUES (%s, %s)", (sender_id, message))
        conn.commit()
        conn.close()

        return {"status": "Message received"}
    except Exception as e:
        return {"status": f"Server error: {str(e)}"}, 500

@app.route('/reply/<int:id>', methods=['POST'])
def reply(id):
    try:
        message = request.form.get('reply_message')
        if not message:
            return "Missing reply message", 400

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sms_logs WHERE id = %s", (id,))
        sms = cursor.fetchone()
        conn.close()

        if sms:
            sender_id = sms['sender_id']
            try:
                response = requests.post(
                    'http://192.168.43.72/reply',
                    json={'sender_id': sender_id, 'message': message},
                    timeout=5
                )
                print(f"ESP32 response: {response.text}")
            except Exception as e:
                print("ESP32 not responding:", e)
                return f"ESP32 not responding: {str(e)}", 500

            return redirect('/')
        else:
            return "SMS not found", 404
    except Exception as e:
        print("Server error:", e)
        return f"Internal error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
