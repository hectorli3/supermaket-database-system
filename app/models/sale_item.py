from app import db

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    
    item_id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.sale_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    
    def to_dict(self):
        return {
            'item_id': self.item_id,
            'sale_id': self.sale_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price_per_unit': float(self.price_per_unit),
            'total_price': float(self.price_per_unit * self.quantity),
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None
        }
    
    def __repr__(self):
        return f'<SaleItem {self.item_id}>' 