import xml.etree.ElementTree as ET
import argparse

parser = argparse.ArgumentParser(
    prog='parse_emission',
    description='Extract and process values of emissions.')

parser.add_argument('folder', help='Folder to search for model')
parser.add_argument('junction', help='Junction code one of 1001, 1002, 1003, 1004')
parser.add_argument('-n', '--names', nargs='+', default=[], help='List of emission indicators to search for')

args = parser.parse_args()
folder = args.folder
junction_code = args.junction
targets = args.names
print("folder: {} ".format(folder))
print("junction_code: {}".format(junction_code))
print("output file: model/{}/{}/output/my_emission_file.xml".format(folder, junction_code))
accum = {key: 0.0 for key in targets}
count = 0
for event, element in ET.iterparse("model/{}/{}/output/my_emission_file.xml".format(folder, junction_code), ["start"]):
    if element.tag == "vehicle":
        count += 1
        for key in element.attrib:
            if key in targets:
                accum[key] += float(element.attrib[key])

result = {key: accum[key] / count for key in targets}

print("result: {} - count: {}".format(result, count))