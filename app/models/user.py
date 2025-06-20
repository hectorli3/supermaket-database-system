from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'))
    
    # 关系
    work_logs = db.relationship('WorkLog', backref='user', lazy=True)
    sales = db.relationship('Sale', backref='cashier', lazy=True)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'store_id': self.store_id,
            'store_name': self.store.name if self.store else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>' 