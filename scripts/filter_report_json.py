#!/usr/bin/env python
from __future__ import print_function, division
import argparse
import json
import re
from datetime import datetime

parser = argparse.ArgumentParser(description='Reads and parses report.json.')
parser.add_argument('-f', action='store', dest='path',
                    type=str, help='Path to report.json')

path = parser.parse_args().path

# open gzip and extract fatal exception block
f = file(path, 'r')
try:
    doc = json.loads(f.read())
    doc['is_good_doc'] = True
    doc['path'] = path
finally:
    f.close()

if doc['is_good_doc']:
    # delete files key
    doc.pop('files')

    # get task id from path
    id_p = re.compile('.*\/0*(\d*)\/0*(\d*)\/.*')
    doc['id'] = int(''.join(id_p.search(doc['path']).groups()))

print(json.dumps({'report_json': doc}))
