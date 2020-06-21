# This file converts from geojson to csv for import into Wikidata
# example import: https://www.wikidata.org/wiki/Q96475355
# GPLv3

# fix references on all statements that are not härledda

import json
import csv
import geopy.distance

missing_count = 0
feature_count = 0
with open("anordningar.geojson") as json_file:
    data = json.load(json_file)

# https://gis.stackexchange.com/questions/292286/python-library-for-kml-to-geojson#292297
from osgeo import gdal, ogr
srcDS = gdal.OpenEx('vin.gpx')
ds = gdal.VectorTranslate('vin.geojson', srcDS, format='GeoJSON')
with open("vin.geojson") as json_file:
    vindskydd = json.load(json_file)
    
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
        for entry in vindskydd["features"]:
            # find all points closer than 100 meter
            lat = entry["geometry"]["coordinates"][1]
            lon = entry["geometry"]["coordinates"][0]
            entry_coord = (lat,lon)
            distance = geopy.distance.distance(nvcoord, entry_coord).m
            if (distance < 100):
                #print(entry["properties"]["name"] + " is closer than 100m to OBJECTID:"+str(objectid) + ". Distance: "+str(distance)+"m")
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
print("Number of missing shelters in Vindskydd i Norden database found in https://github.com/so9q/SEPAtoWikidata/blob/master/anordningar.pretty.geojson from Naturvårdsverket:")
features = []
for feature in data["features"]:
    objectid = feature["properties"]["OBJECTID"]
    if (objectid not in matches):
        missing_count += 1
        features.append(feature)

print(str(missing_count)+" missing out of "+str(feature_count)+" total")

# export to file
print("exporting missing features to missing.geojson")
feature_collection = FeatureCollection(features)

with open('missing.geojson', 'w') as f:
       dump(feature_collection, f)

