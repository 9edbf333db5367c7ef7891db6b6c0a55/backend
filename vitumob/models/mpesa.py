from google.appengine.ext import ndb


class MpesaPayment(ndb.Expando):
    # id = ndb.GenericProperty()
    code = ndb.StringProperty()
    phone_no = ndb.StringProperty()
    sender = ndb.StringProperty()
    # recoded_trx_date_time = ndb.DateTimeProperty()
    amount = ndb.FloatProperty(default=0.00)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

# Example Transaction
# id: 1007463342;
# mpesa_code: LCK9ESX4H3;
# mpesa_acc: 26902; order_id
# mpesa_msisdn: 254728444264; phone_no
# mpesa_trx_date_time: 20/3/17 9:07 AM;
# mpesa_sender: FAITH SIGEI;
# mpesa_amt: 32646.0

# https://vitumob.com/mpesa?
# id=59538715&
# orig=MPESA&
# dest=254706513985&
# tstamp=2014-11-11+16%3A55%3A09&
# text=FY69MY145+Confirmed.+on+11%2F11%2F14+at+4%3A54+PM+Ksh4%2C516.00+received+from+MARGARET+WANJIRU+254714236724.+Account+Number+16042+New+Utility+balance+is+Ksh3
# &customer_id=274&
# user=safaricom&
# pass=3EdoRm0XHiUPa7x4&
# routemethod_id=2&
# routemethod_name=HTTP&
# mpesa_code=FY69MY145&
# mpesa_acc=16042&
# mpesa_msisdn=254714236724&
# mpesa_trx_date=11%2F11%2F14&
# mpesa_trx_time=4%3A54+PM&
# mpesa_amt=4516.0&
# mpesa_sender=MARGARET+WANJIRU&
# business_number=8238238
