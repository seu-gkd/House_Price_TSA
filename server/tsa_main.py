#coding=utf-8
import os
from fbprophet import Prophet
from flask import Flask
from sqlalchemy import create_engine
import pandas as pd
import json
from msg import Message
import urllib
import chardet
db_info = {'user':'root',
    'password':'gkd123,.',
    'host':'47.101.44.55',
    'database':'Houseprice'
}
engine = create_engine('mysql+pymysql://%(user)s:%(password)s@%(host)s/%(database)s?charset=utf8' % db_info,encoding='utf-8')
app = Flask(__name__)
@app.route('/hello/<province>&<city>&<region>')
def hello_world(province, city, region):
    return 'Hello World!' + province + city + region


@app.route('/tsa/<province>&<city>&<region>')
def get_tsa(province, city, region):
    try:
        province = str(province).decode('string-escape')
        city = str(city).decode('string-escape')
        region = str(region).decode('string-escape')
        print('province:{0}, city:{1}, region:{2}'.format(province, city, region))
    except:
        pass
    try:
        province = urllib.parse.unquote(province)
        city = urllib.parse.unquote(city)
        region = urllib.parse.unquote(region)
        print('province:{0}, city:{1}, region:{2}'.format(province,city,region))
    except:
        msg = Message(1, 'error')
        return json.dumps(msg.__dict__, ensure_ascii=False)
    try:
        f = open(os.getcwd() + '/data/{0}{1}{2}.json'.format(province,city,region), 'r', encoding='utf-8')
        t = json.load(f)
        f.close()
        return str(t)
    except:
        sql = "SELECT * from pricehistorynew where province = '{0}' AND city = '{1}' AND citylevel = '{2}'".format(province,city,region)
        try:
            data = pd.read_sql_query(sql.format(region), con=engine, index_col=None, coerce_float=True, params=None,
                                    parse_dates=None, chunksize=None)
        except:
            msg = Message(1,'error')
            return json.dumps(msg.__dict__, ensure_ascii=False)
        data['mouth'] = pd.to_datetime(data['mouth'])
        data.columns = ['year', 'ds', 'province', 'city', 'citylevel', 'longitude', 'twist', 'y',
                        'proportion', 'inc', 'inc_2', 'pricehistoryId']
        m = Prophet(seasonality_mode='multiplicative')
        m.fit(data)
        future = m.make_future_dataframe(periods=3652)
        fcst = m.predict(future)
        province = str(data[2:3]['province'].values).split("'")[1]
        city = str(data[2:3]['city'].values).split("'")[1]
        citylevel = str(data[2:3]['citylevel'].values).split("'")[1]
        msg = Message()
        msg.set_location(province, city, citylevel)
        for index, row in fcst.iterrows():
            t = str(row['ds']).split(' ')[0].split('-')
            if t[-1] == '01':
                time = t[0] + '-' + t[1]
                price_upper = str(round(row['yhat_upper'], 4))
                price_lower = str(round(row['yhat_lower'], 4))
                price = str(round(row['yhat'], ))
                msg.add_price(time, price_upper, price_lower, price)
        with open(os.getcwd() + '/data/{0}{1}{2}.json'.format(province,city,region), 'w+', encoding='utf-8') as f:
            f.write(json.dumps(msg.__dict__, ensure_ascii=False))
        return json.dumps(msg.__dict__, ensure_ascii=False)



if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run()
    # get_tsa('朝阳')

    # http://10.6.207.179:5000/tsa/<province>&<city>&<region>