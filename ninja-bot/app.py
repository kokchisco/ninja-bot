from flask import Flask, render_template, request, jsonify
import sqlite3
import random

app = Flask(__name__)

# Set up the database to store user info, trades, etc.
def init_db():
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    # Table for users (balance, demo balance, VIP status, etc.)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, balance REAL, demo_balance REAL, vip INTEGER, password TEXT, wallet TEXT, wallet_type TEXT, referral_level INTEGER)''')
    # Table for trades (to track buy/sell results)
    c.execute('''CREATE TABLE IF NOT EXISTS trades (
        user_id INTEGER, amount REAL, type TEXT, profit REAL, result TEXT, timestamp TEXT)''')
    # Table for withdrawals
    c.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
        user_id INTEGER, amount REAL, wallet TEXT, wallet_type TEXT, status TEXT, timestamp TEXT)''')
    # Table for deposits
    c.execute('''CREATE TABLE IF NOT EXISTS deposits (
        user_id INTEGER, amount REAL, timestamp TEXT)''')
    # Table for promo codes
    c.execute('''CREATE TABLE IF NOT EXISTS promo_codes (
        code TEXT, amount REAL, total_limit INTEGER, user_limit INTEGER, used INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# Main page
@app.route('/')
def index():
    user_id = request.args.get('user_id', '1')  # Get user ID from Telegram
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    # Check if user exists, if not, create with $10 welcome bonus
    c.execute("SELECT balance, demo_balance, vip, wallet, wallet_type FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (id, balance, demo_balance, vip, password, wallet, wallet_type, referral_level) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (user_id, 10.0, 1000.0, 0, "default123", "", "", 0))
        user = (10.0, 1000.0, 0, "", "")
    balance, demo_balance, vip, wallet, wallet_type = user
    conn.close()
    return render_template('index.html', user_id=user_id, balance=balance, demo_balance=demo_balance, vip=vip, wallet=wallet, wallet_type=wallet_type)

# Switch between demo and real accounts
@app.route('/switch_account', methods=['POST'])
def switch_account():
    user_id = request.form['user_id']
    account_type = request.form['type']
    return jsonify({'status': 'success', 'type': account_type})

# Handle trades
@app.route('/trade', methods=['POST'])
def trade():
    user_id = request.form['user_id']
    amount = float(request.form['amount'])
    trade_type = request.form['type']
    account_type = request.form['account_type']
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    c.execute("SELECT vip, balance, demo_balance FROM users WHERE id = ?", (user_id,))
    vip, balance, demo_balance = c.fetchone()
    # Win probabilities
    win_prob = 0.85 if account_type == 'demo' else (0.50 if vip else 0.25)
    profit = amount * 0.30 if random.random() < win_prob else -amount * 0.10
    if account_type == 'demo':
        c.execute("UPDATE users SET demo_balance = demo_balance + ? WHERE id = ?", (profit, user_id))
        new_balance = demo_balance + profit
    else:
        c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (profit, user_id))
        new_balance = balance + profit
    c.execute("INSERT INTO trades (user_id, amount, type, profit, result, timestamp) VALUES (?, ?, ?, ?, ?, datetime('now'))",
              (user_id, amount, trade_type, profit, "Win" if profit > 0 else "Loss"))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'new_balance': new_balance, 'profit': profit, 'result': "Win" if profit > 0 else "Loss"})

# Handle withdrawals
@app.route('/withdraw', methods=['POST'])
def withdraw():
    user_id = request.form['user_id']
    amount = float(request.form['amount'])
    wallet = request.form['wallet']
    wallet_type = request.form['wallet_type']
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = c.fetchone()[0]
    if amount > balance or wallet == "":
        return jsonify({'status': 'error', 'message': 'Insufficient funds or no wallet'})
    c.execute("INSERT INTO withdrawals (user_id, amount, wallet, wallet_type, status, timestamp) VALUES (?, ?, ?, ?, ?, datetime('now'))",
              (user_id, amount, wallet, wallet_type, 'pending'))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Handle deposits
@app.route('/deposit', methods=['POST'])
def deposit():
    user_id = request.form['user_id']
    amount = float(request.form['amount'])
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    c.execute("INSERT INTO deposits (user_id, amount, timestamp) VALUES (?, ?, datetime('now'))", (user_id, amount))
    # Referral commissions
    c.execute("SELECT referral_level FROM users WHERE id = ?", (user_id,))
    level = c.fetchone()[0]
    if level == 1:
        referrer_id = user_id  # Simplified; in production, track upline
        c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount * 0.10, referrer_id))
    elif level == 2:
        referrer_id = user_id  # Simplified
        c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount * 0.05, referrer_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Admin panel
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    user_id = request.args.get('user_id', '1')
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    c.execute("SELECT vip FROM users WHERE id = ?", (user_id,))
    if c.fetchone()[0] != 1:
        return "Unauthorized"
    if request.method == 'POST':
        action = request.form['action']
        if action == 'approve_withdrawal':
            withdrawal_id = request.form['id']
            method = request.form['method']
            if method == 'oxapay':
                # Placeholder for OxaPay API integration
                c.execute("UPDATE withdrawals SET status = 'approved' WHERE id = ?", (withdrawal_id,))
            else:
                c.execute("UPDATE withdrawals SET status = 'approved' WHERE id = ?", (withdrawal_id,))
            conn.commit()
        elif action == 'set_vip':
            target_id = request.form['target_id']
            c.execute("UPDATE users SET vip = 1 WHERE id = ?", (target_id,))
            conn.commit()
        elif action == 'add_promo':
            code = request.form['code']
            amount = float(request.form['amount'])
            total_limit = int(request.form['total_limit'])
            user_limit = int(request.form['user_limit'])
            c.execute("INSERT INTO promo_codes (code, amount, total_limit, user_limit, used) VALUES (?, ?, ?, ?, 0)",
                      (code, amount, total_limit, user_limit))
            conn.commit()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM trades")
    trades = c.fetchall()
    c.execute("SELECT * FROM withdrawals")
    withdrawals = c.fetchall()
    c.execute("SELECT * FROM deposits")
    deposits = c.fetchall()
    conn.close()
    return render_template('admin.html', users=users, trades=trades, withdrawals=withdrawals, deposits=deposits)

# Reset demo balance
@app.route('/reset_demo', methods=['POST'])
def reset_demo():
    user_id = request.form['user_id']
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    c.execute("UPDATE users SET demo_balance = 1000 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Change password
@app.route('/change_password', methods=['POST'])
def change_password():
    user_id = request.form['user_id']
    new_password = request.form['password']
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    c.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Transfer money
@app.route('/transfer', methods=['POST'])
def transfer():
    user_id = request.form['user_id']
    target_id = request.form['target_id']
    amount = float(request.form['amount'])
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = c.fetchone()[0]
    if balance >= amount:
        c.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
        c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, target_id))
        conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Daily check-in
@app.route('/check_in', methods=['POST'])
def check_in():
    user_id = request.form['user_id']
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Apply promo code
@app.route('/promo', methods=['POST'])
def promo():
    user_id = request.form['user_id']
    code = request.form['code']
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    c.execute("SELECT amount, total_limit, user_limit, used FROM promo_codes WHERE code = ?", (code,))
    promo = c.fetchone()
    if promo and promo[3] < promo[2]:
        c.execute("UPDATE promo_codes SET used = used + 1 WHERE code = ?", (code,))
        c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (promo[0], user_id))
        conn.commit()
        return jsonify({'status': 'success', 'amount': promo[0]})
    return jsonify({'status': 'error', 'message': 'Invalid or expired code'})

# Set wallet
@app.route('/set_wallet', methods=['POST'])
def set_wallet():
    user_id = request.form['user_id']
    wallet = request.form['wallet']
    wallet_type = request.form['wallet_type']
    conn = sqlite3.connect('ninja.db')
    c = conn.cursor()
    c.execute("UPDATE users SET wallet = ?, wallet_type = ? WHERE id = ?", (wallet, wallet_type, user_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)