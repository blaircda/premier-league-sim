from config import *
from tournament import *
from play_game import *
#from math import log
from time import perf_counter
from collections import defaultdict
import csv

#start = perf_counter()

########################################################################
# set up

#print("Setting up Premier League")

teams = []
elos = {}
team_short = {}
values = {}

# read team data
with open("data/teams.csv", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        team = row["team"]
        teams.append(team)
        team_short[team] = row["team_short"]
        elos[team] = int(row["elo"])
        values[team] = int(row["value"])

# store invariant data used by simulation in state dictionary
state = {
    "teams": teams,
    "elo": elos,
    "values": values
}

model_set = {
#"test": test
#        "rk_strong":ranking_poisson,
#        "val_strong":value_poisson,
#        "rk_val_both": rank_and_value,
#        "rk_tier_plus": ranking_tier_poisson_delta,
#        "val_tier_plus": value_tier_poisson_delta,
#        "log_val_tier_plus": log_value_tier_poisson_delta,
        "elo_static": elo_to_poisson,
        "elo_live":elo_to_poisson_live,
#        "val_extra_goal": value_extra_poisson,
#         "val_share_lin": value_probs_goals,
#        "val_share_elo": value_probs_elo
}

# useful to have immediate access to their names
model_names = list(model_set.keys())
# model_set = {k:v for d in all_models for k,v in d.items()}


# fixtures
fixtures = {}
with open("data/fixtures.csv", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["round"] not in fixtures:
            fixtures[row["round"]] = [(row["home"], row["away"])]
        else:
            fixtures[row["round"]].append( (row["home"], row["away"]) )

#elapsed = perf_counter() - start
#print(f"Setup finished in {elapsed:.6f} s")
########################################################################

K = len(teams)+1

def make_team_stats():
    return {i: 0 for i in range(1, K)} | {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS":0, "PTS_MAX": 0, "PTS_MIN": 1000}

def make_posn_stats():
    return {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS":0, "PTS_MAX": 0, "PTS_MIN": 1000}

# main simulation function
def run_simulations():

    store_team_results, store_posn_results = {}, {}
    
    print(f"Nsims: {Nsims}")

    Nmodels =len(model_set)
    model_count = 1

    # loop over models
    for model_name, model_fn in model_set.items():
        start = perf_counter()
        print(f"Simulating Premier League with game model: {model_name} ({model_count}/{Nmodels})")
        # dict to store basic results direct from simulaton
        team_results = defaultdict(lambda : make_team_stats())
        posn_results = {i: make_posn_stats() for i in range(1,K)}
        # run Nsims simulations with the given model
        for N in range(Nsims):
            if model_name == "elo_live":
                orig_elo = state["elo"].copy()

            results = run_season(state, model_fn, fixtures=fixtures)

            update_results(results, team_results, posn_results)

            if model_name == "elo_live":    
                state["elo"] = orig_elo.copy()

        for team in teams:
            for i in range(1,K):
                posn_results[i][team] = team_results[team][i] 


        # store invariant team data for ease of access
        # for team, res in results.items():
            #res["team"] = team
        # save results for model
        store_team_results[model_name] = team_results
        store_posn_results[model_name] = posn_results
        
        elapsed = perf_counter() - start
        print(f"Simulation finished in {elapsed:.6f} s")
        model_count += 1 

    return store_team_results, store_posn_results
    
if __name__ == '__main__':
    # run the simulations
    store_team_results, store_posn_results = run_simulations()
    #print(*[ (team, results[team]) for team in teams], sep="\n")


    for model_name, model_data in store_team_results.items():
        print(f"\nResults for model: {model_name}")
        sorted_data = { k:v for k, v in sorted(model_data.items(), key=lambda item: (item[1]["PTS"]), reverse=True)}
        padding = max([ len(team) for team in teams]) + 1
        display_stats = ["PTS", "GF", "GA", "GD"]
        display_extr = ["PTS_MAX", "PTS_MIN"]
        print(f"{'Team':<{padding}}"+ " ".join(f"{i:^5}" for i in range(1,K)) + " ".join(f"{stat:^7}" for stat in display_stats+display_extr) )      
        for team, team_data in sorted_data.items():
            print(f"{team:<{padding}}"
                  + " ".join(f"{team_data[i]*100/Nsims:<5.1f}" for i in range(1,K))
                  + " ".join(f"{team_data[stat]/Nsims:^7.0f}" for stat in display_stats)
                  + " ".join(f"{team_data[stat]:^7.0f}" for stat in display_extr)  
                  )

        posn_results = store_posn_results[model_name] 
        print(f"\n{'Posn':<{4}}"+ " ".join(f"{team_short[team]:^6}" for team in teams) + " ".join(f"{stat:^7}" for stat in display_stats+display_extr) )      
        for posn, posn_data in posn_results.items():
            print(f"{posn:<{4}}"
                  + " ".join(f"{posn_data[team]*100/Nsims:^6.2f}" for team in teams)
                  + " ".join(f"{posn_data[stat]/Nsims:^7.0f}" for stat in display_stats)
                  + " ".join(f"{posn_data[stat]:^7.0f}" for stat in display_extr)  
                  )

    # save to csv
    #save_results_to_csv(store_results, model_names)

        
#import cProfile
#import pstats
#cProfile.run("main()", "profile.out")
#stats = pstats.Stats("profile.out")
#stats.sort_stats("cumtime").print_stats(30)
