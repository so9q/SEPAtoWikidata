# This file converts from geojson to csv for import into Wikidata
# example import: https://www.wikidata.org/wiki/Q96475355
# GPLv3

# fix references on all statements that are not härledda

import json
import csv
import geopy.distance

use_cache = True
update_cache = True
#update_cache = False
cache_file = "overpass.json"

missing_count = 0
feature_count = 0
with open("anordningar.geojson") as json_file:
    data = json.load(json_file)

# https://towardsdatascience.com/loading-data-from-openstreetmap-with-python-and-the-overpass-api-513882a27fd0?gi=af86771b0e4d
import os.path

if ((os.path.isfile(cache_file) and update_cache) or update_cache):
    import requests
    import json
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
[out:json];
area["ISO3166-1"="SE"][admin_level=2];
(
    // query part for: “tourism=wilderness_hut and access!=private”
    node["tourism"="wilderness_hut"]["access"!="private"](area);
    way["tourism"="wilderness_hut"]["access"!="private"](area);
    relation["tourism"="wilderness_hut"]["access"!="private"](area);  
    
    // query part for: “amenity=shelter and shelter_type!=public_transport”
    node["amenity"="shelter"]["shelter_type"!="public_transport"](area);
    way["amenity"="shelter"]["shelter_type"!="public_transport"](area);
    relation["amenity"="shelter"]["shelter_type"!="public_transport"](area);
);
out center;
"""
    response = requests.get(overpass_url,
                            params={'data': overpass_query})
    osmdata = response.json()
    with open(cache_file, 'w', encoding='utf8') as json_file:
            json.dump(osmdata, json_file, ensure_ascii=False)
else:
    with open(cache_file, 'r') as myfile:
        osmdata=json.load(myfile)
    
matches = set()
print("Searching for matches within 100m")
# loop through the list
for feature in data["features"]:
    types = feature["properties"]["Undertyp"]
    if types in ["Bakval","Kåta","Tältplats","Koja"]:
        feature_count += 1
        objectid = feature["properties"]["OBJECTID"]
        lat = feature["geometry"]["coordinates"][0][1]
        lon = feature["geometry"]["coordinates"][0][0]
        nvcoord = (lat,lon)
        # calculate distance between this feature and all points in vindskydd
        # https://stackoverflow.com/questions/19412462/getting-distance-between-two-points-based-on-latitude-longitude#19412565
        for point in osmdata["elements"]:
            # find all points closer than 100 meter
            lat = point["lat"]
            lon = point["lon"]
            point_coord = (lat,lon)
            distance = round(geopy.distance.great_circle(nvcoord, point_coord).m)
            if (distance < 100):
                for tags in point["tags"]:
                    if (tags == "name"):
                        name = point["tags"]["name"]
                    elif (tags == "amenity"):
                        name = point["tags"]["amenity"]
                    elif (tags == "leisure"):
                        name = point["tags"]["leisure"]
                    else:
                        name = point["tags"]
                print(str(name) + " is closer than 100m to OBJECTID:"+str(objectid) + ". Distance: "+str(distance)+"m")
                # log matches
                matches.add(objectid)

print(str(len(matches)) +" matches found")

#https://gis.stackexchange.com/questions/130963/write-geojson-into-a-geojson-file-with-python#130987
from geojson import Point, Feature, FeatureCollection, dump

#point = Point((-115.81, 37.24))

#features = []
#features.append(Feature(geometry=point, properties={"country": "Spain"}))

# add more features...
# features.append(...)

# all non-matching objectids are missing
print("Number of missing shelters in OpenStreetMap found in https://github.com/so9q/SEPAtoWikidata/blob/master/anordningar.geojson from Naturvårdsverket:")
features = []
for feature in data["features"]:
    types = feature["properties"]["Undertyp"]
    if types in ["Bakval","Kåta","Tältplats","Koja"]:
        objectid = feature["properties"]["OBJECTID"]
        if (objectid not in matches):
            missing_count += 1
            features.append(feature)

print(str(missing_count)+" missing out of "+str(feature_count)+" total")

# export to file
print("exporting missing features to geojson")
feature_collection = FeatureCollection(features)

# https://stackoverflow.com/questions/18337407/saving-utf-8-texts-in-json-dumps-as-utf8-not-as-u-escape-sequence
with open('missing-shelters-in-openstreetmap.geojson', 'w', encoding='utf8') as f:
       dump(feature_collection, f, ensure_ascii=False)

