const tg = window.Telegram.WebApp;
tg.expand();
let account_type = 'real';

// Show chart
new Chart(document.getElementById('priceChart'), {
    type: 'line',
    data: {
        labels: ['1D', '1W', '1M'],
        datasets: [{
            label: 'Price',
            data: [58000, 58123, 57900],
            borderColor: 'orange',
            fill: false
        }]
    }
});

// Switch accounts
function switchAccount(type) {
    account_type = type;
    fetch('/switch_account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `user_id=${tg.initDataUnsafe.user.id}&type=${type}`
    }).then(() => {
        document.getElementById('withdrawBtn').style.display = type === 'demo' ? 'none' : 'block';
        document.getElementById('resetBtn').style.display = type === 'demo' ? 'block' : 'none';
    });
}

// Trade
function trade(type) {
    const amount = document.getElementById('amount').value;
    fetch('/trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `user_id=${tg.initDataUnsafe.user.id}&amount=${amount}&type=${type}&account_type=${account_type}`
    })
    .then(res => res.json())
    .then(data => {
        alert(`Trade ${data.result}! Profit: $${data.profit}, New Balance: $${data.new_balance}`);
        location.reload();
    });
}

// Withdraw
function withdraw() {
    const amount = prompt('Enter amount to withdraw');
    const wallet = prompt('Enter wallet address');
    const walletType = prompt('Select wallet type (TRX/USDT-TRC20/USDT-BEP20)');
    fetch('/withdraw', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `user_id=${tg.initDataUnsafe.user.id}&amount=${amount}&wallet=${wallet}&wallet_type=${walletType}`
    })
    .then(res => res.json())
    .then(data => alert(data.status === 'success' ? 'Withdrawal requested' : data.message));
}

// Reset demo balance
function resetDemo() {
    fetch('/reset_demo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `user_id=${tg.initDataUnsafe.user.id}`
    })
    .then(() => location.reload());
}

// Change password
function changePassword() {
    const newPass = prompt('Enter new password');
    fetch('/change_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `user_id=${tg.initDataUnsafe.user.id}&password=${newPass}`
    })
    .then(() => alert('Password changed'));
}

// Transfer money
function transfer() {
    const target_id = prompt('Enter user ID to transfer to');
    const amount = prompt('Enter amount to transfer');
    fetch('/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `user_id=${tg.initDataUnsafe.user.id}&target_id=${target_id}&amount=${amount}`
    })
    .then(() => alert('Transferred'));
}

// Daily check-in
function checkIn() {
    fetch('/check_in', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `user_id=${tg.initDataUnsafe.user.id}`
    })
    .then(() => alert('Checked in, +$1'));
}

// Apply promo code
function applyPromo() {
    const code = document.getElementById('promo').value;
    fetch('/promo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `user_id=${tg.initDataUnsafe.user.id}&code=${code}`
    })
    .then(res => res.json())
    .then(data => alert(data.status === 'success' ? `Bonus: $${data.amount}` : data.message));
}

// Set wallet
function setWallet() {
    const wallet = document.getElementById('wallet').value;
    const walletType = document.getElementById('walletType').value;
    fetch('/set_wallet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `user_id=${tg.initDataUnsafe.user.id}&wallet=${wallet}&wallet_type=${walletType}`
    })
    .then(() => alert('Wallet set'));
}

// Navigation
function showHome() { alert('Home clicked'); }
function showTrade() { alert('Trade clicked'); }
function showActivity() { alert('Activity clicked'); }