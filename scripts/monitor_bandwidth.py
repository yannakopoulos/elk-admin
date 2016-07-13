#!/usr/bin/env python
from __future__ import print_function, division
import argparse
import elasticsearch as es
from datetime import datetime as dt
import pytz
import time
import requests
import re
from bs4 import BeautifulSoup
import daemon
import sys

parser = argparse.ArgumentParser(
    description="Reads and parses bandwidth data from the ND bandwidth " +
    "webpage into Elasticsearch.")
parser.add_argument('-H', '--host', action='store', dest='es_host', type=str,
                    default='elk.crc.nd.edu', help="Elasticsearch host.")
parser.add_argument('-p', '--port', action='store', dest='es_port', type=int,
                    default=9200, help="Elasticsearch port number.")
args = parser.parse_args()


with daemon.DaemonContext(
    stdout=sys.stdout,
    stderr=sys.stderr
):
    client = es.Elasticsearch([{'host': args.es_host, 'port': args.es_port}])
    date_p = re.compile('(\d{1,2}\/\d{1,2}\/\d{4}) ' +
                        '(\d{1,2}:\d{2} \w{2}) - \d{1,2}:\d{2} \w{2}')
    timezone = pytz.timezone('America/New_York')

    while True:
        r = requests.get('http://prtg1.nm.nd.edu/sensortable.htm?' +
                         'id=505&subid=1&index=0&position=0')
        soup = BeautifulSoup(r.text, 'lxml')

        table = soup.find("div", {"class": "SubTable"})
        rows = table.find_all('tr')

        for row in rows:
            text = row.get_text().replace(',', '').split('\n')

            date = date_p.search(text[1])
            if date and not text[2] == '':
                timestamp = timezone.localize(
                    dt.strptime(" ".join(date.groups()),
                                '%m/%d/%Y %I:%M %p'),
                    is_dst=None)

                doc = {
                    'timestamp': timestamp,
                    'bandwidth_traffic_in': {
                        'megabit': float(text[2]),
                        'megabit_second': float(text[3])
                    },
                    'bandwidth_traffic_out': {
                        'megabit': float(text[4]),
                        'megabit_second': float(text[5])
                    },
                    'sum': {
                        'megabit': float(text[6]),
                        'megabit_second': float(text[7])
                    },
                    'coverage': float(text[8])
                }

                client.index(index='[all]_campus_bandwidth',
                             doc_type='web', body=doc, id=text[1])
        time.sleep(300)
