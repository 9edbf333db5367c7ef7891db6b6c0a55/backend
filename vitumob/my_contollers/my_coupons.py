import json
from datetime import datetime

from flask import Blueprint, Response
from mongoengine import *

from ..my_models.my_coupon import Coupon
from ..utils.my_coupon import coupon_codes

coupon = Blueprint("coupon", __name__)

@coupons.route("/coupons", methods=["POST"])
def dump_coupons():
    """migrate all the coupons to the mongo DB"""
    def build_coupon_map(coupon):
        cpn = {
            "code" : coupon["gift_code"],
            "multiple_use" : True if coupon["multi_use"] == "yes" else False,
            "used" : int(coupon["used"]) if coupon["used"] else 0,
            "comment" : coupon["comments"],
            "expiration_date" : datetime.strptime(coupon["expiration_date"], "%Y-%m-%d")
        }
        cpn["percent"] = float(coupon["gift_percent"]) \
            if coupon["gift_percent"] is not None and len(coupon["gift_percent"]) > 0 else None
        cpn["amount"] = float(coupon["gift_amount"]) / 100 \
            if coupon["gift_amount"] is not None and len(coupon["gift_amount"]) > 0 else None
        return cpn
    cp_codes = map(build_coupon_map, coupon_codes)

    cp_codes = [Coupon(**cpn) for cpn in cp_codes]
    coupon_keys = client.put_multi(cp_codes)

    payload = {}
    payload["ids"] = [cpn.urlsafe() for cpn in coupon_keys]
    return Response(json.dumps(payload), status=200, mimetype="application/json")
