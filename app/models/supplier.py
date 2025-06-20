from app import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    supplier_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.Text)
    
    # 关系
    products = db.relationship('Product', backref='supplier', lazy=True)
    
    def to_dict(self):
        return {
            'supplier_id': self.supplier_id,
            'name': self.name,
            'contact_info': self.contact_info
        }
    
    def __repr__(self):
        return f'<Supplier {self.name}>' 