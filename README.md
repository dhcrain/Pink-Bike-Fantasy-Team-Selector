[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"


Download html of current Pinkbike points from 
https://www.pinkbike.com/contest/fantasy/dh/athletes/
Then run 
```bash
./run_all.sh Athletes\ -\ DH\ Fantasy.html 
```
Will see the output in the terminal. 

```bash
Selected team (total spent: $1,485,478):

Name                      Gender        Value   Points      UCI    Score        PPV
---------------------------------------------------------------------------
Ryan Pinkerton            male     $  282,726       78      433     0.69 408085.57306
Martin Maes               male     $  167,190       73      397     0.64 259414.06953
Antoine Pierron           male     $  121,304       72      339     0.61 198618.17165
Henri Kiefer              male     $  112,217       58      388     0.55 205347.58018
Nina Hoffmann             female   $  420,000       86      692     0.87 485202.70872
Monika Hrastnik           female   $  382,041       74      455     0.68 563281.19965
---------------------------------------------------------------------------
Total score: 4.038374229492651
Total points: 441
Total UCI points: 2704
```

## Balance Factor

The balance factor is an optional parameter that helps create more balanced teams by penalizing high variance in rider performance. 

**How it works:**
- The algorithm calculates the standard deviation of points across all riders in a team
- Teams with high variance (one star rider and several weak riders) get penalized
- The balanced score is calculated as: `total_score - (standard_deviation / balance_factor)`
- **Higher balance factor** = less penalty for variance = allows more unbalanced teams
- **Lower balance factor** = more penalty for variance = forces more balanced teams

**Usage:**
```bash
./run_all.sh "Athletes - DH Fantasy.html" [balance_factor] [keep_top_percent]
```

**Examples:**
- `balance_factor = 30` (default): Mild preference for balance
- `balance_factor = 10`: Strong preference for balanced teams  
- `balance_factor = 100`: Weak preference for balance, focuses more on raw score

The `keep_top_percent` parameter (default 30%) filters out poorly performing teams early to improve performance. 

