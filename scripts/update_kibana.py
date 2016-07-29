#!/usr/bin/env python
from __future__ import print_function, division
import argparse
import json
import re
import elasticsearch as es
import elasticsearch_dsl as es_dsl

parser = argparse.ArgumentParser(description='Generates new Kibana objects ' +
                                 'from templates for a given user and run.')
parser.add_argument('user', action='store', type=str,
                    help='User ID.')
parser.add_argument('project', action='store', type=str,
                    help='Project ID.')
parser.add_argument('-H', '--host', action='store', dest='host', type=str,
                    default='elk.crc.nd.edu', help='Elasticsearch host.')
parser.add_argument('-p', '--port', action='store', dest='port', type=int,
                    default=9200, help='Elasticsearch port number.')
parser.add_argument('-m', '--modules', nargs='+', action='store',
                    dest='modules', type=str, default=['core'],
                    help='Template modules to load.')
args = parser.parse_args()

temp_prefix = '[template]'
new_prefix = '[' + args.user + '_' + args.project + ']'
other_prefix = re.compile('\[.*\]')

client = es.Elasticsearch([{'host': args.host, 'port': args.port}])

indices = client.indices.get_aliases().keys()
if any(new_prefix in s for s in indices):
    raise AttributeError("Elasticsearch indices with prefix " +
                         new_prefix + " already exist.")

search = es_dsl.Search(using=client, index='.kibana') \
         .filter('prefix', _id=new_prefix)
response = search.execute()
if len(response) > 0:
    raise AttributeError("Kibana objects with prefix " +
                         new_prefix + " already exist.")

# should refine this to allow people to add new modules

search_index = es_dsl.Search(using=client, index='.kibana') \
    .filter('prefix', _id=temp_prefix) \
    .filter('match', _type='index-pattern')

response_index = search_index.execute()

for index in response_index:
    index.meta.id = index.meta.id.replace(temp_prefix, new_prefix, 1)
    client.index(index='.kibana', doc_type=index.meta.doc_type,
                 id=index.meta.id, body=index.to_dict())

for module in args.modules:
    temp_mod_prefix = temp_prefix + '[' + module + ']'
    new_mod_prefix = new_prefix + '[' + module + ']'

    search_vis = es_dsl.Search(using=client, index='.kibana') \
        .filter('prefix', _id=temp_mod_prefix) \
        .filter('match', _type='visualization')

    search_dash = es_dsl.Search(using=client, index='.kibana') \
        .filter('prefix', _id=temp_mod_prefix) \
        .filter('match', _type='dashboard')

    response_vis = search_vis.execute()
    response_dash = search_dash.execute()

    for vis in response_vis:
        vis.meta.id = vis.meta.id.replace(temp_mod_prefix,
                                          new_mod_prefix, 1)
        vis.title = vis.title.replace(temp_mod_prefix,
                                      new_mod_prefix, 1)

        source = json.loads(vis.kibanaSavedObjectMeta.searchSourceJSON)
        source['index'] = other_prefix.sub(new_prefix, source['index'])
        vis.kibanaSavedObjectMeta.searchSourceJSON = json.dumps(source)

        client.index(index='.kibana', doc_type=vis.meta.doc_type,
                     id=vis.meta.id, body=vis.to_dict())

    for dash in response_dash:
        dash.meta.id = dash.meta.id.replace(temp_mod_prefix,
                                            new_mod_prefix, 1)
        dash.title = dash.title.replace(temp_mod_prefix,
                                        new_mod_prefix, 1)

        dash_panels = json.loads(dash.panelsJSON)
        for panel in dash_panels:
            panel['id'] = panel['id'].replace(temp_mod_prefix,
                                              new_mod_prefix, 1)
        dash.panelsJSON = json.dumps(dash_panels)

        client.index(index='.kibana', doc_type=dash.meta.doc_type,
                     id=dash.meta.id, body=dash.to_dict())
