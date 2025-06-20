from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from app import db
from app.models.store import Store

stores_ns = Namespace('stores', description='门店管理')

store_model = stores_ns.model('Store', {
    'name': fields.String(required=True, description='门店名称'),
    'address': fields.String(description='门店地址')
})

@stores_ns.route('/')
class StoreList(Resource):
    @jwt_required()
    def get(self):
        """获取所有门店"""
        stores = Store.query.all()
        return [store.to_dict() for store in stores], 200
    
    @stores_ns.expect(store_model)
    @jwt_required()
    def post(self):
        """创建新门店"""
        data = request.get_json()
        store = Store(name=data['name'], address=data.get('address'))
        db.session.add(store)
        db.session.commit()
        return store.to_dict(), 201

@stores_ns.route('/<int:store_id>')
class StoreDetail(Resource):
    @jwt_required()
    def get(self, store_id):
        """获取门店详情"""
        store = Store.query.get_or_404(store_id)
        return store.to_dict(), 200
    
    @stores_ns.expect(store_model)
    @jwt_required()
    def put(self, store_id):
        """更新门店信息"""
        store = Store.query.get_or_404(store_id)
        data = request.get_json()
        store.name = data.get('name', store.name)
        store.address = data.get('address', store.address)
        db.session.commit()
        return store.to_dict(), 200
    
    @jwt_required()
    def delete(self, store_id):
        """删除门店"""
        store = Store.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {'message': '门店删除成功'}, 200 