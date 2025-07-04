from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app) # Mengizinkan CORS untuk semua rute

DATA_FILE = 'transactions.json'

def load_transactions():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_transactions(transactions):
    with open(DATA_FILE, 'w') as f:
        json.dump(transactions, f, indent=4)

@app.route('/save_transaction', methods=['POST'])
def save_transaction():
    try:
        transaction = request.json
        transactions = load_transactions()

        # Periksa apakah transactionId sudah ada untuk menghindari duplikasi
        existing_ids = {t['transactionId'] for t in transactions}
        if transaction['transactionId'] in existing_ids:
            # Jika ID sudah ada, increment sampai menemukan ID yang unik
            new_id = transaction['transactionId']
            while new_id in existing_ids:
                new_id += 1
            transaction['transactionId'] = new_id
            print(f"Duplicate transaction ID found, assigned new ID: {new_id}")


        transactions.append(transaction)
        save_transactions(transactions)
        return jsonify({"message": "Transaction saved successfully", "transactionId": transaction['transactionId']}), 201
    except Exception as e:
        print(f"Error saving transaction: {e}")
        return jsonify({"message": "Failed to save transaction", "error": str(e)}), 500

@app.route('/get_transactions', methods=['GET'])
def get_transactions():
    transactions = load_transactions()
    return jsonify(transactions), 200

@app.route('/delete_transaction/<int:transaction_id>', methods=['DELETE'])
def delete_single_transaction(transaction_id):
    transactions = load_transactions()
    initial_len = len(transactions)
    transactions = [t for t in transactions if t['transactionId'] != transaction_id]
    if len(transactions) < initial_len:
        save_transactions(transactions)
        return jsonify({"message": f"Transaction {transaction_id} deleted successfully"}), 200
    return jsonify({"message": f"Transaction {transaction_id} not found"}), 404

@app.route('/clear_transactions', methods=['DELETE'])
def clear_transactions():
    save_transactions([]) # Simpan list kosong
    return jsonify({"message": "All transactions cleared successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

