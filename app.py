from flask import Flask, request, render_template, redirect
import mysql.connector
import os

app = Flask(__name__)

# Load from environment variables
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

@app.route('/send/<int:id>', methods=['GET'])
def send_message(id):
    # You can use any SMS API here (like Twilio or Fast2SMS)
    return f"Send SMS back to sender ID with ID = {id} (Add your SMS API logic here)"

if __name__ == '__main__':
    app.run(debug=True)
