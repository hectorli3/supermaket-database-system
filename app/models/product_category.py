from app import db

class ProductCategory(db.Model):
    __tablename__ = 'product_categories'
    
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    
    # 关系
    products = db.relationship('Product', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'category_id': self.category_id,
            'name': self.name
        }
    
    def __repr__(self):
        return f'<ProductCategory {self.name}>' 