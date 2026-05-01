import json

log_path = r"C:\Users\datha\.gemini\antigravity\brain\ae7f3a63-c1c5-47b0-bd4a-777913a4b353\.system_generated\logs\overview.txt"
output_path = r"c:\Users\datha\OneDrive\Desktop\ROS project\scratch\master_prompt_extracted.md"

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            content = data.get("content", "")
            if "# 🌌 THE MASTER ENGINEERING PROTOCOL (v2.0)" in content:
                with open(output_path, 'w', encoding='utf-8') as out:
                    out.write(content)
                print(f"Extracted to {output_path}")
                break
        except Exception as e:
            continue
