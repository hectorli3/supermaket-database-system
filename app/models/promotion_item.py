from app import db

class PromotionItem(db.Model):
    __tablename__ = 'promotion_items'
    
    id = db.Column(db.Integer, primary_key=True)
    promotion_id = db.Column(db.Integer, db.ForeignKey('promotions.promotion_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'promotion_id': self.promotion_id,
            'product_id': self.product_id,
            'promotion_name': self.promotion.name if self.promotion else None,
            'product_name': self.product.name if self.product else None
        }
    
    def __repr__(self):
        return f'<PromotionItem {self.id}>'