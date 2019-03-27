import pandas as pd
from fbprophet import Prophet
from sqlalchemy import create_engine
import pandas as pd
import json
from msg import Message
import os
db_info = {'user':'root',
    'password':'gkd123,.',
    'host':'47.101.44.55',
    'database':'Houseprice'
}
engine = create_engine('mysql+pymysql://%(user)s:%(password)s@%(host)s/%(database)s?charset=utf8' % db_info,encoding='utf-8')

def hello_world(name):
    return 'Hello World!' + name


def get_tsa(region):
    sql = "select * from pricehistorynew where citylevel = '{0}'"
    data = pd.read_sql_query(sql.format(region), con = engine, index_col=None, coerce_float=True, params=None, parse_dates=None,chunksize=None)
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
    with open('test.json','a+',encoding='utf-8') as f:
        f.write(json.dumps(msg.__dict__))
    return json.dumps(msg.__dict__)

def test():
    province = '江苏'
    city = '南京'
    region = '江宁'

    sql = "SELECT * from pricehistorynew where province = '{0}' AND city = '{1}' AND citylevel = '{2}'".format(
        province, city, region)
    try:
        data = pd.read_sql_query(sql.format(region), con=engine, index_col=None, coerce_float=True, params=None,
                                 parse_dates=None, chunksize=None)
    except:
        msg = Message(1, 'error')
        return json.dumps(msg.__dict__, ensure_ascii=False).replace("'", '"')
    data['mouth'] = pd.to_datetime(data['mouth'])
    data.columns = ['year', 'ds', 'province', 'city', 'citylevel', 'longitude', 'twist', 'y',
                    'proportion', 'inc', 'inc_2', 'pricehistoryId']
    m = Prophet()
    m.fit(data)
    future = m.make_future_dataframe(periods=3652)
    fcst = m.predict(future)
    pic = m.plot(fcst)
    pic.savefig('tt.png')


if __name__ == '__main__':
    # get_tsa('朝阳')
    test()
