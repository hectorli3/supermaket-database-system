from app import db

class Store(db.Model):
    __tablename__ = 'stores'
    
    store_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    
    # 关系
    users = db.relationship('User', backref='store', lazy=True)
    work_logs = db.relationship('WorkLog', backref='store', lazy=True)
    inventory = db.relationship('Inventory', backref='store', lazy=True)
    sales = db.relationship('Sale', backref='store', lazy=True)
    
    def to_dict(self):
        return {
            'store_id': self.store_id,
            'name': self.name,
            'address': self.address
        }
    
    def __repr__(self):
        return f'<Store {self.name}>' 