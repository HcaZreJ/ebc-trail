"""解析 assets/ebc-loop.kml：大环线的 20 条导航线与 63 个标注点。

出处见 sources/15-kmz-loop-track.md。点的表示是 (lon, lat, ele)，与 KML
coordinates 的字段顺序一致。
"""
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KML = ROOT / "assets" / "ebc-loop.kml"

KML_NS = "http://www.opengis.net/kml/2.2"


def _tag(name):
    return f"{{{KML_NS}}}{name}"


def _folders_named(root, substring):
    for folder in root.iter(_tag("Folder")):
        name_el = folder.find(_tag("name"))
        name = name_el.text if name_el is not None else None
        if name and substring in name:
            yield folder


def load_lines(kml_path=KML):
    """导航线文件夹里每条 LineString 的点序列，按在 KML 里的出现顺序。"""
    root = ET.parse(str(Path(kml_path))).getroot()
    lines = []
    for folder in _folders_named(root, "导航线"):
        for placemark in folder.findall(_tag("Placemark")):
            line_string = placemark.find(_tag("LineString"))
            if line_string is None:
                continue
            coord_el = line_string.find(_tag("coordinates"))
            if coord_el is None or not coord_el.text:
                continue
            pts = []
            for token in coord_el.text.split():
                lon_s, lat_s, ele_s = token.split(",")
                pts.append((float(lon_s), float(lat_s), float(ele_s)))
            lines.append(pts)
    return lines


def load_waypoints(kml_path=KML):
    """标注点文件夹里带名称的 Point，返回 {名称: (lat, lon, ele)}。"""
    root = ET.parse(str(Path(kml_path))).getroot()
    waypoints = {}
    for folder in _folders_named(root, "标注点"):
        for placemark in folder.findall(_tag("Placemark")):
            point = placemark.find(_tag("Point"))
            if point is None:
                continue
            name_el = placemark.find(_tag("name"))
            name = name_el.text.strip() if name_el is not None and name_el.text else ""
            if not name or name in waypoints:
                continue
            coord_el = point.find(_tag("coordinates"))
            if coord_el is None or not coord_el.text:
                continue
            lon_s, lat_s, ele_s = coord_el.text.strip().split(",")
            waypoints[name] = (float(lat_s), float(lon_s), float(ele_s))
    return waypoints
