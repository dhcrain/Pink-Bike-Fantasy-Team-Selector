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
        return int(float(s))
    except (ValueError, TypeError):
        return 0

def read_riders(csv_path):
    riders = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        # Compute max points and max uci_points dynamically
        max_points = max(get_number_or_0(row.get('points', 0)) for row in reader if row.get('points')) or 1
        max_uci = max(get_number_or_0(row.get('uci_points', 0)) for row in reader if row.get('uci_points')) or 1
        print(f"Max Pinkbike points: {max_points}, Max UCI points: {max_uci}")
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

def precompute_teams(riders, count, criteria_key, balance_factor=None, keep_top_percent=None):
    possible_teams = []
    total_combinations = 0

    for team in itertools.combinations(riders, count):
        total_combinations += 1
        total_value = sum(r['value'] for r in team)
        total_score = sum(r[criteria_key] for r in team)

        if total_value < BUDGET:
            team_data = {'team': team, 'value': total_value, criteria_key: total_score}

            # Precompute balance metrics if balance_factor is provided
            if balance_factor is not None:
                points_list = [rider['points'] for rider in team]
                mean_points = sum(points_list) / len(points_list)
                variance = sum((p - mean_points) ** 2 for p in points_list) / len(points_list)
                std_dev = variance ** 0.5

                # Calculate balanced score - penalize teams with high variance
                balanced_score = total_score - (std_dev / balance_factor)
                team_data['balanced_score'] = balanced_score
                team_data['std_dev'] = std_dev

                # Calculate coefficient of variation (std_dev / mean) as a balance metric
                # Lower values indicate better balance
                if mean_points > 0:
                    team_data['cv'] = std_dev / mean_points
                else:
                    team_data['cv'] = float('inf')  # Handle edge case of zero points

            possible_teams.append(team_data)

    # Sort teams appropriately based on available keys
    if balance_factor is not None:
        # Sort by balanced score
        possible_teams.sort(key=lambda t: t['balanced_score'], reverse=True)

        # If keep_top_percent is specified, filter out poor candidates
        # This will retain teams with good scores but also good balance
        if keep_top_percent and len(possible_teams) > 20:  # Only filter if we have enough teams
            # Keep top performers
            keep_count = max(20, int(len(possible_teams) * (keep_top_percent / 100.0)))
            possible_teams = possible_teams[:keep_count]
    else:
        possible_teams.sort(key=lambda t: t[criteria_key], reverse=True)

    print(f"  Generated {total_combinations} combinations, kept {len(possible_teams)} teams")
    return possible_teams

def select_best_value_team(valid_riders, criteria_key='score', balance_factor=1.5, keep_top_percent=20):
    males = [r for r in valid_riders if r['gender'] == 'male']
    females = [r for r in valid_riders if r['gender'] == 'female']
    if len(males) < MALE_COUNT or len(females) < FEMALE_COUNT:
        print(f"Not enough eligible riders: {len(males)} males, {len(females)} females.")
        return None, 0

    # We precompute balance metrics for individual gender teams
    # and filter out poorly balanced teams early by keeping only the top percentage
    female_teams = precompute_teams(females, FEMALE_COUNT, criteria_key, balance_factor, keep_top_percent)
    print(f"Found {len(female_teams)} possible female teams")

    # Precompute all possible male teams with balance metrics
    # Similarly, filter out poorly balanced teams
    male_teams = precompute_teams(males, MALE_COUNT, criteria_key, balance_factor, keep_top_percent)
    print(f"Found {len(male_teams)} possible male teams")

    # For each female team, find the best male team that fits in the remaining budget
    best_balanced_score = -1
    best_team = None
    best_spent = 0

    for f in female_teams:
        budget_left = BUDGET - f['value']
        if budget_left < 0:
            continue

        # Find the best male team under budget_left
        for m in male_teams:
            if m['value'] <= budget_left:
                # Create combined team
                combined_team = list(f['team']) + list(m['team'])

                # We still need to calculate balance for the combined team
                # as we can't simply add the balance scores of male and female teams
                points_list = [rider['points'] for rider in combined_team]
                mean_points = sum(points_list) / len(points_list)
                variance = sum((p - mean_points) ** 2 for p in points_list) / len(points_list)
                std_dev = variance ** 0.5

                # Calculate combined score and balanced score
                total_score = f[criteria_key] + m[criteria_key]
                balanced_score = total_score - (std_dev / balance_factor)

                total_spent = f['value'] + m['value']

                if (balanced_score > best_balanced_score) or (balanced_score == best_balanced_score and total_spent > best_spent):
                    best_balanced_score = balanced_score
                    best_spent = total_spent
                    best_team = combined_team

    if not best_team:
        print("No valid team found under the budget and constraints.")
        return None, 0

    return best_team, best_spent

def print_rider(r):
    print(f"{r['name']:<25} {r['gender']:<8} ${r['value']:>9,} {r['points']:>8} {r.get('uci_points',0):>8} {r['score']:>8.2f} {r['ppv']:>10.5f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: poetry run python team_selector.py <riders.csv> [balance_factor] [keep_top_percent]")
        sys.exit(1)

    balance_factor = 30.0
    if len(sys.argv) > 2:
        try:
            balance_factor = float(sys.argv[2])
            print(f"Using balance factor: {balance_factor}")
        except ValueError:
            print(f"Invalid balance factor: {sys.argv[2]}, using default of {balance_factor}")

    keep_top_percent = 30
    if len(sys.argv) > 3:
        try:
            keep_top_percent = float(sys.argv[3])
            print(f"Keeping top {keep_top_percent}% of teams by balance score")
        except ValueError:
            print(f"Invalid keep_top_percent: {sys.argv[3]}, using default of {keep_top_percent}%")

    riders = read_riders(sys.argv[1])
    team, spent = select_best_value_team(riders, 'score', balance_factor, keep_top_percent)
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


