# This file converts from geojson to csv for import into Wikidata
# example import: https://www.wikidata.org/wiki/Q96475355
# GPLv3

# fix references on all statements that are not härledda

import json
import csv
import geopy.distance

count = 0
ids = []
with open("anordningar.geojson") as json_file:
    data = json.load(json_file)

# source for this: https://query.wikidata.org/#%23Cats%0ASELECT%20%3Fitem%20%3FitemLabel%20%3Fadmin%20%3FadminLabel%20%3Foperator%20%3FoperatorLabel%20%0AWHERE%20%0A%7B%0A%20%20%3Fitem%20wdt%3AP31%20wd%3AQ179049%3B%0A%20%20%20%20%20%20%20%20wdt%3AP17%20wd%3AQ34.%0A%20%20%3Fitem%20wdt%3AP131%20%3Fadmin.%0A%20%20%3Fitem%20wdt%3AP137%20%3Foperator.%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22sv%22.%20%7D%0A%7D
with open("query.json") as json_file:
    reserves = json.load(json_file)

# https://gis.stackexchange.com/questions/292286/python-library-for-kml-to-geojson#292297
from osgeo import gdal, ogr
srcDS = gdal.OpenEx('vin.gpx')
ds = gdal.VectorTranslate('vin.geojson', srcDS, format='GeoJSON')
with open("vin.geojson") as json_file:
    vindskydd = json.load(json_file)
    
f = open('anordningar.csv', 'w')

matches = set()
with f:
    writer = csv.writer(f)
    # header
    header = ["qid",
              "Len",
              "Lsv",
              "Dsv",
              "P31",   #instance
              "P2561", #name
              "P17",   #country
              "P276",  #location = name of area is known lookup in query.json
              "S248",  #stated in
              "s813",  #retrieved
              "P137",  #operator = lookup in query.json
              "P131",  #administrative ent. = lookup in query.json = municipality
              "P625",  #coord
              "S248",  #stated in
              "s813",  #retrieved
              "P912",  #has facility
              "S248",  #stated in
              "s813",  #retrieved
              "P5195"  #Wikidata Dataset Imports page
              ]
    #print(header)
    writer.writerow(header)
    # loop through the list
    for feature in data["features"]:
        # duplicate finding
        ids.append(feature["properties"]["OBJECTID"])
        
        types = feature["properties"]["Undertyp"]
        if types in ["Bakval","Kåta","Tältplats","Koja"]:
            #print(feature)
            if (types == "Bakval"):
                #print(feature)
                objectid = feature["properties"]["OBJECTID"]
                lat = feature["geometry"]["coordinates"][0][1]
                lon = feature["geometry"]["coordinates"][0][0]
                nvcoord = (lat,lon)
                # calculate distance between this feature and all points in vindskydd
                # this is not really useful from a Wikidata POW.
                # https://stackoverflow.com/questions/19412462/getting-distance-between-two-points-based-on-latitude-longitude#19412565
                # for entry in vindskydd["features"]:
                #     # find all points closer than 100 meter
                #     lat = entry["geometry"]["coordinates"][1]
                #     lon = entry["geometry"]["coordinates"][0]
                #     entry_coord = (lat,lon)
                #     distance = geopy.distance.distance(nvcoord, entry_coord).m
                #     if (distance < 100):
                #         print(entry["properties"]["name"] + " is closer than 100m to OBJECTID:"+str(objectid) + ". Distance: "+str(distance)+"m")
                
                # fix name and descriptions
                for prop in feature["properties"]:
                    reserve = feature["properties"]["Skyddat_område"]
                    if (prop == "Anordningsnamn"):
                        # fix names - only one name is present in the
                        # file at present 2020-06-21 the rest are
                        # descriptions
                        if (feature["properties"]["Anordningsnamn"]  == "Rastplats Timmersläppet"):
                            name = "Rastplats Timmersläppet"
                        else:
                            name = "Bakval"
                        # name = descriptions
                        description = feature["properties"]["Anordningsnamn"] + " i " + reserve
                    else:
                        # no information provided set defaults
                        name = "Bakval"
                        description ="lägerplats med bakval i " + reserve

                # lookup reserve in reserves
                for entry in reserves:
                    if (reserve == entry["itemLabel"]):
                        #print(reserve + " found")
                        found = True
                        location = entry["item"][31:]
                        operator = entry["operator"][31:]
                        admin = entry["admin"][31:]
                        #print(item)

                if not found:
                    print(reserve + " not found in Wikidata :(")
                    count += 1
                
                #print(feature["properties"]["Anordning_ID"])
                source = "Q96504366"
                timestr = "+2020-06-21T00:00:00Z/11"
                row = ["",
                       name,
                       name,
                       description,
                       "Q832778",
                       "sv:"+'"'+name+'"',
                       "Q34",
                       location,
                       source,
                       timestr,
                       operator,
                       admin,
                       "@"+ str(lat) + "/"+ str(lon),
                       source,
                       timestr,
                       "Q96391237", #floorless lean-to with fixed
                                    #bench according to
                                    #http://trundoskoterklubb.pitea.riksnet.se/?Bildgalleri
                                    #and
                                    #https://www.blocket.se/annons/vasterbotten/grillkoja/89950385
                       source,
                       timestr,
                       '"https://www.wikidata.org/wiki/Wikidata:WikiProject_Shelters/Sweden"']
                #print(row)
                writer.writerow(row)

# check for duplicates
import collections
duplicates = [item for item, count in collections.Counter(ids).items() if count > 1]
if (len(duplicates) > 0):
    print(duplicates) # no duplicates found :)

#print(str(count) + " not found in total")
