import re
import os

pb_path = r'C:\Users\datha\.gemini\antigravity\conversations\e47a7dc0-48fd-49be-86f7-b15922045cb5.pb'
with open(pb_path, 'rb') as f:
    data = f.read()

# Extract all printable ASCII strings of length > 200
strings = re.findall(b'[\x20-\x7E\n\r\t]{200,}', data)

app_tsx = ""
index_css = ""
types_ts = ""
api_ts = ""
use_location = ""
use_emergency = ""
use_haptics = ""

for s in strings:
    text = s.decode('ascii', errors='ignore')
    if 'import { useState, useEffect, useRef } from' in text and 'MapPin, Search, Phone' in text:
        app_tsx = text
    if '@import url(\'https://fonts.googleapis.com/css2' in text and '--bg-deep: hsl(240, 10%, 3%);' in text:
        index_css = text
    if 'RoadSoS — Shared TypeScript Interfaces' in text and 'export interface Hospital' in text:
        types_ts = text
    if 'RoadSoS — Typed API Client' in text and 'TIMEOUT_MS =' in text:
        api_ts = text
    if 'RoadSoS — Location Hook' in text and 'Multi-source: GPS' in text:
        use_location = text
    if 'RoadSoS — Emergency State Hook' in text and 'IDLE  CONFIRMING' in text:
        use_emergency = text
    if 'RoadSoS — Haptics Hook' in text and 'navigator.vibrate' in text:
        use_haptics = text

# Some strings might have weird protobuf artifacts at the ends, but we'll dump them to inspect.
with open('extracted_app.txt', 'w', encoding='utf-8') as f: f.write(app_tsx)
with open('extracted_css.txt', 'w', encoding='utf-8') as f: f.write(index_css)
with open('extracted_types.txt', 'w', encoding='utf-8') as f: f.write(types_ts)
with open('extracted_api.txt', 'w', encoding='utf-8') as f: f.write(api_ts)
with open('extracted_location.txt', 'w', encoding='utf-8') as f: f.write(use_location)
with open('extracted_emergency.txt', 'w', encoding='utf-8') as f: f.write(use_emergency)
with open('extracted_haptics.txt', 'w', encoding='utf-8') as f: f.write(use_haptics)

print("Extraction done.")
