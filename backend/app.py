from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Transaction, Bill, SavingGoal, SavingContribution
from config import Config
from datetime import datetime, timedelta, date
import math

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'signin'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- Pages ----------
@app.route('/')
def home():
    return redirect(url_for('signin'))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template('signin.html')
    # POST:
    data = request.form
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('signin.html', error="Invalid username/password")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    data = request.form
    username = data.get('username')
    occupation = data.get('occupation')
    mobile = data.get('mobile')
    email = data.get('email')
    password = data.get('password')
    if User.query.filter((User.username==username)|(User.email==email)).first():
        return render_template('signup.html', error="Username or Email already exists")
    user = User(username=username, occupation=occupation, mobile=mobile, email=email,
                password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect(url_for('dashboard'))

@app.route('/signout')
@login_required
def signout():
    logout_user()
    return redirect(url_for('signin'))

# ---------- Dashboard ----------
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# ---------- Transactions History page ----------
@app.route('/transactions')
@login_required
def transactions_page():
    return render_template('transactions.html')

# ---------- Bills page ----------
@app.route('/bills')
@login_required
def bills_page():
    return render_template('bills.html')

# ---------- Goals page ----------
@app.route('/goals')
@login_required
def goals_page():
    return render_template('goals.html')

# ---------- Advisor page ----------
@app.route('/advisor')
@login_required
def advisor_page():
    return render_template('advisor.html')

# ---------- Learning page ----------
@app.route('/learning')
@login_required
def learning_page():
    return render_template('learning.html')

# ---------- API Endpoints ----------

# Add transaction
@app.route('/api/transaction', methods=['POST'])
@login_required
def api_add_transaction():
    data = request.get_json()
    ttype = data.get('type')
    try:
        amount = float(data.get('amount', 0))
    except:
        return jsonify({'success':False, 'error':'Invalid amount'}), 400
    desc = data.get('description','')
    if ttype not in ('income','expense'):
        return jsonify({'success':False, 'error':'Invalid type'}), 400
    txn = Transaction(user_id=current_user.id, type=ttype, amount=amount, description=desc)
    db.session.add(txn)
    db.session.commit()
    totals = compute_totals(current_user.id)
    return jsonify({'success':True, 'transaction':{
        'id': txn.id,
        'type': txn.type,
        'amount': txn.amount,
        'description': txn.description,
        'timestamp': txn.timestamp.isoformat()
    }, 'totals': totals})

def compute_totals(user_id):
    income = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount),0)).filter_by(user_id=user_id, type='income').scalar() or 0
    expense = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount),0)).filter_by(user_id=user_id, type='expense').scalar() or 0
    net = (income or 0) - (expense or 0)
    return {'total_income': float(income), 'total_expense': float(expense), 'net_balance': float(net)}

# Paginated transactions
@app.route('/api/transactions')
@login_required
def api_transactions():
    page = int(request.args.get('page',1))
    per_page = 15
    q = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc())
    total = q.count()
    items = q.offset((page-1)*per_page).limit(per_page).all()
    data = []
    for it in items:
        data.append({
            'id': it.id, 'type': it.type, 'amount': it.amount,
            'description': it.description, 'timestamp': it.timestamp.isoformat()
        })
    total_pages = math.ceil(total / per_page) if total>0 else 1
    return jsonify({'items': data, 'page': page, 'total_pages': total_pages, 'total': total})

# Chart data (simple last 30 days aggregation)
@app.route('/api/chart-data')
@login_required
def api_chart_data():
    today = date.today()
    days = 30
    labels = []
    expense_series = []
    net_series = []
    running_net = 0
    for i in range(days-1, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime("%Y-%m-%d"))
        inc = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount),0)).filter(Transaction.user_id==current_user.id, Transaction.type=='income', db.func.date(Transaction.timestamp)==d).scalar() or 0
        exp = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount),0)).filter(Transaction.user_id==current_user.id, Transaction.type=='expense', db.func.date(Transaction.timestamp)==d).scalar() or 0
        running_net += float(inc) - float(exp)
        expense_series.append(float(exp))
        net_series.append(float(running_net))
    return jsonify({'labels': labels, 'expense': expense_series, 'net_balance': net_series})

# Bills: add
@app.route('/api/bill', methods=['POST'])
@login_required
def api_add_bill():
    data = request.get_json()
    bill_type = data.get('bill_type')
    try:
        amount = float(data.get('amount', 0))
    except:
        return jsonify({'success':False, 'error':'Invalid amount'}), 400
    date_str = data.get('date')
    try:
        bill_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        bill_date = date.today()
    period = data.get('time_period','monthly')
    priority = int(data.get('priority',2))
    bill = Bill(user_id=current_user.id, bill_type=bill_type, amount=amount, date=bill_date, time_period=period, priority=priority)
    db.session.add(bill)
    db.session.commit()
    return jsonify({'success':True, 'bill': {'id': bill.id, 'bill_type': bill.bill_type, 'amount': bill.amount, 'date': bill.date.isoformat(), 'time_period': bill.time_period, 'priority': bill.priority}})

# Bills: list + upcoming
@app.route('/api/bills')
@login_required
def api_bills():
    bills = Bill.query.filter_by(user_id=current_user.id).order_by(Bill.priority.asc(), Bill.date.asc()).all()
    today = date.today()
    upcoming = []
    all_b = []
    for b in bills:
        next_due = compute_next_due(b.date, b.time_period, today)
        rec = {'id': b.id, 'bill_type': b.bill_type, 'amount': b.amount, 'date': b.date.isoformat(), 'time_period': b.time_period, 'priority': b.priority, 'is_paid': b.is_paid, 'next_due': next_due.isoformat()}
        all_b.append(rec)
        if not b.is_paid and (next_due - today).days <= 5 and (next_due - today).days >= 0:
            upcoming.append(rec)
    return jsonify({'all': all_b, 'upcoming': upcoming})

def compute_next_due(base_date, period, today):
    # start from base_date and advance until >= today
    d = base_date
    if d >= today:
        return d
    while d < today:
        if period == 'daily':
            d = d + timedelta(days=1)
        elif period == 'weekly':
            d = d + timedelta(weeks=1)
        elif period == 'monthly':
            # naive month add: add 30 days (simple)
            d = d + timedelta(days=30)
        elif period == 'quarterly':
            d = d + timedelta(days=90)
        elif period == 'yearly':
            d = d + timedelta(days=365)
        else:
            d = d + timedelta(days=30)
    return d

# Mark bill paid
@app.route('/api/bill/<int:bill_id>/paid', methods=['POST'])
@login_required
def api_bill_paid(bill_id):
    b = Bill.query.get_or_404(bill_id)
    if b.user_id != current_user.id:
        return jsonify({'success':False}), 403
    b.is_paid = True
    db.session.commit()
    return jsonify({'success':True})

# Delete bill
@app.route('/api/bill/<int:bill_id>', methods=['DELETE'])
@login_required
def api_bill_delete(bill_id):
    b = Bill.query.get_or_404(bill_id)
    if b.user_id != current_user.id:
        return jsonify({'success':False}), 403
    db.session.delete(b)
    db.session.commit()
    return jsonify({'success':True})

# Saving Goals
@app.route('/api/goal', methods=['POST'])
@login_required
def api_add_goal():
    data = request.get_json()
    name = data.get('name')
    try:
        amount = float(data.get('amount', 0))
        months = int(data.get('months', 1))
    except:
        return jsonify({'success':False, 'error':'Invalid input'}), 400
    goal = SavingGoal(user_id=current_user.id, name=name, target_amount=amount, target_months=months)
    db.session.add(goal)
    db.session.commit()
    # create blank contributions
    for i in range(1, months+1):
        sc = SavingContribution(goal_id=goal.id, month_index=i, contributed=False, contributed_amount=0.0)
        db.session.add(sc)
    db.session.commit()
    return jsonify({'success':True, 'goal': {'id': goal.id, 'name': goal.name, 'target_amount': goal.target_amount, 'target_months': goal.target_months}})

@app.route('/api/goals')
@login_required
def api_goals():
    goals = SavingGoal.query.filter_by(user_id=current_user.id).all()
    out = []
    for g in goals:
        contribs = SavingContribution.query.filter_by(goal_id=g.id).order_by(SavingContribution.month_index).all()
        contrib_data = [{'month_index': c.month_index, 'contributed': c.contributed, 'contributed_amount': c.contributed_amount} for c in contribs]
        out.append({'id': g.id, 'name': g.name, 'target_amount': g.target_amount, 'target_months': g.target_months, 'committed_date': g.committed_date.isoformat(), 'contributions': contrib_data})
    return jsonify({'goals': out})

@app.route('/api/goal/<int:goal_id>/contribute', methods=['POST'])
@login_required
def api_contribute(goal_id):
    data = request.get_json()
    month_index = int(data.get('month_index'))
    g = SavingGoal.query.get_or_404(goal_id)
    if g.user_id != current_user.id:
        return jsonify({'success':False}), 403
    sc = SavingContribution.query.filter_by(goal_id=g.id, month_index=month_index).first()
    if not sc:
        return jsonify({'success':False,'error':'Invalid month'}), 400
    sc.contributed = True
    monthly_amount = g.target_amount / max(1, g.target_months)
    sc.contributed_amount = float(monthly_amount)
    sc.recorded_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success':True, 'contributed_amount': sc.contributed_amount})

# Learning: add content (requires secret code)
LEARNING_CODE = "JBMNMJ8"
learning_store = []  # simple in-memory store (hackathon minimal). You can persist to DB later.

@app.route('/api/learning', methods=['GET','POST'])
@login_required
def api_learning():
    if request.method == 'GET':
        return jsonify({'items': learning_store})
    data = request.get_json()
    code = data.get('code')
    if code != LEARNING_CODE:
        return jsonify({'success':False, 'error':'Invalid code'}), 403
    item_type = data.get('type')
    name = data.get('name')
    content = data.get('content')  # summary text or yt link
    image = data.get('image')
    learning_store.append({'type': item_type, 'name': name, 'content': content, 'image': image})
    return jsonify({'success':True})

# Simple API to get totals (dashboard)
@app.route('/api/summary')
@login_required
def api_summary():
    return jsonify(compute_totals(current_user.id))

# ---------- Static run ----------
if __name__ == '__main__':
    # create DB tables if not present
    with app.app_context():
        db.create_all()
    app.run(debug=True)
