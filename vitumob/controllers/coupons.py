import json
from datetime import datetime

from flask import Blueprint, Response
from google.appengine.ext import ndb

from ..models.coupon import Coupon
from ..utils.coupons import coupon_codes


coupons = Blueprint('coupons', __name__)


@coupons.route('/coupons/migrate', methods=['POST'])
def dump_coupons():
    """Migrate all the coupons to the Datastore DB"""
    def build_coupon_map(coupon):
        cpn = {
            'code': coupon['gift_code'],
            'multiple_use': True if coupon['multi_use'] == 'yes' else False,
            'used': int(coupon['used']) if coupon['used'] else 0,
            'comment': coupon['comments'],
            'expiration_date': datetime.strptime(coupon['expiration_date'], "%Y-%m-%d")
        }
        cpn['percent'] = float(coupon['gift_percent']) \
            if coupon['gift_percent'] is not None and len(coupon['gift_percent']) > 0 else None
        cpn['amount'] = float(coupon['gift_amount']) / 100 \
            if coupon['gift_amount'] is not None and len(coupon['gift_amount']) > 0 else None
        return cpn

    cpn_codes = map(build_coupon_map, coupon_codes)

    cpn_codes = [Coupon(**cpn) for cpn in cpn_codes]
    coupon_keys = ndb.put_multi(cpn_codes)
    # print[cpn.urlsafe() for cpn in coupon_keys]

    payload = {}
    payload['ids'] = [cpn.urlsafe() for cpn in coupon_keys]
    return Response(json.dumps(payload), status=200, mimetype='application/json')
