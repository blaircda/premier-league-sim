from collections import defaultdict
from play_game import *

def play(team1, team2, state, model, table, matches):
    g1,g2 = play_game(team1, team2, state, model)
    # store matches for revisiting when computing ranking of tied teams
    matches[(team1,team2)] = {team1: g1, team2:g2}
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
    tie = 0
    # iterate over groups and matches therein
    ts = state["teams"]
    table = defaultdict(lambda: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS":0, "TPTS": 0, "TGAway": 0})
    matches = {}

    for i in range(len(ts)):
        for j in range(i+1, len(ts)):
            team1, team2 = ts[i], ts[j]
            play(team1, team2, state, model, table, matches)
            play(team2, team1, state, model, table, matches)

    # If points and goal difference are both equal:
    # the number of goals scored for the team ("GF")
    # then:
    # - most points collected in the head-to-head matches between the tied clubs
    # - the most away goals in the head-to-head matches
    
    pts = {table[team]["PTS"] for team in ts}
    if len(pts) == len(table):
        print("Tie breaking on points alone")
        pass
    else:
        print("\nTie breaking on goal difference")
        for p in pts:
            print(f"\nChecking teams tied on points {p}")
            tied_on_pts = [team for team in ts if table[team]["PTS"]==p]
            print(*[(team, table[team]) for team in tied_on_pts], sep="\n")
            goal_diffs = {table[team]["GD"] for team in tied_on_pts}
            if len(tied_on_pts) == len(goal_diffs):
                pass
            else:
                for g in goal_diffs:
                    print(f"\nChecking teams tied on points {p} with goal diff {g}")
                    tied_on_goal_diffs = [team for team in tied_on_pts if table[team]["GD"]==g]
                    print(*[(team, table[team]) for team in tied_on_goal_diffs], sep="\n")
                    goal_fors = { table[team]["GF"] for team in tied_on_goal_diffs}
                    if len(tied_on_goal_diffs) == len(goal_fors):
                        pass
                    else:
                        for h in goal_fors:
                            print(f"\nChecking teams tied on points {p} with goal diff {g} and goal for {h}")
                            tied_on_goal_fors = [team for team in tied_on_goal_diffs if table[team]["GF"]==h]
                            if len(tied_on_goal_fors) > 1:
                                h2h(tied_on_goal_fors, table, matches, criteria="points")
                        
    table = list(sorted(table.items(),
        key=lambda item: (item[1]["PTS"], item[1]["GD"], item[1]["GF"], item[1]["TPTS"], item[1]["TGAway"]
        ), reverse=True))

    print(f"\nFinal table:")
    print(*table, sep="\n")

    return table, tie


def h2h(tied_teams, table, matches, criteria):
    if criteria=="points":
        stat = "TPTS"
    elif criteria=="goals":
        stat = "TGAway"

    print(f"\nTie breaking on head-to-head {criteria} for the following:")
    print(*[(team, table[team]) for team in tied_teams], sep="\n")
    n = len(tied_teams)
    if n>2:
        print("3way tie!")

    # reset the tie breakers for the teams in questions
    for team in tied_teams:
        table[team]["TPTS"] = 0
        table[team]["TGAway"] = 0

    # compute the minileague
    # writing directly to table
    for i in range(n):
        for j in range(i+1,n):
            team1, team2 = tied_teams[i], tied_teams[j]
            tiebreak(team1, team2, table, matches, on=criteria)
            tiebreak(team2, team1, table, matches, on=criteria)
    tcrit = { table[team][stat] for team in tied_teams }

    # if the tie breaking stats are unique we are good to sort using them
    if len(tcrit) == n:
        return
    # if the tie breaking points are all equal we have to move to the next criteria
    elif len(tcrit) == 1:
        if criteria=="points":
            h2h(tied_teams, table, matches, criteria="goals")
        elif criteria=="goals":
            print("Playoff required")
    # otherwise some teams can be separated, others not, we keep trying
    # I interpret the rules as always trying to applying points criteria first to a tied group
    else:
        for i in tcrit:
            still_tied = [team for team in tied_teams if table[team][stat] == i]
            if len(still_tied) > 1:
                h2h(still_tied, table, matches, criteria="points")
                
def tiebreak(team1, team2, table, matches, on):
    print(matches[(team1, team2)])
    g1,g2 = matches[(team1,team2)][team1], matches[(team1,team2)][team2]
    # only away goals are relevant
    if on=="goals":
        table[team2]["TGAway"] += g2
    elif on=="points":
        if (g1>g2):
            table[team1]["TPTS"] += 3
        elif (g1<g2):
            table[team2]["TPTS"] += 3
        else:
            table[team1]["TPTS"] += 1
            table[team2]["TPTS"] += 1


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
    
