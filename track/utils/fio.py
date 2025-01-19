import json
import xml.etree.ElementTree as ET


def read_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.loads(f.read())


def write_json(file, data):
    with open(file, "w", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False, indent=2))


def read_xml(file):
    tree = ET.parse(file)
    return tree.getroot()


def write_xml(file, eletment: ET.Element):
    ET.indent(eletment)
    ET.ElementTree(eletment).write(
        file,
        encoding="utf-8",
        xml_declaration=True,
    )
