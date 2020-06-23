# This file converts from geojson to csv for import into Wikidata
# example import: https://www.wikidata.org/wiki/Q96475355
# GPLv3

# pseudo code:
# for every osm object
# see if any vin feature matches and save the osmid if yes
# for every non match print osm feature
# output in some format

import json
import csv
import geopy.distance

use_cache = True
#update_cache = True
update_cache = False
cache_file = "overpass-shelters.json"

missing_count = 0
osmfeature_count = 0
with open("vin.geojson") as json_file:
    vindata = json.load(json_file)

# https://towardsdatascience.com/loading-data-from-openstreetmap-with-python-and-the-overpass-api-513882a27fd0?gi=af86771b0e4d
import os.path

if ((os.path.isfile(cache_file) and update_cache) or update_cache):
    print("fetching from overpass")
    import requests
    import json
    overpass_url = "http://overpass-api.de/api/interpreter"
    # thanks to https://www.openstreetmap.org/user/mmd for help with fixing area!
    # see https://help.openstreetmap.org/questions/20531/overpass-ql-nodes-and-ways-in-area
    overpass_query = """
[out:json];
area["ISO3166-1"="SE"][admin_level=2]->.a;
(
    nwr["tourism"="wilderness_hut"]["access"!="private"](area.a);
    nwr["amenity"="shelter"]["shelter_type"!="public_transport"](area.a);
);
out center;
"""
    response = requests.get(overpass_url,
                            params={'data': overpass_query})
    osmjson = response.json()
    with open(cache_file, 'w', encoding='utf8') as json_file:
            json.dump(osmjson, json_file, ensure_ascii=False)

    print("fetching from overpass done")
else:
    print("reading from cache")
    with open(cache_file, 'r') as myfile:
        osmjson=json.load(myfile)
    print("reading from cache done")

#convert overpass json to geojson
import osm2geojson
print("converting to geojson")
osmdata = osm2geojson.json2geojson(osmjson)
print("conversion done")
#print(osmdata["features"][0])

matches = set()
print("Searching for matches within 100m")
# loop through the list
for osmfeature in osmdata["features"]:
        osmfeature_count += 1
        # debug break out
        # if (osmfeature_count == 5):
        #     break
        osmid = osmfeature["properties"]["id"]
        lat = osmfeature["geometry"]["coordinates"][1]
        lon = osmfeature["geometry"]["coordinates"][0]
        osmcoord = (lat,lon)
        # calculate distance between this feature and all points in vindskydd
        # https://stackoverflow.com/questions/19412462/getting-distance-between-two-points-based-on-latitude-longitude#19412565
        for feature in vindata["features"]:
            # find all points closer than 100 meter
            lat = feature["geometry"]["coordinates"][1]
            lon = feature["geometry"]["coordinates"][0]
            vincoord = (lat,lon)
            distance = round(geopy.distance.great_circle(vincoord, osmcoord).m)
            if (distance < 100):
                #does all have names?
                name = feature["properties"]["name"]
                print(str(name) + " is closer than 100m to osmid:"+str(osmid) + ". Distance: "+str(distance)+"m")
                # log matches
                matches.add(osmid)

print(str(len(matches)) +" matches found")

#https://gis.stackexchange.com/questions/130963/write-geojson-into-a-geojson-file-with-python#130987
from geojson import Point, Feature, FeatureCollection, dump

# all non-matching objectids are missing
#print(matches)
print("Calculating of missing shelters in VIN found in OSM")
features = []
for feature in osmdata["features"]:
    osmid = feature["properties"]["id"]    
    if (osmid not in matches):
        #print(str(osmid)+ " not in matches")
        missing_count += 1
        # remove nested tags and place them in properties instead
        for tag in feature["properties"]["tags"]:
            feature["properties"][tag] = feature["properties"]["tags"][tag]
        del feature["properties"]["tags"]
        features.append(feature)

print(str(missing_count)+" missing out of "+str(osmfeature_count)+" total")

# export to file
print("Exporting missing features to geojson")
feature_collection = FeatureCollection(features)

# https://stackoverflow.com/questions/18337407/saving-utf-8-texts-in-json-dumps-as-utf8-not-as-u-escape-sequence
with open('missing-shelters-in-vin-based-on-openstreetmap.geojson', 'w', encoding='utf8') as f:
       dump(feature_collection, f, ensure_ascii=False)

