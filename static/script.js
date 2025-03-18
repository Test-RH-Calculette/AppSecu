document.getElementById('reimbursed_by_secu').addEventListener('change', function() {
    document.getElementById('secu-fields').style.display = this.checked ? 'block' : 'none';
});

document.getElementById('is_mutuelle').addEventListener('change', function() {
    document.getElementById('mutuelle-fields').style.display = this.checked ? 'block' : 'none';
});

document.getElementById('reimbursement-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const data = {
        date: document.getElementById('date').value,
        act_type: document.getElementById('act_type').value,
        amount_paid: document.getElementById('amount_paid').value,
        reimbursed_by_secu: document.getElementById('reimbursed_by_secu').checked,
        base_reimbursement: document.getElementById('base_reimbursement').value || 0,
        rate: document.getElementById('rate').value || 0,
        real_amount_reimbursed: document.getElementById('real_amount_reimbursed').value || 0,
        forfait_participation: document.getElementById('forfait_participation').value || 0,
        is_mutuelle: document.getElementById('is_mutuelle').checked,
        mutuelle_name: document.getElementById('mutuelle_name').value || '',
        mutuelle_reimbursed: document.getElementById('mutuelle_reimbursed').value || 0
    };

    fetch('/add_reimbursement', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(response => response.json())
      .then(data => { document.getElementById('message').innerText = data.message; })
      .catch(error => console.error('Erreur:', error));
});
