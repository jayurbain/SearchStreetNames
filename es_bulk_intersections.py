'''
es_bulk_intersections.py
jay.urbain@gmail.com

Given a textual query of a geocodeable place, for example: Bayside Wisconsin, 
returns list of dictionaries containg the following formatted for bulk insert
into Elasic Search
- OSM node id,
- list of streets at node (intersection)
- latitude of node
- longitude

The query must be geocodable and OSM must have polygon boundaries for the geocode result.

Example:
place = 'Bayside, Wisconsin'
json_file = 'bayside_wi.json'
es_bulk_intersections(intersections, json_file)

$ head json_file

[
{'osmid': 472988808, 'latitude': 43.1707462, 'longitude': -87.8955177, 'streets': {'North Lake Drive', 'East Buttles Place'}}, 
{'osmid': 196628902, 'latitude': 43.1709381, 'longitude': -87.8970584, 'streets': {'North Fielding Road', 'East Buttles Place'}}, 
{'osmid': 196673178, 'latitude': 43.1709506, 'longitude': -87.8983888, 'streets': {'North Greenvale Road', 'East Buttles Place'}},
'''

import json
import argparse
import road_connections

def es_bulk_intersections(index_name, intersections, place, bulk_file):
    '''
    inputs 
    - index name - ES index name
    - intersections - list of geocoded intersections
        [
        {'osmid': 472988808, 'latitude': 43.1707462, 'longitude': -87.8955177, 'streets': {'North Lake Drive', 'East Buttles Place'}}, 
        {'osmid': 196628902, 'latitude': 43.1709381, 'longitude': -87.8970584, 'streets': {'North Fielding Road', 'East Buttles Place'}}, 
        {'osmid': 196673178, 'latitude': 43.1709506, 'longitude': -87.8983888, 'streets': {'North Greenvale Road', 'East Buttles Place'}},
        ...
    - bulk_file - file path for bulk file output
    
    outputs
    - text file in ElasticSearch bulk insert format

    {'index': {'_index': 'intersections', '_type': '_doc', '_id': 472988808}}
    {'location': {'lat': 43.1707462, 'lon': -87.8955177}, 'streets': ['North Lake Drive', 'East Buttles Place'], 'place': 'Bayside, Wisconsin'}
    {'index': {'_index': 'intersections', '_type': '_doc', '_id': 196628902}}
    {'location': {'lat': 43.1709381, 'lon': -87.8970584}, 'streets': ['North Fielding Road', 'East Buttles Place'], 'place': 'Bayside, Wisconsin'}
    '''

    with open(bulk_file, 'w') as fp:
        
        for d in intersections:
            index = { "index" : { "_index": index_name, "_type" : "_doc", "_id" : d['osmid'] }}
            print(json.dumps(index), file=fp)
            location = { "location": { "lat": d['latitude'], "lon": d['longitude']}, "streets": d['streets'], "place": place}
            print(json.dumps(location), file=fp)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='es bulk intersections')
    parser.add_argument("--index_name", required=True, type=str, help="ElasticSearch index name")
    parser.add_argument("--place", required=True, type=str, help="Geocodeable place describing a spatial region, e.g., 'Bayside, Wisconsin'")
    parser.add_argument("--bulk_file", required=True, type=str, help="bulk file path")
    args = parser.parse_args()
    intersections = road_connections.connections(args.place)
    es_bulk_intersections(args.index_name, intersections, args.place, args.bulk_file)
                    
