from app import db

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    inventory_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # 唯一约束
    __table_args__ = (db.UniqueConstraint('product_id', 'store_id'),)
    
    def to_dict(self):
        # 调试信息
        product_obj = getattr(self, 'product', None)
        print(f"库存ID {self.inventory_id}: product对象={product_obj}, product_id={self.product_id}")
        if product_obj:
            print(f"  商品名称={product_obj.name}, SKU={product_obj.sku}")
        
        return {
            'inventory_id': self.inventory_id,
            'product_id': self.product_id,
            'store_id': self.store_id,
            'quantity': self.quantity,
            'price': float(self.price),
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'store_name': self.store.name if self.store else None
        }
    
    def __repr__(self):
        return f'<Inventory {self.inventory_id}>'