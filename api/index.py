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

# Simple best-effort rate limiter (works per Vercel container)
ip_tracker = {}
RATE_LIMIT_TRIES = 3
RATE_LIMIT_WINDOW = 60 # seconds

@app.route('/api/student/<reg_no>', methods=['GET'])
def get_student(reg_no):
    if not student_data:
        return jsonify({"error": "Data not loaded"}), 500
        
    # Get IP from Vercel's proxy header
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip:
        client_ip = client_ip.split(',')[0].strip()
        current_time = time.time()
        
        # Clean old IP records
        if client_ip in ip_tracker:
            ip_tracker[client_ip] = [t for t in ip_tracker[client_ip] if current_time - t < RATE_LIMIT_WINDOW]
            
            if len(ip_tracker[client_ip]) >= RATE_LIMIT_TRIES:
                return jsonify({"error": "Rate limit exceeded. Please wait 60 seconds."}), 429
                
            ip_tracker[client_ip].append(current_time)
        else:
            ip_tracker[client_ip] = [current_time]
        
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
