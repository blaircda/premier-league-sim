from collections import defaultdict
from play_game import *


def play(team1, team2, state, model, table, matches):
    g1,g2 = play_game(team1, team2, state, model)
    # store matches for revisiting when computing ranking of tied teams
    matches[frozenset((team1,team2))] = {team1: g1, team2:g2}
    # update table
    table[team1]["GF"] += g1
    table[team1]["GA"] += g2
    table[team2]["GF"] += g2
    table[team2]["GA"] += g1
    table[team1]["GD"] += g1-g2
    table[team2]["GD"] += g2-g1
    if (g1>g2):
        table[team1]["W"] += 1
        table[team2]["L"] += 1
        table[team1]["PTS"] += 3
    elif (g1<g2):
        table[team2]["W"] += 1
        table[team1]["L"] += 1
        table[team2]["PTS"] += 3
    else:
        table[team1]["D"] += 1
        table[team2]["D"] += 1
        table[team1]["PTS"] += 1
        table[team2]["PTS"] += 1

def run_season(state, model):
    # iterate over groups and matches therein
    ts = state["teams"]
    table = defaultdict(lambda: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS":0 })
    matches = {}

    for i in range(len(ts)):
        for j in range(i+1, len(ts)):
            team1, team2 = ts[i], ts[j]
            play(team1, team2, state, model, table, matches)
            play(team2, team1, state, model, table, matches)

    # If points and goal difference are both equal:
    # -the number of goals scored for the team ("GF")
    # - most points collected in the head-to-head matches between the tied clubs
    # - most the most away goals in the head-to-head matches

    table = list(sorted(table.items(),
        key=lambda item: (item[1]["PTS"], item[1]["GD"], item[1]["GF"]
        ), reverse=True))

    return table

def update_results(table, results):
    """
    input: table = list of tuples (team name, dict {W, D, L, GF, GA, GD, PTS})
           results = dict of dicts
    """
    for i, team_data in enumerate(table):
        team = team_data[0]
        stats = team_data[1]
        results[team][i+1] += 1
        for k, v in stats.items():
            results[team][k] += v
    
