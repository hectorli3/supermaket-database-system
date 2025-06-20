from app import db

class Product(db.Model):
    __tablename__ = 'products'
    
    product_id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.category_id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.supplier_id'))
    
    # 关系
    inventory = db.relationship('Inventory', backref='product', lazy=True)
    promotion_items = db.relationship('PromotionItem', backref='product', lazy=True)
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)
    
    def to_dict(self):
        return {
            'product_id': self.product_id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'supplier_id': self.supplier_id,
            'category_name': self.category.name if self.category else None,
            'supplier_name': self.supplier.name if self.supplier else None
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'