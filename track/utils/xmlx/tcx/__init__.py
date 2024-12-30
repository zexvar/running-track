import xml.etree.ElementTree as ET
from dataclasses import dataclass

NS_PARAMS = {
    "xmlns": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
    "xmlns:ns2": "http://www.garmin.com/xmlschemas/UserProfile/v2",
    "xmlns:ns3": "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
    "xmlns:ns4": "http://www.garmin.com/xmlschemas/ProfileExtension/v1",
    "xmlns:ns5": "http://www.garmin.com/xmlschemas/ActivityGoals/v1",
    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xsi:schemaLocation": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd",
}


def Element(tag, text=None, attrib={}, **extra):
    element = ET.Element(tag, attrib={**attrib, **extra})
    if text:
        element.text = str(text)
    return element


def SubElement(parent, tag, text=None, attrib={}, **extra):
    element = ET.SubElement(parent, tag, attrib={**attrib, **extra})
    if text:
        element.text = str(text)
    return element


def ValueElement(tag, text=None, attrib={}, **extra):
    element = ET.Element(tag, attrib={**attrib, **extra})
    if text:
        ET.SubElement(element, "Value").text = str(text)
    return element


@dataclass
class ActivityData:
    id: str


class TCX(ET.Element):
    def __init__(self, author_name=None):
        super().__init__("TrainingCenterDatabase", **NS_PARAMS)
        self.activities = SubElement(self, "Activities")
        if author_name:
            author = SubElement(self, "Author", {"xsi:type": "Application_t"})
            SubElement(author, "Name", author_name)

    def write(self, path):
        ET.indent(self)
        ET.ElementTree(self).write(
            path,
            encoding="utf-8",
            xml_declaration=True,
        )


class Activity(ET.Element):
    def __init__(self, id, sport="Running"):
        super().__init__("Activity", attrib={"Sport": sport})
        SubElement(self, "Id", text=id)


class Lap(ET.Element):
    def __init__(
        self,
        start_time,
        total_time=None,
        distance=None,
        max_speed=None,
        calories=None,
        avg_bpm=None,
        max_bpm=None,
    ):
        super().__init__("Lap", attrib={"StartTime": start_time})
        if total_time:
            SubElement(self, "TotalTimeSeconds", total_time)
        if distance:
            SubElement(self, "DistanceMeters", distance)
        if max_speed:
            SubElement(self, "MaximumSpeed", max_speed)
        if calories:
            SubElement(self, "Calories", calories)
        if avg_bpm:
            self.append(ValueElement("AverageHeartRateBpm", avg_bpm))
        if max_bpm:
            self.append(ValueElement("MaximumHeartRateBpm", max_bpm))

        self.track = SubElement(self, "Track")
        self.extension = SubElement(self, "Extensions")


class Trackpt(ET.Element):
    def __init__(self, time, lat=None, lon=None, altitude=None, distance=None, bpm=None):
        super().__init__("Trackpoint")
        SubElement(self, "Time", time)

        if lat and lon:
            position = SubElement(self, "Position")
            SubElement(position, "LatitudeDegrees", lat)
            SubElement(position, "LongitudeDegrees", lon)

        if altitude:
            SubElement(self, "AltitudeMeters", altitude)
        if distance:
            SubElement(self, "DistanceMeters", altitude)
        if bpm:
            self.append(ValueElement("HeartRateBpm", bpm))

        self.extension = SubElement(self, "Extensions")


class Extension(ET.Element):
    def __init__(self, tag, speed=None, cadence=None, watts=None):
        super().__init__(f"ns3:{tag}")
        if speed:
            SubElement(self, "ns3:Speed", speed)
        if cadence:
            SubElement(self, "ns3:RunCadence", cadence)
        if watts:
            SubElement(self, "ns3:Watts", watts)
