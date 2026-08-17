from config import *
from tournament import *
from play_game import *
#from math import log
from time import perf_counter
from collections import defaultdict
import csv

start = perf_counter()

########################################################################
# set up

print("Setting up Premier League")

teams = []
#rankings = {}
#values = {}
#log_values = {}
#odds = {}
elos = {}

# read team data
with open("data/teams.csv", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        team = row["team"]
        teams.append(team)
#        values[team] = float(row["value"])
#        odds[team] = float(row["odds"])
        elos[team] = int(row["elo"])
#        log_values[team] = int(round( log(float(row["value"])),0))

#log_values = {k:v for k, v in sorted(log_values.items(), key=lambda item: item[1], reverse=True)}

# create and output team tiers
#print("Ranking tiers")
#ranking_tiers = make_show_tiers(rankings, tier_size = 8, reverse=False)

#print("Value tiers")
#value_tiers = make_show_tiers(values, tier_size = 8, reverse=True)

#print("Log value tiers")
#n = max(log_values.values())
#while n>=min(log_values.values()):
#    print("Tier", 4-n,":", end=" ")
#    for k,v in log_values.items():
#        if v==n:
#            print(k, end="  ")
#    print()
#    n=n-1
#print(" ")

# store invariant data used by simulation in state dictionary
state = {
    "teams": teams,
#    "values": values,
#    "ranking_tiers": ranking_tiers,
#    "value_tiers": value_tiers,
#    "log_value_tiers": log_values,
#    "odds": odds,
    "elo": elos
}

model_set = {
#        "rk_strong":ranking_poisson,
#        "val_strong":value_poisson,
#        "rk_val_both": rank_and_value,
#        "rk_tier_plus": ranking_tier_poisson_delta,
#        "val_tier_plus": value_tier_poisson_delta,
#        "log_val_tier_plus": log_value_tier_poisson_delta,
        "elo_static": elo_to_poisson,
#        "elo_live":elo_to_poisson_live,
#        "val_extra_goal": value_extra_poisson,
#        "val_share_lin": value_probs_goals,
#        "val_share_elo": value_probs_elo
}

# useful to have immediate access to their names
model_names = list(model_set.keys())

# model_set = {k:v for d in all_models for k,v in d.items()}

elapsed = perf_counter() - start
print(f"Setup finished in {elapsed:.6f} s")
########################################################################

# main simulation function
def run_simulations():

    store_results = {}
    
    print(f"\nNsims: {Nsims}\n")

    Nmodels =len(model_set)
    model_count = 1

    # loop over models
    for model_name, model_fn in model_set.items():
        start = perf_counter()
        print(f"Simulating Premier League with game model: {model_name} ({model_count}/{Nmodels})")
        # dict to store basic results direct from simulaton
        results_dict = defaultdict(lambda: defaultdict(int))
        # run Nsims simulations with the given model
        for N in range(Nsims):
            if model_name == "elo_live":
                orig_elo = state["elo"].copy()
            results = run_season(state, model_fn)
            update_results(results, results_dict)
            if model_name == "elo_live":    
                state["elo"] = orig_elo.copy()
        # store invariant team data for ease of access
        # for team, res in results_dict.items():
            #res["odds_diff"]  = res["champions"] - Nsims*odds[team]
            #res["ranking"] = rankings[team]
            #res["value"] = values[team]
            #res["odds"] = odds[team]
            #res["group"] = team_groups[team]
            #res["team"] = team
        # save results for model
        #store_results[model_name] = {k:v for k, v in sorted(results_dict.items(), key=lambda item: rankings[item[0]])}
        elapsed = perf_counter() - start
        print(f"Simulation finished in {elapsed:.6f} s")
        model_count += 1 

    return results_dict
    
if __name__ == '__main__':
    # run the simulations
    results = run_simulations()
    print(results)
    # save to csv
    #save_results_to_csv(store_results, outcome_data, store_finals, store_sf, model_names)

        
#import cProfile
#import pstats
#cProfile.run("main()", "profile.out")
#stats = pstats.Stats("profile.out")
#stats.sort_stats("cumtime").print_stats(30)
