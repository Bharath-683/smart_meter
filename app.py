@app.route('/api/sms', methods=['POST'])
def api_sms():
    data = request.get_json()
    sender_id = data['sender_id']
    message = data['message']
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sms_logs (sender_id, message) VALUES (%s, %s)",
        (sender_id, message)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'Message stored successfully'})
