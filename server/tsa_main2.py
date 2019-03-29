#coding=utf-8
import os
from fbprophet import Prophet
from flask import Flask, make_response
from sqlalchemy import create_engine
import pandas as pd
import json
from msg import Message
import urllib
from flask_cors import CORS
import requests
import xgboost as xgb
from data import *
db_info = {'user':'root',
    'password':'gkd123,.',
    'host':'47.101.44.55',
    'database':'Houseprice'
}
engine = create_engine('mysql+pymysql://%(user)s:%(password)s@%(host)s/%(database)s?charset=utf8' % db_info,encoding='utf-8')
app = Flask(__name__)
CORS(app, supports_credentials=True)

# @app.route('/loupan/<propertyType>&<landscapingRatio>&<siteArea>&<floorAreaRatio>&<buildingArea>&<yearofpropertyRights>&<parkingRatio>&<propertycosts>&<hospital>&<metro>&<school>&<mall>&<avgprice>')
# def get_loupan(propertyType, landscapingRatio, siteArea, floorAreaRatio, buildingArea, yearofpropertyRights, parkingRatio, propertycosts, hospital, metro, school, mall, avgprice):
#     input = [int(propertyType), float(landscapingRatio), float(siteArea), float(floorAreaRatio), float(buildingArea), float(yearofpropertyRights), float(parkingRatio), float(propertycosts), float(hospital), float(metro), float(school), float(mall), float(avgprice)]
#     x = xgb.DMatrix(input)
#     tar = xgb.Booster(model_file='xgb.model')
#     pre = tar.predict(x)
#     return str(pre[0])

@app.route('/loupan/<propertyType>&<landscapingRatio>&<siteArea>&<floorAreaRatio>&<buildingArea>&<yearofpropertyRights>&<parkingRatio>&<propertycosts>&<lat>&<lng>')
def get_loupan(propertyType, landscapingRatio, siteArea, floorAreaRatio, buildingArea, yearofpropertyRights, parkingRatio, propertycosts, lat, lng):
    ak = 'nVPoiLMEoGMsNp5zsewOhVEfXRydOnyg'
    price_sql = "select regionname,avgprice from regioninfo where cityname='{0}'"
    location = str(lat) + ',' + str(lng)
    nearby_api = 'http://api.map.baidu.com/place/v2/search?query={0}&location={1}&radius=2000&output=json&ak={2}'
    address_api = 'http://api.map.baidu.com/geocoder/v2/?callback=renderReverse&location={0}&output=json&pois=1&latest_admin=1&ak={1}'
    # hospital, metro, school, mall
    params = [0,0,0,0]
    targets = ['医院','地铁站','学校','商场']
    for i in range(len(targets)):
        json_text = requests.get(nearby_api.format(targets[i], location, ak)).text.replace(' ', '').replace('\n', '')
        js = json.loads(json_text)
        params[i] = len(js['results'])
    # avg(price)
    json_text = requests.get(address_api.format(location, ak)).text.split('enderReverse&&renderReverse(')[1][:-1].replace(' ', '').replace('\n', '')
    js = json.loads(json_text)
    address = js['result']['formatted_address']
    price = -1
    for i in cities:
        if i in address:
            data = pd.read_sql_query(price_sql.format(i), con=engine, index_col=None, coerce_float=True, params=None, parse_dates=None, chunksize=None)
            for index, row in data.iterrows():
                if row['regionname'] in address:
                    price = row['avgprice']
    if price == -1:
        msg = Message(1, '没有相应地区的价格信息')
        return json.dumps(msg.__dict__, ensure_ascii=False).replace("'", '"')


    input = [int(propertyType), float(landscapingRatio), float(siteArea), float(floorAreaRatio), float(buildingArea), float(yearofpropertyRights), float(parkingRatio), float(propertycosts), float(params[0]), float(params[1]), float(params[2]), float(params[3]), float(price)]
    x = xgb.DMatrix(input)
    tar = xgb.Booster(model_file='xgb.model')
    pre = tar.predict(x)
    msg = Message(0, 'success')
    msg.add_price('0','0','0',str(pre[0]))
    return json.dumps(msg.__dict__, ensure_ascii=False).replace("'", '"')

@app.route('/tsa/<province>&<city>&<region>')
def get_tsa(province, city, region):
    #         return json.dumps(msg.__dict__, ensure_ascii=False)
    province = urllib.parse.unquote(str(province))
    city = urllib.parse.unquote(str(city))
    region = urllib.parse.unquote(str(region))

    try:
        f = open(os.getcwd() + '/data/{0}{1}{2}.json'.format(province,city,region), 'r', encoding='utf-8')
        t = json.load(f)
        f.close()
        return str(t).replace("'",'"')
    except:
        sql = "SELECT * from pricehistorynew where province = '{0}' AND city = '{1}' AND citylevel = '{2}'".format(province, city, region)
        try:
            data = pd.read_sql_query(sql.format(region), con=engine, index_col=None, coerce_float=True, params=None,
                                 parse_dates=None, chunksize=None)
        except:
            msg = Message(1, 'error')
            return json.dumps(msg.__dict__, ensure_ascii=False).replace("'", '"')

        data['mouth'] = pd.to_datetime(data['mouth'])
        data.columns = ['year', 'ds', 'province', 'city', 'citylevel', 'longitude', 'twist', 'y', 'proportion', 'inc',
                        'inc_2', 'pricehistoryId']
        data = data.sort_values(by='ds')

        m = Prophet(yearly_seasonality=4, changepoint_prior_scale=0.09, weekly_seasonality=False, daily_seasonality=False)
        m.fit(data)
        future = m.make_future_dataframe(periods=365)
        fcst = m.predict(future)

        province = str(data[2:3]['province'].values).split("'")[1]
        city = str(data[2:3]['city'].values).split("'")[1]
        citylevel = str(data[2:3]['citylevel'].values).split("'")[1]
        msg = Message(0,"success","success")
        msg.set_location(province, city, citylevel)
        for index, row in fcst.iterrows():
            t = str(row['ds']).split(' ')[0].split('-')
            if t[-1] == '01':
                time = t[0] + '-' + t[1]
                price_upper = str(round(row['yhat_upper'], 4))
                price_lower = str(round(row['yhat_lower'], 4))
                try:
                    price = str(data[data['ds'] == row['ds']]['y'].values[0])
                except:
                    # price = str(round(row['yhat'] + round(row['yhat_upper'] + row['yhat_lower'])/3, ))
                    price = str(round(row['yhat'],2))
                msg.add_price(time, price_upper, price_lower, price)
        try:
            with open(os.getcwd() + '/data/{0}{1}{2}.json'.format(province,city,region), 'w+', encoding='utf-8') as f:
                f.write(json.dumps(msg.__dict__, ensure_ascii=False).replace("\'", '\"'))
        except:
            print('write error')
        res = json.dumps(msg.__dict__, ensure_ascii=False).replace("'",'"')
        resp = make_response(res)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET,POST'
        resp.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
        return res.replace("\'", '\"')



if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=5000, debug=True)
    # app.run()
    # get_tsa('朝阳')

    # http://10.6.207.179:5000/tsa/<province>&<city>&<region>
