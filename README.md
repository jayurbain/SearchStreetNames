## SearchStreetNames
Searchable street names using ElasticSearch and OSMnx python library to identify streets and geocodeable intersections.

### Retrieving geocoded intersections with street names

#### Install the OSMnx python library for interacting with OpenStreetMap networks
```
conda config --prepend channels conda-forge
conda create -n ox --strict-channel-priority osmnx
```

Alternatively, install OSMnx via pip within some environment: `pip install osmnx`

Reference:    
https://github.com/gboeing/osmnx


### Retrieving geocoded intersections: 
At this point you should be able to retrieve a list of street intersection dictionaries.
`road_connections.py` - given a textual query of a geocodeable place return a list of dictionaries with the following information:
- OSM node id
- list of streets at node (intersection)
- latitude of node
- longitude

```
python road_connections.py --place "Bayside, Wisconsin"

Found nearest nodes to 176 points in 0.00 seconds
{'osmid': 472988808, 'latitude': 43.1707462, 'longitude': -87.8955177, 'streets': ['East Buttles Place', 'North Lake Drive']}
{'osmid': 196628902, 'latitude': 43.1709381, 'longitude': -87.8970584, 'streets': ['East Buttles Place', 'North Fielding Road']}
{'osmid': 196673178, 'latitude': 43.1709506, 'longitude': -87.8983888, 'streets': ['North Greenvale Road', 'East Buttles Place']}
{'osmid': 6915412409, 'latitude': 43.1715911, 'longitude': -87.8996654, 'streets': ['East Buttles Place', 'East Buttles Road', 'North Pelham Parkway']}
...
```

`place` must be geocodable and OSM must have polygon boundaries for the geocode result.

### Indexing intersections with ElasticSearch:

#### Install and run ElasticSearch (ES)

ElasticSearch Setup:
https://www.elastic.co/guide/en/elasticsearch/reference/current/setup.html

ElasticSearch Getting Started Guide:  
https://www.elastic.co/guide/en/elasticsearch/reference/current/getting-started.html

AWS ElasticSearch:    
https://aws.amazon.com/elasticsearch-service/getting-started/

Start ElasticSearch (ES) locally:    
Elasticsearch can be started from the command line within the ElasticSearch directory:
```
./bin/elasticsearch
```
Check ES by navigating to:   
```
https://localhost:9200
```

You should see something like the following:   
```
{
  "name" : "jays-mbp-2.lan",
  "cluster_name" : "elasticsearch",
  "cluster_uuid" : "4RoI0VLQRFGcjlEgVH1MnA",
  "version" : {
    "number" : "7.5.2",
    "build_flavor" : "default",
    "build_type" : "tar",
    "build_hash" : "8bec50e1e0ad29dad5653712cf3bb580cd1afcdf",
    "build_date" : "2020-01-15T12:11:52.313576Z",
    "build_snapshot" : false,
    "lucene_version" : "8.3.0",
    "minimum_wire_compatibility_version" : "6.8.0",
    "minimum_index_compatibility_version" : "6.0.0-beta1"
  },
  "tagline" : "You Know, for Search"
}
```

#### Create an ElasticSearch Index  

Create the index `intersctions` and define the datatype mappings for the index.

Recommend using a tool like `Postman` to handle complex curl queries.

```
curl -XPUT http://localhost:9200/intersections -d
'{
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "location": {
                "type": "geo_point"
            },
            "streets": {
                "type": "text",
                "analyzer": "standard"
            },
            "place": {
                "type": "text",
                "analyzer": "standard"
            }
        }
    }
}'
```
Note: Creating the index and mapping the data types can be done in
two steps, but you need to define the data type mapping before 
inserting records. You need to use this approach with AWS ElasticSearch.

So with AWS ElasticSearch, define your domain using their online tools,
and then isse the following query to define the index mappings:

curl --location --request PUT 'https://search-intersections-y6owyaorob2xafcmoct3va32eq.us-east-1.es.amazonaws.com/intersections' \
--header 'Content-Type: application/json' \
--data-raw '{
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "location": {
                "type": "geo_point"
            },
            "streets": {
                "type": "text",
                "analyzer": "standard"
            },
            "place": {
                "type": "text",
                "analyzer": "standard"
            }
        }
    }
}'

In either case, if everything worked, you should get something like the following:

```
{
    "acknowledged": true,
    "shards_acknowledged": true,
    "index": "intersections"
}
```

Insert a single record into the index by id (OSMID):

```
curl -XPUT http://localhost:9200/intersections/_doc/472988808' \
--header 'Content-Type: application/json' \
--data-raw '{
  "location": { 
    "lat": 43.1707462,
    "lon": -87.8955177
  },
  "streets": ["North Lake Drive", "East Buttles Place"],
  "place": "Bayside, Wisconsin"
}'

```

You should see something like the following:
```
{
    "_index": "intersections",
    "_type": "_doc",
    "_id": "472988808",
    "_version": 1,
    "result": "created",
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 0,
    "_primary_term": 1
}
```

Query the index:

```
curl --location --request GET 'http://localhost:9200/intersections/_search?q=lake' \
--header 'Content-Type: application/json'

```

You should see something like the following:

```

{"took":780,"timed_out":false,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0},"hits":{"total":{"value":1,"relation":"eq"},"max_score":0.2876821,"hits":[{"_index":"intersections","_type":"_doc","_id":"472988808","_score":0.2876821,"_source":
{
  "location": { 
    "lat": 43.1707462,
    "lon": -87.8955177
  },
  "streets": ["North Lake Drive", "East Buttles Place"],
  "place": "Bayside, Wisconsin"
}
```

Bulk insert:

Run `es_bulk_intersections` to generate a JSON file of intersections in ES bulk format:

```
python es_bulk_intersections.py --index_name='intersections' --place='Bayside, Wisconsin' --bulk_file='bayside_wi.json'
```

Post the bulk records to ES:

```
$ curl -XPOST http://127.0.0.1:9200/intersections/_bulk --data-binary "@bayside_wi.json"

AWS ES:   

curl -XPOST https://search-intersections-y6owyaorob2xafcmoct3va32eq.us-east-1.es.amazonaws.com/_bulk --header 'Content-Type: application/json' --data-binary "@bayside_wi.json"

curl -XPOST https://search-intersections-y6owyaorob2xafcmoct3va32eq.us-east-1.es.amazonaws.com/_bulk --header 'Content-Type: application/json' --data-binary "@chicago_il.json"
```

Repeat the queries above:
```
$ curl -XGET http://localhost:9200/intersections/_search?q=lake

{"took":487,"timed_out":false,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0},"hits":{"total":{"value":19,"relation":"eq"},"max_score":2.7334583,"hits":[{"_index":"intersections","_type":"_doc","_id":"472982424","_score":2.7334583,"_source":{"location": {"lat": 43.1762392, "lon": -87.895758}, "streets": ["North Lake Drive"], "place": "Bayside, Wisconsin"}},{"_index":"intersections","_type":"_doc","_id":"4602472245","_score":2.7334583,"_source":{"location": {"lat": 43.1953975, "lon": -87.8972865}, "streets": ["North Lake Drive", null], "place": "Bayside, Wisconsin"}},{"_index":"intersections","_type":"_doc","_id":"231846907","_score":2.7334583,"_source":{"location": {"lat": 43.1955777, "lon": -87.8979194}, "streets": ["North Lake Drive"], "place": "Bayside, Wisconsin"}},{"_index":"intersections","_type":"_doc","_id":"472988808","_score":2.172727,"_source":{"location": {"lat": 43.1707462, "lon": -87.8955177}, "streets": ["North Lake Drive", "East Buttles Place"], "place": "Bayside, Wisconsin"}},{"_index":"intersections","_type":"_doc","_id":"472988853","_score":2.172727,"_source":{"location": {"lat": 43.1747281, "lon": -87.895458}, "streets": ["East Wahner Place", "North Lake Drive"], "place": "Bayside, Wisconsin"}},{"_index":"intersections","_type":"_doc","_id":"472988850","_score":2.172727,"_source":{"location": {"lat": 43.1729254, "lon": -87.8954734}, "streets": ["North Lake Drive", "East Wabash Place"], "place": "Bayside, Wisconsin"}},{"_index":"intersections","_type":"_doc","_id":"196635217","_score":2.172727,"_source":{"location": {"lat": 43.1780603, "lon": -87.8953535}, "streets": ["East Glencoe Place", "North Lake Drive"], "place": "Bayside, Wisconsin"}},{"_index":"intersections","_type":"_doc","_id":"196635218","_score":2.172727,"_source":{"location": {"lat": 43.1796597, "lon": -87.8952999}, "streets": ["North Lake Drive", "East Standish Place"], "place": "Bayside, Wisconsin"}},{"_index":"intersections","_type":"_doc","_id":"196635219","_score":2.172727,"_source":{"location": {"lat": 43.1807839, "lon": -87.8952595}, "streets": ["North Lake Drive", "East Hermitage Road"], "place": "Bayside, Wisconsin"}},{"_index":"intersections","_type":"_doc","_id":"196635228","_score":2.172727,"_source":{"location": {"lat": 43.1865708, "lon": -87.8950885}, "streets": ["North Lake Drive", "East Glenbrook Road"], "place": "Bayside, Wisconsin"}}]}}(ox) 
```

This is what we're after: structured query with large query text to find most relevant intersections

```
curl -XGET http://localhost:9200/intersections/_search?pretty -d
'
{
  "query": 
	{
		"match":
		{
		"streets":"slacks moodring lives near lake drive and east standish place in disturbia wisconsin"
		}
	}
}
'
```

You should see something like the following:

```
{
  "took": 11,
  "timed_out": false,
  "_shards": {
    "total": 1,
    "successful": 1,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 109,
      "relation": "eq"
    },
    "max_score": 8.776541,
    "hits": [
      {
        "_index": "intersections",
        "_type": "_doc",
        "_id": "196635218",
        "_score": 8.776541,
        "_source": {
          "location": {
            "lat": 43.1796597,
            "lon": -87.8952999
          },
          "streets": [
            "North Lake Drive",
            "East Standish Place"
          ],
          "place": "Bayside, Wisconsin"
        }
      },
      {
        "_index": "intersections",
        "_type": "_doc",
        "_id": "196665011",
        "_score": 6.6657786,
        "_source": {
          "location": {
            "lat": 43.1786498,
            "lon": -87.8889138
          },
          "streets": [
            "East Standish Place"
          ],
          "place": "Bayside, Wisconsin"
        }
      },
      {
        "_index": "intersections",
        "_type": "_doc",
        "_id": "196665007",
        "_score": 6.603813,
        "_source": {
          "location": {
            "lat": 43.179363,
            "lon": -87.8912343
          },
          "streets": [
            "North Bayside Drive",
            "East Standish Place"
          ],
          "place": "Bayside, Wisconsin"
        }
      },
      ...
```

Structured (body) geocode query by latitude and longitude bounding box

```
curl --location --request GET 'http://localhost:9200/intersections/_search' \
--header 'Content-Type: application/json' \
--data-raw '{
  "query": {
    "geo_bounding_box": { 
      "location": {
        "top_left": {
          "lat": 44.986656,
          "lon": -93.258133
        },
        "bottom_right": {
          "lat": 27.964157,
          "lon": -82.452606
        }
      }
    }
  }
}'

```

You should see something like the following:

```
{
  "took": 3,
  "timed_out": false,
  "_shards": {
    "total": 1,
    "successful": 1,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 1,
      "relation": "eq"
    },
    "max_score": 1.0,
    "hits": [
      {
        "_index": "intersections",
        "_type": "_doc",
        "_id": "472988808",
        "_score": 1.0,
        "_source": {
          "location": {
            "lat": 43.1707462,
            "lon": -87.8955177
          },
          "streets": [
            "North Lake Drive",
            "East Buttles Place"
          ],
          "place": "Bayside, Wisconsin"
        }
      }
    ]
  }
}
```

Structured (body) geocode query by latitude and longitude distance

```
curl --location --request GET 'http://localhost:9200/intersections/_search' \
--header 'Content-Type: application/json' \
--data-raw '{
    "query": {
        "bool": {
            "must": {
                "match_all": {}
            },
            "filter": {
                "geo_distance": {
                    "distance": "1km",
                    "location": {
                        "lat": 43.1806231,
                        "lon": -87.8927188
                    }
                }
            }
        }
    }
}'

```

You should see something like the following:

```
{
    "took": 7,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 70,
            "relation": "eq"
        },
        "max_score": 1.0,
        "hits": [
            {
                "_index": "intersections",
                "_type": "_doc",
                "_id": "472982424",
                "_score": 1.0,
                "_source": {
                    "location": {
                        "lat": 43.1762392,
                        "lon": -87.895758
                    },
                    "streets": [
                        "North Lake Drive"
                    ],
                    "place": "Bayside, Wisconsin"
                }
            },
            ...
```