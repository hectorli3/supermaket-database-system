from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from app import db
from app.models.product import Product

products_ns = Namespace('products', description='商品管理')

@products_ns.route('/')
class ProductList(Resource):
    @jwt_required()
    def get(self):
        """获取所有商品"""
        products = Product.query.all()
        return [product.to_dict() for product in products], 200