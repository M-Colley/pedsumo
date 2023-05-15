import math
import sys
import xml.etree.ElementTree as ET
xmlfile = "edgedata-file_Wildau.xml"
tree = ET.parse(xmlfile)
root = tree.getroot()

xmlfile2 = "outputdfrouter.xml"
tree2 = ET.parse(xmlfile2)
root2 = tree2.getroot()

fahrzeuganzahl={}

for elm in root.findall('interval/edge'):
    edge = elm.attrib['id']
    value = elm.attrib['departed']
    value2 = elm.attrib['entered']
    fahrzeuganzahl[edge] = int(value) + int(value2)
print(fahrzeuganzahl)

ms = 0
for elm2 in root2.findall('interval/edge'):
    edge2 = elm2.attrib['id']
    if edge2 in fahrzeuganzahl:
        value3 = elm2.attrib['departed']
        value4 = elm2.attrib['entered']
        fahrzeuganzahl2 = int(value3) + int(value4)
        differenz = fahrzeuganzahl[edge] - fahrzeuganzahl2
        ms += differenz**2
rms = math.sqrt(ms/len(fahrzeuganzahl))
print(sys.argv[0])
print(rms)
print(str(sys.argv))

