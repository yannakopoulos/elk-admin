import elasticsearch as es
import elasticsearch_dsl as es_dsl
import json
import os
import argparse

parser = argparse.ArgumentParser(description='Gets Kibana objects ' +
                                 'and generates templates.')
parser.add_argument('user', action='store', type=str,
                    help='User ID.')
parser.add_argument('project', action='store', type=str,
                    help='Project ID.')
parser.add_argument('-H', '--host', action='store', dest='es_host', type=str,
                    default='elk.crc.nd.edu', help='Elasticsearch host.')
parser.add_argument('-p', '--port', action='store', dest='es_port', type=int,
                    default=9200, help='Elasticsearch port number.')
parser.add_argument('-m', '--modules', nargs='+', action='store',
                    dest='modules', type=str, default=['core'],
                    help='Template modules to load.')
args = parser.parse_args()

prefix = '[' + args.user + '_' + args.project + ']'
client = es.Elasticsearch([{'host': args.es_host, 'port': args.es_port}])

print("getting Kibana objects with prefix" + prefix)
try:
    os.mkdir('templates')
except Exception:
    pass

print("getting index patterns")
try:
    os.mkdir('templates/index')
except Exception:
    pass
search_index = es_dsl.Search(using=client, index='.kibana') \
    .filter('prefix', _id=prefix) \
    .filter('match', _type='index-pattern')
response_index = search_index.execute()

for index in response_index:
    index.meta.id = index.meta.id.replace(
        prefix, '[template]')
    index.title = index.title.replace(prefix, '[template]')

    with open('templates/index/' + index.meta.id + '.json', 'w') as f:
        f.write(json.dumps(index.to_dict()))

for module in args.modules:
    try:
        os.mkdir('templates/' + module)
    except Exception:
        pass

    print("getting " + module + " visualizations")
    try:
        os.mkdir('templates/{0}/vis'.format(module))
    except Exception:
        pass
    search_vis = es_dsl.Search(
        using=client, index='.kibana') \
        .filter('prefix', _id=prefix + '[' + module + ']') \
        .filter('match', _type='visualization')
    response_vis = search_vis.execute()

    for vis in response_vis:
        vis.meta.id = vis.meta.id.replace(prefix, '[template]')
        vis.title = vis.title.replace(prefix, '[template]')

        source = json.loads(vis.kibanaSavedObjectMeta.searchSourceJSON)
        source['index'] = source['index'].replace(prefix, '[template]')
        vis.kibanaSavedObjectMeta.searchSourceJSON = json.dumps(source)

        with open('templates/{0}/vis/{1}.json'.format(module, vis.meta.id), 'w') as f:
            f.write(json.dumps(vis.to_dict()))

    print("getting " + module + " dashboard")
    try:
        os.mkdir('templates/{0}/dash'.format(module))
    except Exception:
        pass
    search_dash = es_dsl.Search(
        using=client, index='.kibana') \
        .filter('prefix', _id=prefix + '[' + module + ']') \
        .filter('match', _type='dashboard')
    response_dash = search_dash.execute()

    for dash in response_dash:
        dash.meta.id = dash.meta.id.replace(prefix, '[template]')
        dash.title = dash.title.replace(prefix, '[template]')

        dash_panels = json.loads(dash.panelsJSON)
        for panel in dash_panels:
            panel['id'] = panel['id'].replace(prefix, '[template]')
        dash.panelsJSON = json.dumps(dash_panels)

        with open('templates/{0}/dash/{1}.json'.format(module, vis.meta.id), 'w') as f:
            f.write(json.dumps(dash.to_dict()))
