import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Ini penting untuk mengizinkan permintaan dari domain yang berbeda (misalnya, dari file HTML lokal atau hosting frontend lain)

TRANSACTIONS_FILE = 'transactions.json'

# Fungsi untuk memuat transaksi dari file JSON
def load_transactions():
    try:
        with open(TRANSACTIONS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return [] # Mengembalikan list kosong jika file belum ada

# Fungsi untuk menyimpan transaksi ke file JSON
def save_transactions(transactions):
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(transactions, f, indent=4)

@app.route('/')
def hello_world():
    return 'Hello from Flask!'

@app.route('/process_transaction', methods=['POST'])
def process_transaction():
    data = request.json
    product_name = data.get('product_name')
    quantity = data.get('quantity')
    price_per_unit = data.get('price_per_unit')
    money_received = data.get('money_received')

    if not all([product_name, quantity, price_per_unit, money_received is not None]):
        return jsonify({'error': 'Data tidak lengkap'}), 400

    try:
        quantity = int(quantity)
        price_per_unit = float(price_per_unit)
        money_received = float(money_received)
    except ValueError:
        return jsonify({'error': 'Kuantitas, harga, dan uang diterima harus angka yang valid'}), 400

    total_price = quantity * price_per_unit
    change = money_received - total_price

    # Buat objek transaksi
    transaction = {
        'product_name': product_name,
        'quantity': quantity,
        'price_per_unit': price_per_unit,
        'total_price': total_price,
        'money_received': money_received,
        'change': change,
        'timestamp': request.json.get('timestamp') # Ambil timestamp dari frontend
    }

    transactions = load_transactions()
    transactions.append(transaction)
    save_transactions(transactions)

    return jsonify({'message': 'Transaksi berhasil!', 'change': change}), 200

@app.route('/get_transactions', methods=['GET'])
def get_transactions():
    transactions = load_transactions()
    return jsonify(transactions), 200

@app.route('/delete_transaction/<int:index>', methods=['DELETE'])
def delete_transaction(index):
    transactions = load_transactions()
    if 0 <= index < len(transactions):
        deleted_transaction = transactions.pop(index)
        save_transactions(transactions)
        return jsonify({'message': f'Transaksi {index} berhasil dihapus', 'deleted': deleted_transaction}), 200
    return jsonify({'error': 'Indeks transaksi tidak valid'}), 404

@app.route('/delete_all_transactions', methods=['DELETE'])
def delete_all_transactions():
    save_transactions([]) # Simpan list kosong
    return jsonify({'message': 'Semua riwayat transaksi berhasil dihapus'}), 200
    # Rute untuk menyajikan halaman Pentol.html
@app.route('/Pentol.html')
def serve_pentol_html():
    return send_from_directory('.', 'Pentol.html')

# Rute untuk menyajikan halaman riwayat.html
@app.route('/riwayat.html')
def serve_riwayat_html():
    return send_from_directory('.', 'riwayat.html')

# Opsional: Jika Anda ingin Pentol.html menjadi halaman utama (saat mengakses hanya URL utama)
@app.route('/')
def serve_index():
    return send_from_directory('.', 'Pentol.html')
    
if __name__ == '__main__':
    # Saat deploy ke Replit atau Railway, port biasanya diset oleh environment variable
    # Pastikan app.py Anda mendengarkan di host '0.0.0.0' agar dapat diakses dari luar
    app.run(host='0.0.0.0', port=5000)
    # Anda juga bisa menggunakan:
    # from os import environ
    # app.run(host='0.0.0.0', port=environ.get('PORT', 5000))
