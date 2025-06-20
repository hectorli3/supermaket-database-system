from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.inventory import Inventory

sales_ns = Namespace('sales', description='销售管理')

sale_item_model = sales_ns.model('SaleItem', {
    'product_id': fields.Integer(required=True, description='商品ID'),
    'quantity': fields.Integer(required=True, description='数量'),
    'price_per_unit': fields.Float(required=True, description='单价')
})

sale_model = sales_ns.model('Sale', {
    'store_id': fields.Integer(required=True, description='门店ID'),
    'items': fields.List(fields.Nested(sale_item_model), required=True, description='销售商品列表'),
    'total_amount': fields.Float(required=True, description='总金额')
})

@sales_ns.route('/')
class SaleList(Resource):
    @jwt_required()
    def get(self):
        """获取销售记录"""
        sales = Sale.query.all()
        return [sale.to_dict() for sale in sales], 200
    
    @sales_ns.expect(sale_model)
    @jwt_required()
    def post(self):
        """创建销售记录"""
        data = request.get_json()
        cashier_id = get_jwt_identity()
        
        # 创建销售记录
        sale = Sale(
            store_id=data['store_id'],
            cashier_id=cashier_id,
            total_amount=data['total_amount']
        )
        db.session.add(sale)
        db.session.flush()  # 获取sale_id
        
        # 创建销售项目并更新库存
        for item_data in data['items']:
            sale_item = SaleItem(
                sale_id=sale.sale_id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                price_per_unit=item_data['price_per_unit']
            )
            db.session.add(sale_item)
            
            # 更新库存
            inventory = Inventory.query.filter_by(
                product_id=item_data['product_id'],
                store_id=data['store_id']
            ).first()
            if inventory:
                inventory.quantity -= item_data['quantity']
        
        db.session.commit()
        return sale.to_dict(), 201 