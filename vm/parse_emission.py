import xml.etree.ElementTree as ET
import argparse
import numpy


parser = argparse.ArgumentParser(
    prog='parse_emission',
    description='Extract and process values of emissions.')

parser.add_argument('folder', help='Folder to search for model')
parser.add_argument('junction', help='Junction code one of 1001, 1002, 1003, 1004')
# parser.add_argument('scale', help='scale parameter for SUMO congestion', type=float)
# parser.add_argument('step_length', help='SUMO step length parameter', type=float)
# parser.add_argument('-n', '--names', nargs='+', default=[], help='List of emission indicators to search for')

args = parser.parse_args()
folder = args.folder
junction_code = args.junction
# print(f"folder: {folder} junction_code: {junction_code}")
timeLoss = [] 
for event, element in ET.iterparse(f"model/{folder}/{junction_code}/tripinfos.xml", ["start"]):
    if element.tag == "tripinfo":
        id_value = element.attrib["id"]
        if id_value.startswith("pt_bus"):
            timeLoss_value = element.attrib["timeLoss"]
            # print(f"id {id_value} timeLoss {timeLoss_value}")
            timeLoss.append(float(timeLoss_value))

# print(f"median: {numpy.median(timeLoss)} mean: {numpy.mean(timeLoss)}")

print(f"result: {numpy.mean(timeLoss)}")
