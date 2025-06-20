from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from app.models.promotion import Promotion

promotions_ns = Namespace('promotions', description='促销管理')

@promotions_ns.route('/')
class PromotionList(Resource):
    @jwt_required()
    def get(self):
        """获取促销列表"""
        promotions = Promotion.query.all()
        return [promo.to_dict() for promo in promotions], 200