#!/usr/bin/env python
from __future__ import print_function, division
import argparse
import json
import re
import elasticsearch as es
import elasticsearch_dsl

parser = argparse.ArgumentParser(description="Cleans up Kibana objects and " +
                                 "Elasticsearch indices for a given user " +
                                 "and project")
parser.add_argument('user', action='store', type=str, help="User ID.")
parser.add_argument('project', action='store', type=str, help="Run ID.")
parser.add_argument('-e', '--elasticsearch', action='store_true',
                    help="Delete Elasticsearch indices with [user_project] prefix")
parser.add_argument('-k', '--kibana', action='store_true',
                    help="Delete Kibana objects with [user_project] prefix.")
parser.add_argument('-H', '--host', action='store', dest='host', type=str,
                    default='elk.crc.nd.edu', help="Elasticsearch host.")
parser.add_argument('-p', '--port', action='store', dest='port', type=int,
                    default=9200, help="Elasticsearch port number.")

args = parser.parse_args()

prefix = '[' + args.user + '_' + args.project + ']'

client = es.Elasticsearch([{'host': args.host, 'port': args.port}])


if args.kibana:
    search = elasticsearch_dsl.Search(using=client, index='.kibana') \
        .filter('prefix', _id=prefix)
    response = search.execute()

    for result in response:
        client.delete(index='.kibana', doc_type=result.meta.doc_type,
                      id=result.meta.id)

if args.elasticsearch:
    client.indices.delete(index=prefix + '_*')
