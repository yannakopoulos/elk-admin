#!/usr/bin/env python
from __future__ import print_function, division
import argparse
import gzip
import re
import xmltodict
import os
import elasticsearch

parser = argparse.ArgumentParser(description='Reads and parses report.xml.gz.')
parser.add_argument('-f', action='store', dest='path',
                    type=str, help='Path to report.xml.gz')

path = parser.parse_args().path

user = 'matze'
run = 'v29'

prefix = '[' + user + '-' + run + ']'

es = elasticsearch.Elasticsearch([{'host': 'localhost', 'port': 9200}])
index = prefix + '_lobster_report_xml'

# gets status and task id from path
id_p = re.compile('(\w*)\/(\d{4})\/(\d{4})')
# gets PFN domain from PFN field
domain_p = re.compile('root://([^/]*)')

gzip_handler = gzip.open(path, 'rb')
try:
    xml_data = gzip_handler.read()
    doc = xmltodict.parse(xml_data)
    doc['is_good_doc': True]
except Exception:
    doc = {'is_good_doc': False}
finally:
    gzip_handler.close()

if doc['is_good_doc']:
    # get task id and successful/failed
    status, id1, id2 = id_p.search(path).groups()
    task_id = int(id1 + id2)

    if 'FrameworkJobReport' in doc and 'InputFile' in doc['FrameworkJobReport']:
        count = 0
        for d in doc['FrameworkJobReport']['InputFile']:
            if isinstance(d, dict):
                d['status'] = status
                d['task_id'] = task_id
                d['path'] = path

                results = domain_p.search(d['PFN'])

                if results:
                    d['PFN_domain'] = results.group(1)

                # es.index(index=index, doc_type='InputFile', body=d,
                #          id=id1 + id2 + '_' + str(count))

                doc[str(count)] = d
                count += 1

    doc.pop('is_good_doc')
