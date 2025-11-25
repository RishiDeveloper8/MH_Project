from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    occupation = db.Column(db.String(120))
    mobile = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    bills = db.relationship('Bill', backref='user', lazy=True)
    saving_goals = db.relationship('SavingGoal', backref='user', lazy=True)

class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Bill(db.Model):
    __tablename__ = "bills"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bill_type = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)   # reference date (next due origin)
    time_period = db.Column(db.String(20))  # daily/weekly/monthly/quarterly/yearly
    priority = db.Column(db.Integer, default=2)  # 1 high,2 medium,3 low
    is_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SavingGoal(db.Model):
    __tablename__ = "saving_goals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    committed_date = db.Column(db.DateTime, default=datetime.utcnow)
    target_months = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SavingContribution(db.Model):
    __tablename__ = "saving_contributions"
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('saving_goals.id'), nullable=False)
    month_index = db.Column(db.Integer, nullable=False)  # 1..target_months
    contributed = db.Column(db.Boolean, default=False)
    contributed_amount = db.Column(db.Float, default=0.0)
    recorded_at = db.Column(db.DateTime)
