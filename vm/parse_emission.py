import xml.etree.ElementTree as ET
import argparse

parser = argparse.ArgumentParser(
    prog='parse_emission',
    description='Extract and process values of emissions.')

parser.add_argument('-n', '--names', nargs='+', default=[], help='List of emission indicators to search for')

args = parser.parse_args()
targets = args.names
accum = {key: 0.0 for key in targets}
count = 0
for event, element in ET.iterparse("model/Terrassa/output/my_emission_file.xml", ["start"]):
    if element.tag == "vehicle":
        count += 1
        for key in element.attrib:
            if key in targets:
                accum[key] += float(element.attrib[key])

result = {key: accum[key] / count for key in targets}

print("result: {} - count: {}".format(result, count))