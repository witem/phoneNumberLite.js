from array import array
from optparse import OptionParser
from xml.dom.minidom import parseString
import re
import sys
import logging

logger = logging.getLogger('xml2meta')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# parse command line arguments
use = "Usage: %prog [options] PhoneNumberMetadata.xml"
parser = OptionParser(usage = use)
parser.add_option("-t", "--tests", dest="tests", action="store_true", default=False, help="Emit tests instead of meta data.")
options, args = parser.parse_args()

# we expect the dictionary name to be present
if len(args) < 1:
    print("Missing input file name.")
    exit(-1)

# read the input dictionary file
file = open(args[0])
data = file.read()
file.close()

def quote(x):
    return "\"" + x.replace("\\", "\\\\") + "\""

def nodeValue(x):
    if x == None:
        return ""
    return quote(x.nodeValue)

def text(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return quote("".join(rc))

def strip(x):
    return re.sub(r"\s", "", x)

def pattern(x, type):
    return strip(text(x[0].getElementsByTagName(type)[0].childNodes))

def format(x):
    if len(x) == 0:
        return ""
    if len(x) != 1:
        logger.info('Skipped availableFormats')
    # assert len(x) == 1
    result = []
    for numberFormat in x[0].getElementsByTagName("numberFormat"):
        attr = numberFormat.attributes
        pattern = nodeValue(attr.get("pattern"))
        nationalPrefixFormattingRule = nodeValue(attr.get("nationalPrefixFormattingRule"))
        format = text(numberFormat.getElementsByTagName("format")[0].childNodes)
        leadingDigits = numberFormat.getElementsByTagName("leadingDigits");
        if len(leadingDigits) > 0:
            leadingDigits = strip(text(leadingDigits[0].childNodes))
        else:
            leadingDigits = ""
        intlFormat = numberFormat.getElementsByTagName("intlFormat")
        if len(intlFormat) == 1:
            intlFormat = text(intlFormat[0].childNodes)
        else:
            assert len(intlFormat) == 0
            intlFormat = "";

        result.append("[" + ",".join([pattern, format, leadingDigits, nationalPrefixFormattingRule, intlFormat]) + "]")
    return "[" + ",".join(result) + "]"

# go through the phone number meta data and convert and filter it into a JS file we will include
dom = parseString(data)
territories = dom.getElementsByTagName("phoneNumberMetadata")[0].getElementsByTagName("territories")[0].getElementsByTagName("territory")
map = {}
examples = []
for territory in territories:
    attr = territory.attributes
    region = nodeValue(attr.get("id"))
    countryCode = nodeValue(attr.get("countryCode"))
    internationalPrefix = nodeValue(attr.get("internationalPrefix"))
    nationalPrefix = nodeValue(attr.get("nationalPrefix"))
    nationalPrefixForParsing = strip(nodeValue(attr.get("nationalPrefixForParsing")))
    nationalPrefixTransformRule = nodeValue(attr.get("nationalPrefixTransformRule"))
    if region == '"BR"':
        nationalPrefixForParsing = '"(?:0|90)(?:(1[245]|2[135]|[34]1)(\\\\d{10,11}))?"'
    nationalPrefixFormattingRule = nodeValue(attr.get("nationalPrefixFormattingRule"))
    nationalPattern = pattern(territory.getElementsByTagName("generalDesc"), "nationalNumberPattern")
    formats = format(territory.getElementsByTagName("availableFormats"))
    mainCountryForCode = nodeValue(attr.get("mainCountryForCode"))
    if not countryCode in map:
        map[countryCode] = []
    map[countryCode].append("'[{0},{1},{2},{3},{4},{5},{6},{7}]'".format(region,
                                                                             internationalPrefix,
                                                                             nationalPrefix,
                                                                             nationalPrefixForParsing,
                                                                             nationalPrefixTransformRule,
                                                                             nationalPrefixFormattingRule,
                                                                             nationalPattern,
                                                                             formats))
    if len(map[countryCode]) > 1 and mainCountryForCode == "\"true\"":
        x = map[countryCode]
        t = x[0]
        x[0] = x[len(x)-1]
        x[len(x)-1] = t
    if region != "\"001\"":
        for example in territory.getElementsByTagName("exampleNumber"):
            examples.append("Parse({0}, {1});".format(text(example.childNodes), region))

print("/* Automatically generated. Do not edit. */")
output = []

if options.tests:
    for example in examples:
        print(example)
    sys.exit()

print("module.exports = {");
for cc in map:
    entry = map[cc]
    if len(entry) > 1:
        output.append(cc + ": [" + ",".join(entry) + "]")
    else:
        output.append(cc + ": " + entry[0])
for line in output:
    print(line + ",")
print("};")
