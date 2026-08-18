from collections import defaultdict
from play_game import *
from config import *
import itertools

def play(team1, team2, state, model, table, matches):
    """
    generates the result of team1 vs team2
    updates table and records the result in matches
    """
    g1,g2 = play_game(team1, team2, state, model)
    # store matches for revisiting when computing ranking of tied teams
    matches[(team1,team2)] = {team1: g1, team2:g2}
    # update table
    table[team1]["GF"] += g1
    table[team1]["GA"] += g2
    table[team2]["GF"] += g2
    table[team2]["GA"] += g1
    #table[team1]["GD"] += g1-g2
    #table[team2]["GD"] += g2-g1
    if (g1>g2):
        table[team1]["W"] += 1
        table[team2]["L"] += 1
        #table[team1]["PTS"] += 3
    elif (g1<g2):
        table[team2]["W"] += 1
        table[team1]["L"] += 1
        #table[team2]["PTS"] += 3
    else:
        table[team1]["D"] += 1
        table[team2]["D"] += 1
        #table[team1]["PTS"] += 1
        #table[team2]["PTS"] += 1

def run_season(state, model, fixtures = None):
    """
    simulates a season of the Premier League
    optionally can do this following the official sequence of fixtures (gameweek by gameweek)
    allowing one to update ELO ratings etc throughout the simulated season
    returns the final league table
    """
    tie = 0
    # iterate over groups and matches therein
    ts = state["teams"]
    table = defaultdict(lambda: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS":0, "TPTS": 0, "TGAway": 0})
    matches = {}

    if fixtures:
        for gameweek, games in fixtures.items():
            for pairing in games:
                play(pairing[0], pairing[1], state, model, table, matches)
    else:
        for team1, team2 in itertools.combinations(ts,2):
            play(team1, team2, state, model, table, matches)
            play(team2, team1, state, model, table, matches)

    for team in ts:
        table[team]["GD"] = table[team]["GF"] - table[team]["GA"]
        table[team]["PTS"] = 3*table[team]["W"] + table[team]["D"]
        
    # If points and goal difference are both equal:
    # the number of goals scored for the team ("GF")
    # then:
    # - most points collected in the head-to-head matches between the tied clubs
    # - the most away goals in the head-to-head matches
    
    pts = {table[team]["PTS"] for team in ts}
    if len(pts) == len(table):
        #print("Tie breaking on points alone")
        pass
    else:
        #print("\nTie breaking on goal difference")
        for p in pts:
            tied_on_pts = [team for team in ts if table[team]["PTS"]==p]
            goal_diffs = {table[team]["GD"] for team in tied_on_pts}
            #print(f"\nChecking teams tied on points {p}")
            #print(*[(team, table[team]) for team in tied_on_pts], sep="\n")
            if len(tied_on_pts) == len(goal_diffs):
                pass
            else:
                for g in goal_diffs:
                    tied_on_goal_diffs = [team for team in tied_on_pts if table[team]["GD"]==g]
                    goal_fors = { table[team]["GF"] for team in tied_on_goal_diffs}
                    #print(f"\nChecking teams tied on points {p} with goal diff {g}")
                    #print(*[(team, table[team]) for team in tied_on_goal_diffs], sep="\n")
                    if len(tied_on_goal_diffs) == len(goal_fors):
                        pass
                    else:
                        for h in goal_fors:
                            tied_on_goal_fors = [team for team in tied_on_goal_diffs if table[team]["GF"]==h]
                            #print(f"\nChecking teams tied on points {p} with goal diff {g} and goal for {h}")
                            if len(tied_on_goal_fors) > 1:
                                h2h(tied_on_goal_fors, table, matches, criteria="points")
                        
    table = list(sorted(table.items(),
        key=lambda item: (item[1]["PTS"], item[1]["GD"], item[1]["GF"], item[1]["TPTS"], item[1]["TGAway"]
        ), reverse=True))
    #print(f"\nFinal table:")
    #print(*table, sep="\n")
    return table


def h2h(tied_teams, table, matches, criteria):
    """
    input:
    tied_teams: teams that cannot be separated by PTS, GD, GD
    table: the full league table for writing tie-breaking criteria results to
    matches: the list of matches to access the head-to-head record of the tied teams
    criteria: either "points" meaning points in head-to-head matches
              or "goals" meaning AWAY goals in head-to-head matches

    the function is first called with criteria = "points"
    it tries to separate the tied_teams via this criteria, calling itself on subgroups
    once it becomes impossible for (a subgroup of the tied teams) it calls itself with the "goals" criteria
    etc.
    if no separation is possible, and if a meaningful result (relegation, European qualification) is affected, the rules call for a playoff at this point...
    ... I do not implement a playoff considering this a statistically unlikely edge case...
    (indeed technically if a meaningful result is not affected these head-to-head tiebreaks are not even meant to be invoked)
    """
    # set the key in table associated with the criteria 
    if criteria=="points":
        stat = "TPTS"
    elif criteria=="goals":
        stat = "TGAway"

    #print(f"\nTie breaking on head-to-head {criteria} for the following:")
    #print(*[(team, table[team]) for team in tied_teams], sep="\n")
    n = len(tied_teams)
    #if n>2:
    #    print(f"3way tie breaking on head-to-head {criteria} for the following:")
    #    print(*[(team, table[team]) for team in tied_teams], sep="\n")

    # reset the tie breakers for the teams in question
    for team in tied_teams:
        table[team]["TPTS"] = 0
        table[team]["TGAway"] = 0

    # compute the minileague
    # writing directly to table
    for team1, team2 in itertools.combinations(tied_teams,2):
        get_tiebreak_result(team1, team2, table, matches, criteria=criteria)
        get_tiebreak_result(team2, team1, table, matches, criteria=criteria)
        
    tcrit = { table[team][stat] for team in tied_teams }

    # if the tie breaking stats are unique we are good to sort using them
    if len(tcrit) == n:
        return
    # if the tie breaking points are all equal we have to move to the next criteria
    elif len(tcrit) == 1:
        if criteria=="points":
            h2h(tied_teams, table, matches, criteria="goals")
        elif criteria=="goals":
            pass
            #print("Playoff required")
    # otherwise some teams can be separated, others not, we keep trying
    # I interpret the rules as always trying to apply points criteria first to a tied group
    else:
        for i in tcrit:
            still_tied = [team for team in tied_teams if table[team][stat] == i]
            if len(still_tied) > 1:
                h2h(still_tied, table, matches, criteria="points")
                
def get_tiebreak_result(team1, team2, table, matches, criteria):
    """
    retrieves match data for team1 vs team2
    and writes relevant tiebreak criteria to table 
    """
    #print(matches[(team1, team2)])
    g1,g2 = matches[(team1,team2)][team1], matches[(team1,team2)][team2]
    # only away goals are relevant
    if criteria=="goals":
        table[team2]["TGAway"] += g2
    elif criteria=="points":
        if (g1>g2):
            table[team1]["TPTS"] += 3
        elif (g1<g2):
            table[team2]["TPTS"] += 3
        else:
            table[team1]["TPTS"] += 1
            table[team2]["TPTS"] += 1

def update_results(table, team_results, posn_results):
    """
    input: table = list of tuples (team name, dict {W, D, L, GF, GA, GD, PTS})
           results = dict of dicts
    """
    for i, team_data in enumerate(table):
        team = team_data[0]
        stats = team_data[1]
        pts = stats["PTS"]
        team_results[team][i+1] += 1
        for k, v in stats.items():
            if k in ["PTS", "GF", "GA", "GD"]:
                team_results[team][k] += v
                posn_results[i+1][k] += v
        if pts > team_results[team]["PTS_MAX"]:
            team_results[team]["PTS_MAX"] = pts
        if pts < team_results[team]["PTS_MIN"]:
            team_results[team]["PTS_MIN"] = pts
        if pts > posn_results[i+1]["PTS_MAX"]:
            posn_results[i+1]["PTS_MAX"] = pts
        if pts < posn_results[i+1]["PTS_MIN"]:
            posn_results[i+1]["PTS_MIN"] = pts
