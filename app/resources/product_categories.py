from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from app.models.product_category import ProductCategory

categories_ns = Namespace('categories', description='商品分类管理')

@categories_ns.route('/')
class CategoryList(Resource):
    @jwt_required()
    def get(self):
        """获取商品分类"""
        categories = ProductCategory.query.all()
        return [cat.to_dict() for cat in categories], 200 