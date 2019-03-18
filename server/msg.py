import json
class Message:
    def __init__(self, code=0,msg=None, desc=None):
        self.code = code
        self.msg = msg
        self.desc = desc
        self.data = dict()
        self.data['priceHistory'] = []

    def set_location(self,province,city,citylevel):
        self.data['province'] = province
        self.data['city'] = city
        self.data['citylevel'] = citylevel

    def add_price(self, time, price_upper, price_lower, price):
        d = dict()
        d['time'] = time
        d['price'] = dict()
        d['price']['price_upper'] = price_upper
        d['price']['price_lower'] = price_lower
        d['price']['price'] = price
        self.data['priceHistory'].append(d)

