# Mise à jour de l'application pour inclure la gestion de la mutuelle et l'affichage des graphiques et des actes non remboursés.

import os

# Mise à jour du projet
updated_project_structure = {
    "AppSecu": {
        "app.py": """\
from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

app = Flask(__name__)

# Création de la base de données
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
            base_reimbursement REAL,
            rate REAL,
            amount_reimbursed REAL,
            real_amount_reimbursed REAL,
            forfait_participation REAL,
            non_reimbursed_amount REAL,
            is_mutuelle BOOLEAN,
            mutuelle_name TEXT,
            mutuelle_reimbursed REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_reimbursement', methods=['POST'])
def add_reimbursement():
    data = request.json
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    act_type = data['act_type']
    amount_paid = float(data['amount_paid'])
    base_reimbursement = float(data['base_reimbursement'])
    rate = float(data['rate'])

    amount_reimbursed = (base_reimbursement * rate) / 100
    real_amount_reimbursed = float(data['real_amount_reimbursed'])
    forfait_participation = float(data['forfait_participation'])
    non_reimbursed_amount = amount_paid - real_amount_reimbursed - forfait_participation

    is_mutuelle = data['is_mutuelle']
    mutuelle_name = data['mutuelle_name'] if is_mutuelle else None
    mutuelle_reimbursed = float(data['mutuelle_reimbursed']) if is_mutuelle else 0.0
    non_reimbursed_amount -= mutuelle_reimbursed

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reimbursements 
        (date, act_type, amount_paid, base_reimbursement, rate, amount_reimbursed, real_amount_reimbursed, forfait_participation, non_reimbursed_amount, is_mutuelle, mutuelle_name, mutuelle_reimbursed) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, act_type, amount_paid, base_reimbursement, rate, amount_reimbursed, real_amount_reimbursed, forfait_participation, non_reimbursed_amount, is_mutuelle, mutuelle_name, mutuelle_reimbursed))
    conn.commit()
    conn.close()

    return jsonify({"message": "Remboursement ajouté avec succès!"}), 201

@app.route('/get_reimbursements', methods=['GET'])
def get_reimbursements():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reimbursements ORDER BY date DESC')
    reimbursements = cursor.fetchall()
    conn.close()
    return jsonify(reimbursements)

@app.route('/get_unreimbursed', methods=['GET'])
def get_unreimbursed():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reimbursements WHERE real_amount_reimbursed = 0 AND mutuelle_reimbursed = 0")
    unreimbursed = cursor.fetchall()
    conn.close()
    return jsonify(unreimbursed)

@app.route('/chart.png')
def chart():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT date, non_reimbursed_amount FROM reimbursements")
    data = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(data, columns=['date', 'non_reimbursed_amount'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.groupby(df['date'].dt.strftime('%Y-%m'))['non_reimbursed_amount'].sum()

    plt.figure(figsize=(8,4))
    plt.plot(df.index, df.values, marker='o', linestyle='-')
    plt.xlabel('Mois')
    plt.ylabel('Reste à charge (€)')
    plt.title('Reste à charge total par mois')
    plt.xticks(rotation=45)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')

@app.route('/report')
def report():
    return render_template('report.html')

if __name__ == '__main__':
    app.run(debug=True)
""",
        "templates": {
            "index.html": """\
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Suivi des remboursements médicaux</title>
    <script defer src="/static/script.js"></script>
</head>
<body>
    <h1>Suivi des remboursements médicaux</h1>
    <form id="reimbursement-form">
        <label>Date: <input type="date" id="date"></label><br>
        <label>Type d’acte médical: <input type="text" id="act_type"></label><br>
        <label>Montant payé: <input type="number" id="amount_paid"></label><br>
        <label>Base de remboursement: <input type="number" id="base_reimbursement"></label><br>
        <label>Taux de remboursement (%): <input type="number" id="rate"></label><br>
        <label>Montant réellement versé: <input type="number" id="real_amount_reimbursed"></label><br>
        <label>Participation forfaitaire: <input type="number" id="forfait_participation"></label><br>
        <label>Mutuelle utilisée ? <input type="checkbox" id="is_mutuelle"></label><br>
        <div id="mutuelle-fields" style="display: none;">
            <label>Nom de la mutuelle: <input type="text" id="mutuelle_name"></label><br>
            <label>Montant remboursé par la mutuelle: <input type="number" id="mutuelle_reimbursed"></label><br>
        </div>
        <button type="submit">Ajouter</button>
    </form>
    <div id="message"></div>
</body>
</html>
""",
            "report.html": """\
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapports de remboursements</title>
    <script defer src="/static/report.js"></script>
</head>
<body>
    <h1>Rapports des remboursements</h1>
    <img src="/chart.png" alt="Graphique des restes à charge">
    <h2>Actes non remboursés</h2>
    <ul id="unreimbursed-list"></ul>
</body>
</html>
"""
        }
    }
}

# Création et mise à jour des fichiers
for folder, content in updated_project_structure.items():
    for file, code in content.items():
        if isinstance(code, dict):
            os.makedirs(os.path.join(folder, file), exist_ok=True)
            for sub_file, sub_code in code.items():
                with open(os.path.join(folder, file, sub_file), "w", encoding="utf-8") as f:
                    f.write(sub_code)
        else:
            with open(os.path.join(folder, file), "w", encoding="utf-8") as f:
                f.write(code)

"Application mise à jour avec succès !"
