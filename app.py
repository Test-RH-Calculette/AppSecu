import os

# Redéfinition de l'ensemble des fichiers du projet après la réinitialisation

project_structure = {
    "med_reimburse_app": {
        "app.py": """\
from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import os

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
""",
        "requirements.txt": """\
flask
gunicorn
""",
        "Procfile": """\
web: gunicorn -w 4 -b 0.0.0.0:5000 app:app
""",
        "static": {
            "script.js": """\
document.getElementById('reimbursed_by_secu').addEventListener('change', function() {
    document.getElementById('secu-fields').style.display = this.checked ? 'block' : 'none';
});

document.getElementById('is_mutuelle').addEventListener('change', function() {
    document.getElementById('mutuelle-fields').style.display = this.checked ? 'block' : 'none';
});

document.getElementById('reimbursement-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const reimbursedBySecu = document.getElementById('reimbursed_by_secu').checked;
    const isMutuelle = document.getElementById('is_mutuelle').checked;
    
    let amountPaid = parseFloat(document.getElementById('amount_paid').value) || 0;
    let baseReimbursement = reimbursedBySecu ? parseFloat(document.getElementById('base_reimbursement').value) || 0 : 0;
    let rate = reimbursedBySecu ? parseFloat(document.getElementById('rate').value) || 0 : 0;
    let realAmountReimbursed = reimbursedBySecu ? parseFloat(document.getElementById('real_amount_reimbursed').value) || 0 : 0;
    let forfaitParticipation = reimbursedBySecu ? parseFloat(document.getElementById('forfait_participation').value) || 0 : 0;
    let mutuelleReimbursed = isMutuelle ? parseFloat(document.getElementById('mutuelle_reimbursed').value) || 0 : 0;

    let targetAmountReimbursed = (baseReimbursement * rate) / 100;
    let nonReimbursedAmount = amountPaid - realAmountReimbursed - forfaitParticipation;
    let finalNonReimbursed = nonReimbursedAmount - mutuelleReimbursed;

    document.getElementById('calculation-result').innerHTML = `
        <h3>Résultats du calcul :</h3>
        <p>Montant versé cible : <strong>${targetAmountReimbursed.toFixed(2)} €</strong></p>
        <p>Différence avec le montant réel versé : <strong>${(realAmountReimbursed - targetAmountReimbursed).toFixed(2)} €</strong></p>
        <p>Reste à charge sans mutuelle : <strong>${nonReimbursedAmount.toFixed(2)} €</strong></p>
        <p>Reste à charge après mutuelle : <strong>${finalNonReimbursed.toFixed(2)} €</strong></p>
    `;

    const data = {
        date: document.getElementById('date').value,
        act_type: document.getElementById('act_type').value,
        amount_paid: amountPaid,
        reimbursed_by_secu: reimbursedBySecu,
        base_reimbursement: baseReimbursement,
        rate: rate,
        real_amount_reimbursed: realAmountReimbursed,
        forfait_participation: forfaitParticipation,
        is_mutuelle: isMutuelle,
        mutuelle_name: isMutuelle ? document.getElementById('mutuelle_name').value : '',
        mutuelle_reimbursed: mutuelleReimbursed
    };

    fetch('/add_reimbursement', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(response => response.json())
      .then(data => { 
          document.getElementById('message').innerText = "Ajout confirmé : " + data.message; 
      })
      .catch(error => console.error('Erreur:', error));
});
"""
        },
        "templates": {
            "index.html": """\
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Suivi des remboursements</title>
    <script defer src="/static/script.js"></script>
</head>
<body>
    <button onclick="location.href='/report'">Voir le suivi</button>
    <h1>Ajout d'un acte médical</h1>
    <form id="reimbursement-form">
        <label>Date: <input type="date" id="date"></label><br>
        <label>Type d’acte médical: <input type="text" id="act_type"></label><br>
        <label>Montant payé: <input type="number" id="amount_paid"></label><br>
        <label>Remboursé par la Sécurité sociale ? <input type="checkbox" id="reimbursed_by_secu"></label><br>
        <div id="secu-fields" style="display: none;">
            <label>Base remboursement: <input type="number" id="base_reimbursement"></label><br>
            <label>Taux (%): <input type="number" id="rate"></label><br>
        </div>
        <button type="submit">Ajouter</button>
    </form>
    <div id="calculation-result"></div>
    <div id="message"></div>
</body>
</html>
"""
        }
    }
}

"Application recréée avec succès !"
