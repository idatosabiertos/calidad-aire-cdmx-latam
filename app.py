import requests
import pandas as pd
import itertools
import operator
import time
import datetime

def O3_IMECA2CONC(IMECA):
    conc = IMECA*0.11/100 # en ppm
    return conc*1000 #en ppb

def SO2_IMECA2CONC(IMECA):
    conc = IMECA*0.13/100 # ppm
    return conc*1000 #en ppb

def NO2_IMECA2CONC(IMECA):
    conc = IMECA*0.21/100 # en ppm
    return conc*1000 #en ppb

def CO_IMECA2CONC(IMECA):
    conc = IMECA*11/100 # en ppm
    return conc #en ppm

def PM10_IMECA2CONC(IMECA):
    form1 = IMECA/.833
    form2 = (IMECA -40.0)/0.5
    form3 = IMECA/0.625
    value_by_region = {0:form1,1:form2,2:form3}
    region = [dectect_region(form1),dectect_region(form2),dectect_region(form2)]
    most_common_region = most_common(region)
    return value_by_region[most_common_region] #en ug/m3

def IMECA2CONC(Chemical,Value):
    Value = int(Value)
    if Chemical == "O3": return O3_IMECA2CONC(Value)
    if Chemical == "SO2": return SO2_IMECA2CONC(Value)
    if Chemical == "NO2": return NO2_IMECA2CONC(Value)
    if Chemical == "CO": return CO_IMECA2CONC(Value)
    if Chemical == "PM10": return PM10_IMECA2CONC(Value)
    return "n/a"

def dectect_region(conc):
    if conc <= 121.0:
        return 0
    if conc >121.0 and conc <=320:
        return 1
    if conc > 320:
        return 2

def most_common(L):
    # get an iterable of (item, iterable) pairs
    SL = sorted((x, i) for i, x in enumerate(L))
    # print 'SL:', SL
    groups = itertools.groupby(SL, key=operator.itemgetter(0))
    # auxiliary function to get "quality" for an item
    def _auxfun(g):
      item, iterable = g
      count = 0
      min_index = len(L)
      for _, where in iterable:
        count += 1
        min_index = min(min_index, where)
      # print 'item %r, count %r, minind %r' % (item, count, min_index)
      return count, -min_index
    # pick the highest-count/earliest item
    return max(groups, key=_auxfun)[0]

def gen_feed_info():
    now = datetime.datetime.now()
    feed_dict = {}
    feed_dict["feed_id"] = "MXMEX-"+ str(now.year) + str(now.month) + str(now.day) + str(now.hour) + str(now.minute)
    feed_dict["feed_publisher-name"] = "Secretaría de Medio Ambiente de la Ciudad de México"
    feed_dict["feed_publisher-url"] = "http://www.aire.df.gob.mx/default.php"
    feed_dict["feed_start-date"] = datetime.datetime.now().isoformat()
    feed_dict["feed_finish-date"] = datetime.datetime.now().isoformat()
    feed_df = pd.DataFrame.from_dict([feed_dict])
    feed_df.to_csv("output/feed_info.csv", index=False)
    return feed_dict["feed_id"]

r = requests.get("http://148.243.232.113/calidadaire/xml/simat.json")
stations = r.json()["pollutionMeasurements"]["stations"]
units = {"NO2":"ppb","O3":"ppb","SO2":"ppb","PM10":"ug/m3","CO":"ppm"}
methods = {"O3":"MXMEX-O3-1993","NO2":"MXMEX-NOx-1993","SO2":"MXMEX-SO2-1993","PM10":"MXMEX-PM10-1993", "Temp": "MXMEX-TEMP", "Hum": "MXMEX-HUM", "CO":"MXMEX-CO-1993"}


country = [{
            "country_id": "MX",
            "country_lat": "19.24",
            "country_long": "-99.09",
            "country_name": "México",
            "country_timezone": "UTC +6:00"
        }]

dataframe_country = pd.DataFrame(country)
dataframe_country.to_csv("output/countries.csv", index=False)


city = [{
            "country_id": "MX",
            "city_id": "MXMEX",
            "city_lat": "19.38",
            "city_long": "-99.08",
            "city_name": "Ciudad de México y zona metropolitana",
            "city_timezone": "UTC +6:00"
        }]

dataframe_city = pd.DataFrame(city)
dataframe_city.to_csv("output/cities.csv", index=False)

estaciones =  {}
estaciones_as_list = []
for station in stations:
    local_dict = {
        "station_id": "MXMEX-" + station["shortName"],
        "country_id": "MX",
        "city_id": "MXMEX",
        "station_local" : station["name"],
        "station_name" : station["name"],
        "level": "station",
        "station_long" : station["location"].split(",")[1],
        "station_lat" : station["location"].split(",")[0],
        "station_timezone": "UTC +6:00"
    }
    estaciones[station["name"]] = local_dict
    estaciones_as_list.append(local_dict)
dataframe_estaciones = pd.DataFrame(estaciones_as_list)
dataframe_estaciones.to_csv("output/stations.csv", index=False)

pollutants =  {}
pollutants_as_list = []
feed_id = gen_feed_info()
now = datetime.datetime.now()
nowminusminuteandsecond = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
current_time = datetime.datetime.now().isoformat()
truncated_time = nowminusminuteandsecond.isoformat()
for station in stations:
    if station["pollutant"] == "n.d":
        next
    else:
        local_dict = {
            "station_id": "MXMEX-" + station["shortName"],
            "pollutant_id": station["pollutant"],
            "pollutant_unit": units[station["pollutant"]],
            "pollutant_update-time": truncated_time,
            "pollutant_value": IMECA2CONC(station["pollutant"],station["imecaPoints"]),
            "pollutant_averaging": 1,
            "method_id" : methods[station["pollutant"]],
            "feed_id" : feed_id
        }
        pollutants_as_list.append(local_dict)
        if station["temperature"] is not '':
            temp_dict = {
                "station_id": "MXMEX-" + station["shortName"],
                "pollutant_id": "Temp",
                "pollutant_unit": "C",
                "pollutant_update-time": truncated_time,
                "pollutant_value": station["temperature"],
                "pollutant_averaging": 1,
                "method_id" : methods[station["pollutant"]],
                "feed_id" : feed_id
            }
            pollutants_as_list.append(temp_dict)
        else:
            temp_dict = {}
        if station["humidity"] is not '':
            hum_dict = {
                "station_id": "MXMEX-" + station["shortName"],
                "pollutant_id": "Hum",
                "pollutant_unit": "%",
                "pollutant_update-time": truncated_time,
                "pollutant_value": station["humidity"],
                "pollutant_averaging": 1,
                "method_id" : methods[station["pollutant"]],
                "feed_id" : feed_id
            }
            pollutants_as_list.append(hum_dict)
        else:
            hum_dict = {}
pollutants_df = pd.DataFrame.from_dict(pollutants_as_list)
pollutants_df.to_csv("output/pollutants.csv", index=False)
