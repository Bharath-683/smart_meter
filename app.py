from flask import Flask, request, render_template, redirect
import mysql.connector
import os

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
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sms_logs ORDER BY created_at DESC")
    messages = cursor.fetchall()
    conn.close()
    return render_template("index.html", messages=messages)

@app.route('/api/sms', methods=['POST'])
def receive_sms():
    data = request.json
    sender_id = data.get('sender_id')
    message = data.get('message')

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sms_logs (sender_id, message) VALUES (%s, %s)", (sender_id, message))
    conn.commit()
    conn.close()

    return {"status": "Message received"}

@app.route('/reply/<int:id>', methods=['POST'])
def reply(id):
    message = request.form.get('reply_message')

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sms_logs WHERE id = %s", (id,))
    sms = cursor.fetchone()
    conn.close()

    if sms:
        sender_id = sms['sender_id']
        # Send reply to ESP32 (assuming it's listening)
        try:
            response = requests.post(
                'http://192.168.43.72/reply',
                json={'sender_id': sender_id, 'message': message},
                timeout=5
            )
            print(f"ESP32 response: {response.text}")
        except Exception as e:
            print("ESP32 not responding:", e)

        return redirect('/')
    else:
        return "SMS not found", 404


if __name__ == '__main__':
    app.run(debug=True)

