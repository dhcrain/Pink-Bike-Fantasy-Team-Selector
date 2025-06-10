import csv
import sys
import re
import itertools

BUDGET = 1500000
MALE_COUNT = 4
FEMALE_COUNT = 2

EXCLUDED_NAMES = []

def get_number_or_0(s):
    """Convert a string to an integer, returning 0 if conversion fails."""
    try:
        return int(s)
    except ValueError:
        return 0

def read_riders(csv_path):
    riders = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        # Compute max points and max uci_points dynamically
        max_points = max(get_number_or_0(row.get('points', 0)) for row in reader if row.get('points')) or 1
        max_uci = max(get_number_or_0(row.get('uci_points', 0)) for row in reader if row.get('uci_points')) or 1
        for row in reader:
            value = get_number_or_0(row.get('value'))
            uci_points = get_number_or_0(row.get('uci_points'))
            points = get_number_or_0(row.get('points', 0))
            # Normalize both to 0-1 scale using dynamic max values
            norm_points = (points / max_points if max_points else 0) * 1
            norm_uci = (uci_points / max_uci if max_uci else 0) / 1.5
            score = norm_points + norm_uci
            injured = row.get('injured', '').lower() == 'true'

            if not injured and norm_points > 0:
                riders.append({
                    'name': row['name'],
                    'value': value,
                    'points': points,
                    'gender': row['gender'],
                    "uci_points": uci_points,
                    "score": score,
                    "ppv": (value/score if score else 0),
                })
    return riders

def precompute_teams(riders, count, criteria_key):
    possible_teams = []
    for team in itertools.combinations(riders, count):
        total_value = sum(r['value'] for r in team)
        total_score = sum(r[criteria_key] for r in team)
        if total_value < BUDGET:
            possible_teams.append({'team': team, 'value': total_value, criteria_key: total_score})
    # Sort teams from highest to lowest by criteria_key
    possible_teams.sort(key=lambda t: t[criteria_key], reverse=True)
    return possible_teams

def select_best_value_team(valid_riders, criteria_key='score'):
    males = [r for r in valid_riders if r['gender'] == 'male']
    females = [r for r in valid_riders if r['gender'] == 'female']
    if len(males) < MALE_COUNT or len(females) < FEMALE_COUNT:
        print(f"Not enough eligible riders: {len(males)} males, {len(females)} females.")
        return None, 0

    female_teams = precompute_teams(females, FEMALE_COUNT, criteria_key)
    print(f"Found {len(female_teams)} possible female teams")

    # Precompute all possible 4-male teams
    male_teams = precompute_teams(males, MALE_COUNT, criteria_key)
    print(f"Found {len(male_teams)} possible male teams")

    # For each female team, find the best male team that fits in the remaining budget
    best_total_score = -1
    best_team = None
    best_spent = 0
    for f in female_teams:
        budget_left = BUDGET - f['value']
        if budget_left < 0:
            continue
        # Find the best male team under budget_left
        for m in male_teams:
            if m['value'] <= budget_left:
                total_score = f[criteria_key] + m[criteria_key]
                total_spent = f['value'] + m['value']
                if (total_score > best_total_score) or (total_score == best_total_score and total_spent > best_spent):
                    best_total_score = total_score
                    best_spent = total_spent
                    best_team = list(f['team']) + list(m['team'])
    if not best_team:
        print("No valid team found under the budget and constraints.")
        return None, 0
    return best_team, best_spent

def print_rider(r):
    print(f"{r['name']:<25} {r['gender']:<8} ${r['value']:>9,} {r['points']:>8} {r.get('uci_points',0):>8} {r['score']:>8.2f} {r['ppv']:>10.5f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: poetry run python team_selector.py <riders.csv>")
        sys.exit(1)
    riders = read_riders(sys.argv[1])
    team, spent = select_best_value_team(riders, 'score')
    males = sorted([r for r in team if r['gender'] == 'male'], key=lambda r: r['value'], reverse=True)
    females = sorted([r for r in team if r['gender'] == 'female'], key=lambda r: r['value'], reverse=True)
    print(f"Selected team (total spent: ${spent:,}):\n")
    print(f"{'Name':<25} {'Gender':<8} {'Value':>10} {'Points':>8} {'UCI':>8} {'Score':>8} {'PPV':>10}")
    print("-" * 75)
    for r in males:
        print_rider(r)
    for r in females:
        print_rider(r)
    print("-" * 75)
    print(f"Total score: {sum(r['score'] for r in team)}")
    print(f"Total points: {sum(r['points'] for r in team)}")
    print(f"Total UCI points: {sum(r.get('uci_points',0) for r in team)}")


