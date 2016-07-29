#!/usr/bin/env python
from __future__ import print_function, division
import argparse
import gzip
import re
import json

parser = argparse.ArgumentParser(description='Reads and parses task.log.gz.')
parser.add_argument('-f', action='store', dest='path',
                    type=str, help='Path to task.log.gz')

path = parser.parse_args().path

doc = {}  # doc containing log data
doc['has_fatal_exception'] = False

# open gzip and extract fatal exception block
gzip_handler = gzip.open(path, 'rb')
try:
    recording = False
    for line in gzip_handler:
        if 'Begin Fatal Exception' in line:
            doc['has_fatal_exception'] = True
            recording = True
            error_lines = []
        if recording:
            error_lines.append(line[8:])
        if 'End Fatal Exception' in line:
            recording = False
finally:
    gzip_handler.close()

# task id
task_p = re.compile('\/(\d{4})\/(\d{4})\/')
doc['id'] = int("".join(task_p.search(path).groups()))

if doc['has_fatal_exception']:
    # compile full error message, if it exists
    doc['message'] = "".join(error_lines)
    doc['has_fatal_exception'] = True

    # exception category
    e_cat_p = re.compile('\'(.*)\'')
    doc['exception_category'] = \
        e_cat_p.search(doc['message']).group(1)

    # exception message
    e_mess_p = re.compile('Exception Message:\n(.*)')
    doc['exception_message'] = \
        e_mess_p.search(doc['message']).group(1)

# send json doc to logstash via stdout
print(json.dumps({'task_log_gz': doc}))
