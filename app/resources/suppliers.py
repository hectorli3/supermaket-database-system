from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from app.models.supplier import Supplier

suppliers_ns = Namespace('suppliers', description='供应商管理')

@suppliers_ns.route('/')
class SupplierList(Resource):
    @jwt_required()
    def get(self):
        """获取供应商列表"""
        suppliers = Supplier.query.all()
        return [supplier.to_dict() for supplier in suppliers], 200