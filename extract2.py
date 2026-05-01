import os

pb_path = r'C:\Users\datha\.gemini\antigravity\conversations\e47a7dc0-48fd-49be-86f7-b15922045cb5.pb'
with open(pb_path, 'rb') as f:
    data = f.read()

text = data.decode('utf-8', errors='ignore')

def extract_block(marker):
    idx = text.find(marker)
    if idx == -1: return ''
    start_idx = text.rfind('"CodeContent":"', 0, idx)
    if start_idx != -1:
        start_idx += len('"CodeContent":"')
        end_idx = text.find('","Description"', start_idx)
        if end_idx == -1:
            end_idx = text.find('","IsArtifact"', start_idx)
        if end_idx != -1:
            code = text[start_idx:end_idx]
            return code.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t').replace('\\r', '\r').replace('\\\\', '\\')
    return ''

app_tsx = extract_block('import { useState, useEffect, useRef } from')
index_css = extract_block('@import url(\'https://fonts.googleapis.com/css2')
types_ts = extract_block('export interface ActionPlan {')
api_ts = extract_block('const BASE_URL = ')
use_loc = extract_block('export function useLocation() {')
use_emer = extract_block('export function useEmergency() {')
use_hapt = extract_block('export function useHaptics() {')
main_tsx = extract_block('createRoot(document.getElementById')
index_html = extract_block('<!DOCTYPE html>')

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f: f.write(app_tsx)
with open('frontend/src/index.css', 'w', encoding='utf-8') as f: f.write(index_css)
with open('frontend/src/types/index.ts', 'w', encoding='utf-8') as f: f.write(types_ts)
with open('frontend/src/services/api.ts', 'w', encoding='utf-8') as f: f.write(api_ts)
with open('frontend/src/hooks/useLocation.ts', 'w', encoding='utf-8') as f: f.write(use_loc)
with open('frontend/src/hooks/useEmergency.ts', 'w', encoding='utf-8') as f: f.write(use_emer)
with open('frontend/src/hooks/useHaptics.ts', 'w', encoding='utf-8') as f: f.write(use_hapt)
with open('frontend/src/main.tsx', 'w', encoding='utf-8') as f: f.write(main_tsx)
with open('frontend/index.html', 'w', encoding='utf-8') as f: f.write(index_html)

print(f"Extracted App.tsx: {len(app_tsx)} chars")
print(f"Extracted index.css: {len(index_css)} chars")
print(f"Extracted types.ts: {len(types_ts)} chars")
print(f"Extracted api.ts: {len(api_ts)} chars")
print(f"Extracted location.ts: {len(use_loc)} chars")
print(f"Extracted emergency.ts: {len(use_emer)} chars")
print(f"Extracted haptics.ts: {len(use_hapt)} chars")
print(f"Extracted main.tsx: {len(main_tsx)} chars")
print(f"Extracted index.html: {len(index_html)} chars")
