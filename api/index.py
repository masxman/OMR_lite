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

@app.route('/api/student/<reg_no>', methods=['GET'])
def get_student(reg_no):
    if not student_data:
        return jsonify({"error": "Data not loaded"}), 500
        
    if reg_no in student_data:
        info = student_data[reg_no]
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
