import sys
import csv
import re
import json

def extract_aAthletesKeyed_from_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    # Find the JS variable aAthletesKeyed = {...};
    match = re.search(r'let aAthletesKeyed\s*=\s*(\{.*?\});', html, re.DOTALL)
    if not match:
        raise ValueError('Could not find aAthletesKeyed JS variable in the HTML file.')
    js_obj = match.group(1)
    # Fix for single-line JS objects (remove trailing commas, etc.)
    js_obj = re.sub(r',\s*([}\]])', r'\1', js_obj)
    # Parse as JSON
    data = json.loads(js_obj)
    return data

def parse_riders_from_aAthletesKeyed(data):
    riders = []
    for athlete in data.values():
        name = f"{athlete.get('firstname', '').strip()} {athlete.get('lastname', '').strip()}"
        value = int(athlete.get('value', 0)) if athlete.get('value') else None
        points = int(athlete.get('totalpoints', 0)) if athlete.get('totalpoints') else 0
        gender = 'female' if athlete.get('gender') == '2' else 'male'
        injured = bool(athlete.get('injury'))
        riders.append({
            'name': name,
            'value': value,
            'points': points,
            'gender': gender,
            'injured': injured
        })
    return riders

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python file_parser.py <html_file> [output_csv]")
        sys.exit(1)
    file_path = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "riders.csv"
    data = extract_aAthletesKeyed_from_html(file_path)
    riders = parse_riders_from_aAthletesKeyed(data)
    print(f"Found {len(riders)} riders.")
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'value', 'points', 'gender', 'injured']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for rider in riders:
            writer.writerow(rider)
    print(f"Riders written to {output_csv}")
