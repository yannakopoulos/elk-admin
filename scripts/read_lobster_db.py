#!/usr/bin/env python
from __future__ import print_function, division
import argparse
import elasticsearch
import sqlite3
from datetime import datetime

parser = argparse.ArgumentParser(
    description='Reads and parses lobster.db. into Elasticsearch.')
parser.add_argument('directory', action='store', type=str,
                    help='Path to Lobster project folder.')

# user = 'matze'
# run = 'v29'
#
# prefix = '[' + user + '_' + run + ']'

prefix = '[template]'

es = elasticsearch.Elasticsearch([{'host': 'elk.crc.nd.edu', 'port': 9200}])

index = prefix + '_lobster_tasks'
doc_type = 'logs'

conn = sqlite3.connect(parser.parse_args().directory + 'lobster.db')
c = conn.cursor()

for row in c.execute('SELECT * FROM tasks'):
    keys = [description[0] for description in c.description]
    doc = dict(zip(keys, row))

    # parse timestamps
    doc['time_processing_end'] = datetime.fromtimestamp(
        doc['time_processing_end'])
    doc['time_prologue_end'] = datetime.fromtimestamp(doc['time_prologue_end'])
    doc['time_retrieved'] = datetime.fromtimestamp(doc['time_retrieved'])
    doc['time_stage_in_end'] = datetime.fromtimestamp(doc['time_stage_in_end'])
    doc['time_stage_out_end'] = datetime.fromtimestamp(
        doc['time_stage_out_end'])
    doc['time_transfer_in_end'] = datetime.fromtimestamp(
        doc['time_transfer_in_end'])
    doc['time_transfer_in_start'] = datetime.fromtimestamp(
        doc['time_transfer_in_start'])
    doc['time_transfer_out_end'] = datetime.fromtimestamp(
        doc['time_transfer_out_end'])
    doc['time_transfer_out_start'] = datetime.fromtimestamp(
        doc['time_transfer_out_start'])
    doc['time_wrapper_ready'] = datetime.fromtimestamp(
        doc['time_wrapper_ready'])
    doc['time_wrapper_start'] = datetime.fromtimestamp(
        doc['time_wrapper_start'])

    upsert_doc = {'doc': {'lobster_db': doc,
                          'timestamp': doc['time_retrieved']},
                  'doc_as_upsert': True}

    es.update(index=index, doc_type=doc_type, body=upsert_doc, id=doc['id'])
