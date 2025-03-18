from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import os
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

app = Flask(__name__)
DB_NAME = 'medical_reimbursements.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reimbursements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            act_type TEXT,
            amount_paid REAL,
            reimbursed_by_secu BOOLEAN,
            base_reimbursement REAL,
            rate REAL,
            target_amount_reimbursed REAL,
            real_amount_reimbursed REAL,
            forfait_participation REAL,
            non_reimbursed_amount REAL,
            is_mutuelle BOOLEAN,
            mutuelle_name TEXT,
            mutuelle_reimbursed REAL,
            final_non_reimbursed REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/add_reimbursement', methods=['POST'])
def add_reimbursement():
    data = request.json
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    act_type = data['act_type']
    amount_paid = float(data['amount_paid'])
    reimbursed_by_secu = data['reimbursed_by_secu']

    base_reimbursement = float(data['base_reimbursement']) if reimbursed_by_secu else 0.0
    rate = float(data['rate']) if reimbursed_by_secu else 0.0
    target_amount_reimbursed = (base_reimbursement * rate) / 100 if reimbursed_by_secu else 0.0

    real_amount_reimbursed = float(data['real_amount_reimbursed']) if reimbursed_by_secu else 0.0
    forfait_participation = float(data['forfait_participation']) if reimbursed_by_secu else 0.0
    non_reimbursed_amount = amount_paid - real_amount_reimbursed - forfait_participation

    is_mutuelle = data['is_mutuelle']
    mutuelle_name = data['mutuelle_name'] if is_mutuelle else None
    mutuelle_reimbursed = float(data['mutuelle_reimbursed']) if is_mutuelle else 0.0
    final_non_reimbursed = non_reimbursed_amount - mutuelle_reimbursed

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reimbursements 
        (date, act_type, amount_paid, reimbursed_by_secu, base_reimbursement, rate, target_amount_reimbursed, 
        real_amount_reimbursed, forfait_participation, non_reimbursed_amount, is_mutuelle, mutuelle_name, 
        mutuelle_reimbursed, final_non_reimbursed) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, act_type, amount_paid, reimbursed_by_secu, base_reimbursement, rate, target_amount_reimbursed,
          real_amount_reimbursed, forfait_participation, non_reimbursed_amount, is_mutuelle, mutuelle_name,
          mutuelle_reimbursed, final_non_reimbursed))
    conn.commit()
    conn.close()

    return jsonify({"message": "Remboursement ajouté avec succès!"}), 201

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
