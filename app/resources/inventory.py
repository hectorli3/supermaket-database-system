from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from app.models.inventory import Inventory

inventory_ns = Namespace('inventory', description='库存管理')

@inventory_ns.route('/')
class InventoryList(Resource):
    @jwt_required()
    def get(self):
        """获取库存列表"""
        inventory = Inventory.query.all()
        return {'inventory': [item.to_dict() for item in inventory]}, 200 