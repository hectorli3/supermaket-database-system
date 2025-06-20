from app import db
from datetime import datetime

class Sale(db.Model):
    __tablename__ = 'sales'
    
    sale_id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    cashier_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    sale_timestamp = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # 关系
    sale_items = db.relationship('SaleItem', backref='sale', lazy=True)
    
    def to_dict(self):
        return {
            'sale_id': self.sale_id,
            'store_id': self.store_id,
            'cashier_id': self.cashier_id,
            'sale_timestamp': self.sale_timestamp.isoformat() if self.sale_timestamp else None,
            'total_amount': float(self.total_amount),
            'store_name': self.store.name if self.store else None,
            'cashier_name': self.cashier.username if self.cashier else None,
            'items': [item.to_dict() for item in self.sale_items]
        }
    
    def __repr__(self):
        return f'<Sale {self.sale_id}>'