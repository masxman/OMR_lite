from flask import Flask, jsonify, request
from flask_cors import CORS
import csv
import os

app = Flask(__name__)
CORS(app)

# Load CSV using built-in csv module to avoid heavy Pandas dependency
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'MCA', 'pipeline_data', 'ranked_results.csv')
student_data = {}

if os.path.exists(CSV_PATH):
    with open(CSV_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            student_data[row['Register_Number']] = {
                'Total_Score': row.get('Total_Score', '0'),
                'Rank_Range': row.get('Rank_Range', '--')
            }

import time

# Simple best-effort rate limiter with penalty
ip_tracker = {}
RATE_LIMIT_TRIES = 3
RATE_LIMIT_WINDOW = 60 # seconds to trigger penalty
PENALTY_COOLDOWN = 300 # 5 minutes penalty

@app.route('/api/student/<reg_no>', methods=['GET'])
def get_student(reg_no):
    if not student_data:
        return jsonify({"error": "Data not loaded"}), 500
        
    # Get IP from Vercel's proxy header
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip:
        client_ip = client_ip.split(',')[0].strip()
        current_time = time.time()
        
        if client_ip not in ip_tracker:
            ip_tracker[client_ip] = {'timestamps': [], 'penalty_until': 0}
            
        record = ip_tracker[client_ip]
        
        # Check if they are currently serving a penalty
        if current_time < record['penalty_until']:
            remaining = int(record['penalty_until'] - current_time)
            return jsonify({"error": f"Rate limit exceeded. Try again in {remaining} seconds."}), 429
            
        # Clean old timestamps outside the window
        record['timestamps'] = [t for t in record['timestamps'] if current_time - t < RATE_LIMIT_WINDOW]
        
        # If they hit the limit, apply the 5 minute penalty
        if len(record['timestamps']) >= RATE_LIMIT_TRIES:
            record['penalty_until'] = current_time + PENALTY_COOLDOWN
            return jsonify({"error": "Spam detected. You have been timed out for 5 minutes."}), 429
            
        record['timestamps'].append(current_time)
        
    if reg_no in student_data:
        info = student_data[reg_no]
        
        # Fire off Discord Webhook silently if configured
        webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
        if webhook_url:
            import urllib.request
            import urllib.error
            import json as json_lib
            try:
                payload = {
                    "content": f"🚨 **New Query!** Someone just checked Reg No: `{reg_no}` (Score: {info['Total_Score']}, Rank: {info['Rank_Range']})"
                }
                req = urllib.request.Request(
                    webhook_url, 
                    data=json_lib.dumps(payload).encode('utf-8'),
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                    }
                )
                urllib.request.urlopen(req, timeout=2) # Keep timeout extremely short to not block response
            except Exception as e:
                print(f"Webhook failed: {e}")

        return jsonify({
            "register_number": reg_no,
            "total_score": int(info['Total_Score']),
            "rank_range": info['Rank_Range']
        })
    else:
        return jsonify({"error": "Registration number not found"}), 404

# Expose the WSGI app for Vercel
# Vercel looks for the 'app' variable in api/index.py

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
