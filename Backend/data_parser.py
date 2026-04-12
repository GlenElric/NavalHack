"""
Data Parser Module
Parses raw maritime communication messages from markdown files
and structures them into a standardized format.
"""
import re
import os
import glob
import json


def parse_dms_to_decimal(dms_str):
    """Convert DMS coordinates like 13°45'N, 71°23'W to decimal."""
    pattern = r"(\d+)[°](\d+)?[']?\s*([NSEW])"
    match = re.search(pattern, dms_str)
    if not match:
        return None
    degrees = float(match.group(1))
    minutes = float(match.group(2)) if match.group(2) else 0.0
    direction = match.group(3)
    decimal = degrees + minutes / 60.0
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal


def extract_coordinates(text):
    """Extract lat/lon pairs from message text."""
    # Pattern: 13°45'N, 71°23'W  or  12°30'N TO 13°00'N, 70°45'W TO 71°15'W
    coord_pattern = r"(\d+[°]\d*[']?\s*[NS])\s*,?\s*(\d+[°]\d*[']?\s*[EW])"
    matches = re.findall(coord_pattern, text)
    coords = []
    for lat_str, lon_str in matches:
        lat = parse_dms_to_decimal(lat_str)
        lon = parse_dms_to_decimal(lon_str)
        if lat is not None and lon is not None:
            coords.append({"lat": lat, "lon": lon})
    return coords


def extract_bearing(text):
    """Extract bearing/heading from text."""
    pattern = r"(?:HEADING|BEARING|heading|bearing)\s+(\d+)[°]?"
    match = re.search(pattern, text)
    if match:
        return int(match.group(1))
    # Also check for standalone heading pattern
    pattern2 = r"HEADING\s+(\d+)"
    match2 = re.search(pattern2, text)
    if match2:
        return int(match2.group(1))
    return None


def extract_speed(text):
    """Extract speed in knots from text."""
    pattern = r"(?:SPEED|speed)\s+(?:UNKNOWN|(\d+))\s*(?:KNOTS|knots|KTS)?"
    match = re.search(pattern, text.upper())
    if match and match.group(1):
        return int(match.group(1))
    pattern2 = r"(\d+)\s*(?:KNOTS|knots|KTS)"
    match2 = re.search(pattern2, text)
    if match2:
        return int(match2.group(1))
    return None


def extract_vessel_name(text):
    """Extract vessel/entity name in quotes from text."""
    pattern = r'"([^"]+)"'
    matches = re.findall(pattern, text)
    if matches:
        return matches[0]
    # Also check escaped quotes
    pattern2 = r'\\"([^"\\]+)\\"'
    matches2 = re.findall(pattern2, text)
    if matches2:
        return matches2[0]
    return None


def classify_contact_type(text):
    """Classify the type of contact based on keywords."""
    from config import CONTACT_TYPES
    text_lower = text.lower()
    for contact_type, keywords in CONTACT_TYPES.items():
        for kw in keywords:
            if kw in text_lower:
                return contact_type
    return "unknown"


def classify_threat_level(text):
    """Classify threat level based on keywords."""
    from config import THREAT_KEYWORDS
    text_lower = text.lower()
    for kw in THREAT_KEYWORDS["high"]:
        if kw in text_lower:
            return "high"
    for kw in THREAT_KEYWORDS["medium"]:
        if kw in text_lower:
            return "medium"
    return "low"


def determine_zone(coords, zones):
    """
    Determine which maritime zone a coordinate falls in.
    Optimized with bounding box caching to avoid O(N) min/max calculations per call.
    """
    if not coords:
        return None
    lat, lon = coords[0]["lat"], coords[0]["lon"]
    for zone in zones:
        if "coordinates" not in zone or len(zone["coordinates"]) < 3:
            continue

        # Bolt: Use cached bounding box for O(1) lookup
        if "_bbox" not in zone:
            lats = [c["lat"] for c in zone["coordinates"]]
            lons = [c["lon"] for c in zone["coordinates"]]
            zone["_bbox"] = (min(lats), max(lats), min(lons), max(lons))

        min_lat, max_lat, min_lon, max_lon = zone["_bbox"]
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return zone["name"]
    return None


def parse_comm_message(raw_text, msg_id=0):
    """Parse a single communication message into structured format."""
    from config import MARITIME_ZONES

    lines = raw_text.strip().split('\n')
    from_field = ""
    to_field = ""
    priority = ""
    dtg = ""
    message_body = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("FROM:"):
            from_field = stripped[5:].strip()
        elif stripped.startswith("TO:"):
            to_field = stripped[3:].strip()
        elif stripped.startswith("PRIORITY:"):
            priority = stripped[9:].strip()
        elif stripped.startswith("DTG:"):
            dtg = stripped[4:].strip()
        else:
            message_body += stripped + " "

    message_body = message_body.strip()
    full_text = raw_text

    coordinates = extract_coordinates(full_text)
    bearing = extract_bearing(full_text)
    speed = extract_speed(full_text)
    vessel_name = extract_vessel_name(full_text)
    contact_type = classify_contact_type(full_text)
    threat_level = classify_threat_level(full_text)
    zone = determine_zone(coordinates, MARITIME_ZONES)

    return {
        "id": msg_id,
        "from": from_field,
        "to": to_field,
        "priority": priority,
        "dtg": dtg,
        "message": message_body,
        "raw_text": raw_text.strip(),
        "coordinates": coordinates,
        "bearing": bearing,
        "speed": speed,
        "vessel_name": vessel_name,
        "contact_type": contact_type,
        "threat_level": threat_level,
        "zone": zone,
        "type": "comm_message"
    }


def parse_surveillance_log(raw_text, msg_id=0):
    """Parse a surveillance log entry into structured format."""
    from config import MARITIME_ZONES

    lines = raw_text.strip().split('\n')
    date = ""
    time_val = ""
    location = ""
    report = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Date:"):
            date = stripped[5:].strip()
        elif stripped.startswith("Time:"):
            time_val = stripped[5:].strip()
        elif stripped.startswith("Location:"):
            location = stripped[9:].strip()
        elif stripped.startswith("Report:"):
            report = stripped[7:].strip()
        else:
            report += " " + stripped

    report = report.strip()
    full_text = raw_text

    coordinates = extract_coordinates(full_text)
    bearing = extract_bearing(full_text)
    speed = extract_speed(full_text)
    vessel_name = extract_vessel_name(full_text)
    contact_type = classify_contact_type(full_text)
    threat_level = classify_threat_level(full_text)
    zone = determine_zone(coordinates, MARITIME_ZONES)

    return {
        "id": msg_id,
        "date": date,
        "time": time_val,
        "location": location,
        "report": report,
        "raw_text": raw_text.strip(),
        "coordinates": coordinates,
        "bearing": bearing,
        "speed": speed,
        "vessel_name": vessel_name,
        "contact_type": contact_type,
        "threat_level": threat_level,
        "zone": zone,
        "type": "surveillance_log"
    }


def parse_md_file(file_path):
    """Parse a markdown file and extract all message blocks."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract code blocks (between ``` markers)
    blocks = re.findall(r'```\s*\n(.*?)\n\s*```', content, re.DOTALL)
    return blocks


def load_all_data(data_directory):
    """Load and parse all maritime data from a directory of markdown files."""
    all_contacts = []
    msg_id = 0

    md_files = glob.glob(os.path.join(data_directory, "*.md"))

    for file_path in sorted(md_files):
        filename = os.path.basename(file_path)
        blocks = parse_md_file(file_path)

        for block in blocks:
            block_stripped = block.strip()
            if not block_stripped:
                continue

            if block_stripped.startswith("FROM:") or "FROM:" in block_stripped[:50]:
                parsed = parse_comm_message(block_stripped, msg_id)
                all_contacts.append(parsed)
                msg_id += 1
            elif block_stripped.startswith("Date:") or "Date:" in block_stripped[:20]:
                parsed = parse_surveillance_log(block_stripped, msg_id)
                all_contacts.append(parsed)
                msg_id += 1
            elif block_stripped.startswith("{") or block_stripped.startswith("["):
                # JSON block (zones, etc.) - skip for now
                pass

    return all_contacts


def load_extracted_json(json_path):
    """Load previously extracted data from JSON file."""
    if not os.path.exists(json_path):
        return []

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    contacts = []
    for i, entry in enumerate(data):
        msg_text = entry.get("message", "")
        parsed = parse_comm_message(msg_text, msg_id=1000 + i)
        parsed["from"] = entry.get("source", parsed["from"])
        parsed["to"] = entry.get("destination", parsed["to"])
        parsed["priority"] = entry.get("priority", parsed["priority"])
        parsed["dtg"] = entry.get("date", parsed["dtg"])
        contacts.append(parsed)

    return contacts
