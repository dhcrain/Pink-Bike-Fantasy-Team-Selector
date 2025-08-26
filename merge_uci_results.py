import csv
import sys
import requests
import io
import os
import re
import json
import difflib
from bs4 import BeautifulSoup
from dotenv import load_dotenv

MEN_UCI_URL = 'https://ucimtbworldseries.com/rankings/series/uci-dhi-world-cup/dhi-men-elite/2025'
WOMEN_UCI_URL = 'https://ucimtbworldseries.com/rankings/series/uci-dhi-world-cup/dhi-women-elite/2025'
STANDINGS_URL = 'https://www.ucimtbworldseries.com/api/athletes-standings'

def normalize_name(name):
    # Remove punctuation, spaces, and lowercase
    return re.sub(r'[^a-z0-9]', '', name.lower())

def fuzzy_match_name(name, candidates, threshold=0.8):
    """Return the best fuzzy match for name in candidates above threshold, or None."""
    best = difflib.get_close_matches(name, candidates, n=1, cutoff=threshold)
    return best[0] if best else None

def load_uci_results_from_standings(url, gender):
    """
    Fetch UCI results from the standings API and return as a dict mapping
    (lowercased name, gender) to their result row.
    """
    request_bodies = {
        'male': {"standingTypeSlug": "uci-dhi-world-cup-men-elite-overall-standings", "year": "2025"},
        'female': {"standingTypeSlug": "uci-dhi-world-cup-women-elite-overall-standings", "year": "2025"}
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:142.0) Gecko/20100101 Firefox/142.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.ucimtbworldseries.com/standings',
        'Origin': 'https://www.ucimtbworldseries.com',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
    }
    response = requests.post(url, json=request_bodies[gender], headers=headers)
    response.raise_for_status()
    data = response.json()
    results = {}
    if 'athletesStandings' in data:
        for item in data['athletesStandings']:
            name = item.get('riderFullName')
            points = item.get('total_points')
            if name and points is not None:
                norm_name = normalize_name(name)
                results[(norm_name, gender)] = {
                    'Points': str(points)  # Ensure points are string like the old function
                }
    return results

def load_uci_results_from_url(url, gender):
    """
    Fetch UCI results from a URL (HTML table) and return as a dict mapping
    (lowercased name, gender) to their result row.
    """
    response = requests.get(url)
    response.raise_for_status()
    html = response.content.decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        raise RuntimeError(f"Could not find a table in {url}")
    headers = [th.get_text(strip=True).lower() for th in table.find('tr').find_all(['th', 'td'])]
    col_map = {}
    print(f"Headers found: {headers}")

    for idx, h in enumerate(headers):
        if 'points' in h:
            col_map['points'] = idx
    if 'points' not in col_map:
        raise RuntimeError(f"Could not find 'points' column in {url}. Headers: {headers}")
    results = {}
    for row in table.find_all('tr')[1:]:  # skip header
        if row.has_attr('x-show'):
            continue  # Ignore rows with x-show attribute
        cells = row.find_all(['td', 'th'])
        if len(cells) <= col_map['points']:
            continue
        # Find the h3 tag for the rider name in this row
        h3 = row.find('h3')
        if not h3:
            continue
        name = h3.get_text(strip=True)
        norm_name = normalize_name(name)
        points = cells[col_map['points']].get_text(strip=True)
        results[(norm_name, gender)] = {
            'Points': points
        }
    return results

def merge_uci_results(riders_csv, output_csv):
    riders = []
    # men_uci_results = load_uci_results_from_url(men_uci_url, 'male')
    # women_uci_results = load_uci_results_from_url(women_uci_url, 'female')
    men_uci_results = load_uci_results_from_standings(STANDINGS_URL, 'male')
    women_uci_results = load_uci_results_from_standings(STANDINGS_URL, 'female')
    uci_results = {**men_uci_results, **women_uci_results}
    uci_names_by_gender = {
        'male': [k[0] for k in men_uci_results.keys()],
        'female': [k[0] for k in women_uci_results.keys()]
    }
    with open(riders_csv, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['uci_points']
        for row in reader:
            name_key = normalize_name(row['name'])
            gender = row.get('gender', '').strip().lower()
            uci_row = uci_results.get((name_key, gender))
            if not uci_row:
                # Try fuzzy match
                match = fuzzy_match_name(name_key, uci_names_by_gender.get(gender, []), threshold=0.6)
                if match:
                    uci_row = uci_results.get((match, gender))
            if uci_row:
                row['uci_points'] = uci_row.get('Points')
            else:
                print(f"Warning: No UCI match for ({row['name']}, {row['value']})")
                row['uci_points'] = ''
            riders.append(row)
    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in riders:
            writer.writerow(row)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python merge_uci_results.py riders.csv [output_csv]")
        sys.exit(1)
    riders_csv = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else 'riders_with_uci.csv'
    merge_uci_results(riders_csv, output_csv)
    print(f"Merged UCI results into {output_csv}")
