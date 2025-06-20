from app import db
from datetime import date

class Promotion(db.Model):
    __tablename__ = 'promotions'
    
    promotion_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # 关系
    promotion_items = db.relationship('PromotionItem', backref='promotion', lazy=True)
    
    def is_active(self):
        """检查促销是否有效"""
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    def to_dict(self):
        return {
            'promotion_id': self.promotion_id,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_active': self.is_active()
        }
    
    def __repr__(self):
        return f'<Promotion {self.name}>' 