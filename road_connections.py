'''
road_connections.py
jay.urbain@gmail.com

Road Connections
Given a textual query of a geocodeable place, for example: Bayside Wisconsin, 
returns list of dictionaries:
- OSM node id,
- list of streets at node (intersection)
- latitude of node
- longitude

The query must be geocodable and OSM must have polygon boundaries for the geocode result.

Example
place = 'Bayside, Wisconsin'
intersections = connections(place)
print(intersections)

{'osmid': 472988808, 'latitude': 43.1707462, 'longitude': -87.8955177, 'streets': ['East Buttles Place', 'North Lake Drive']}
{'osmid': 196628902, 'latitude': 43.1709381, 'longitude': -87.8970584, 'streets': ['East Buttles Place', 'North Fielding Road']}
{'osmid': 196673178, 'latitude': 43.1709506, 'longitude': -87.8983888, 'streets': ['North Greenvale Road', 'East Buttles Place']}
{'osmid': 6915412409, 'latitude': 43.1715911, 'longitude': -87.8996654, 'streets': ['East Buttles Place', 'East Buttles Road', 'North Pelham Parkway']}
...

'''
import networkx as nx
import osmnx as ox
import geopandas as gpd
ox.config(log_console=True, use_cache=True)

import matplotlib.cm as cm
import matplotlib.colors as colors

import argparse

def connections( place ):
    '''
    inputs - textual query specifying spatial boundaries of some geocodeable place(s)
    returns - tuples of street intersections using OSM data
    '''
    
    # Create a networkx graph from OSM data within the spatial boundaries of geocodable place(s).
    G = ox.graph_from_place(place, network_type='drive',  timeout=3600)
    
    # Project a graph from lat-long to the UTM zone appropriate for its geographic location.
    # https://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system
    Gp = ox.project_graph(G)
    
    # Clean-up intersections comprising clusters of nodes by merging them and returning their centroids
    ints = ox.clean_intersections(Gp)

    # create a dataframe of intersections
    gdf = gpd.GeoDataFrame(ints, columns=['geometry'], crs=Gp.graph['crs'])
    
    # generate lists of X, Y locations (UTM zone)
    X = gdf['geometry'].map(lambda pt: pt.coords[0][0])
    Y = gdf['geometry'].map(lambda pt: pt.coords[0][1])

    nodes = ox.get_nearest_nodes(Gp, X, Y, method='kdtree')
    connections = {}
    
    intersections = []
    for n in nodes:
        dict = {'osmid': G.nodes()[n]['osmid'],
               'latitude': G.nodes()[n]['y'],
                'longitude': G.nodes()[n]['x']
               }
        # print(dict)
        connections[n] = set([])
        for nbr in nx.neighbors(G, n):
            for d in G.get_edge_data(n, nbr).values():
                if 'name' in d:
                    if type(d['name']) == str:
                        connections[n].add(d['name'])
                    elif type(d['name']) == list:
                        for name in d['name']:
                            connections[n].add(name)
                    else:
                        connections[n].add(None)
                else:
                    connections[n].add(None)
                    
        if len(connections) > 0:
            dict['streets'] = list(connections[n])
            print(dict)
            intersections.append(dict)
        
    return intersections

# get a graph for some place
def plot_place(place):
    G = ox.graph_from_place(place, network_type='drive')
    fig, ax = ox.plot_graph(G)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='road connections')
    parser.add_argument("--place", required=True, type=str, help="Geocodeable place describing a spatial region, e.g., 'Bayside, Wisconsin'")
    args = parser.parse_args()
    connections(args.place)
                    
