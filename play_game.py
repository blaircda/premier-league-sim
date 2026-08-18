import numpy as np
from scipy.stats import skellam

def play_game(team1, team2, state, model_fn):
    """
    returns goals only
    """
    return model_fn(team1, team2, state)

def test(team1, team2, state):
    scorelines = {
        ("A", "B"): (1,0),
        ("A", "C"): (1,0),
        ("A", "D"): (1,0),
        ("B", "A"): (0,1),
        ("C", "A"): (0,1),
        ("D", "A"): (0,1),
        ("B", "C"): (0,0),
        ("B", "D"): (0,0),
        ("C", "D"): (0,0),
        ("C", "B"): (1,1),
        ("D", "B"): (1,1),
        ("D", "C"): (0,0)
    }

    return scorelines.get( (team1, team2), (0,0))
    
########################################################################
# ELO model
# see https://eloratings.net/about
# note: in Elo win expectancy, draws count as 0.5
########################################################################

# LOOKUP TABLE FOR WIN EX
diff_to_w = [round(1/( 10**(-diff/400)+1),2) for diff in range(-2000,2001)]

# LOOKUP TABLE FOR lams
win_ex_lams = {0.5: (1.4, 1.4),
 0.51: (1.4, 1.36),
 0.52: (1.4, 1.31),
 0.53: (1.4, 1.27),
 0.54: (1.4, 1.23),
 0.55: (1.4, 1.19),
 0.56: (1.4, 1.15),
 0.57: (1.4, 1.1),
 0.58: (1.4, 1.06),
 0.59: (1.4, 1.02),
 0.6: (1.4, 0.99),
 0.61: (1.4, 0.95),
 0.62: (1.4, 0.91),
 0.63: (1.4, 0.87),
 0.64: (1.4, 0.83),
 0.65: (1.4, 0.79),
 0.66: (1.4, 0.76),
 0.67: (1.4, 0.72),
 0.68: (1.4, 0.68),
 0.69: (1.4, 0.65),
 0.7: (1.4, 0.61),
 0.71: (1.4, 0.58),
 0.72: (1.4, 0.54),
 0.73: (1.4, 0.5),
 0.74: (1.4, 0.47),
 0.75: (1.4, 0.43),
 0.76: (1.6, 0.52),
 0.77: (1.6, 0.49),
 0.78: (1.6, 0.45),
 0.79: (1.6, 0.41),
 0.8: (1.8, 0.49),
 0.81: (1.8, 0.45),
 0.82: (1.8, 0.41),
 0.83: (2.0, 0.48),
 0.84: (2.0, 0.43),
 0.85: (2.2, 0.49),
 0.86: (2.2, 0.44),
 0.87: (2.4, 0.49),
 0.88: (2.4, 0.44),
 0.89: (2.6, 0.48),
 0.9: (2.6, 0.42),
 0.91: (2.6, 0.36),
 0.92: (2.8, 0.38),
 0.93: (2.8, 0.31),
 0.94: (3.0, 0.31),
 0.95: (3.2, 0.3),
 0.96: (3.2, 0.21),
 0.97: (3.6, 0.23),
 0.98: (4.0, 0.2),
 0.99: (4.8, 0.21),
 1.0: (6.8, 0.22)
}

def elo_to_poisson(team1, team2, state):
    """
    model function to simulate elo predicted result using Poisson distributions
    """
    home_adv = 38
    diff = state["elo"][team1] - state["elo"][team2] + home_adv
    wex = diff_to_w[diff+2000]
    if wex < 0.5:
        wex = round(1 - wex, 2)
    lam1, lam2 = win_ex_lams[wex]
    if(diff>0): # team1 is better
        return  np.random.poisson(lam1), np.random.poisson(lam2)
    else: # team2 is better
        return np.random.poisson(lam2), np.random.poisson(lam1)


# ELO UPDATE
# needs to be updated to clubelo (or alternative source) methodology

# clubelo.com
# points exchanged are:
# Delta = K * GD factor * (Res - Wex)
# where K = 20
# and for a win or loss
# GD factor = Sqrt(Actual GD) / Sum_{All Possible GDs} ( Sqrt(Poss. GD) Prob(Poss. GD)/Prob(Result) )
# so you need to know the prob of Poss. GD for a particular rating difference

gd_adj = [1,1,1.5,1.75] + [1+ (0.75 + (N-3)/8) for N in range(4,51)]

def update_elo(team1, team2, state, wex1, wex2, g1, g2):
    K = 20*gd_adj[abs(g1-g2)]
    if g1 > g2: # team1 wins
        Delta = round(K*wex2,0)
    elif g1 < g2: # team2 wins
        Delta = -round(K*wex1,0)
    else: # draw
        Delta = round(K*(0.5-wex1),0)

    state["elo"][team1] =  state["elo"][team1] + int(Delta)
    state["elo"][team2] =  state["elo"][team2] - int(Delta)



# turn this into a lookup table
def goal_diff_factor_sk(lambda1,lambda2):
    """
    given scorelines generated using poisson vars lambda1, lambda2
    assuming that the result was a win for team with lambda1
    we want to compute a goal difference factor defined as:
    Sum_{All Possible GDs} ( Sqrt(Poss. GD) Prob(Poss. GD)/Prob(Result) )
    """
    sum_over_goal_diffs = sum(np.sqrt(k)*skellam.pmf(k, lambda1, lambda2) for k in range(1, 20))
    prob_win =  1 - skellam.cdf(0, lambda1, lambda2)
    return sum_over_goal_diffs / prob_win

def update_club_elo(team1, team2, state, wex1, wex2, g1, g2):
    lam1, lam2 = win_ex_lams[max(wex1, wex2)]
    K = 20
    if g1 > g2: # team 1 wins
        G = np.sqrt(abs(g1-g2))*goal_diff_factor_sk(lam1,lam2)
        Delta = round(K*G*wex2,0)
    elif g1 < g2: # team2 wins
        G = np.sqrt(abs(g1-g2))*goal_diff_factor_sk(lam2,lam1)
        Delta = -round(K*G*wex1,0)
    else: # draw
        Delta = round(K*(0.5-wex1),0)

    state["elo"][team1] =  state["elo"][team1] + int(Delta)
    state["elo"][team2] =  state["elo"][team2] - int(Delta)
    
    
def elo_to_poisson_live(team1, team2, state):
    """
    model function to simulate elo predicted result using Poisson distributions
    update elo based on result
    """
    home_adv = 38
    diff = state["elo"][team1] - state["elo"][team2] + home_adv
    wex1 = diff_to_w[diff+2000]
    wex2 = round(1-wex1, 2)

    lam1, lam2 = win_ex_lams[max(wex1, wex2)]
    
    g1, g2 = np.random.poisson(lam1), np.random.poisson(lam2)

    # update elo rankings          
    if(diff>0): # team1 is better
        update_elo(team1, team2, state, wex1, wex2, g1, g2)
        return  g1, g2
    else:# team2 is better
        update_elo(team1, team2, state, wex1, wex2, g2, g1)
        return g2, g1


########################################################################
# stuff 
########################################################################
# expected values calculated using https://footystats.org/stats/common-score
lambda_home_data = 1.64
lambda_away_data = 1.33
# these imply home team wins 45%, away team wins 32%, draws 23%

# expected values - stronger home advantage
lambda_home = 1.5
lambda_away = 0.5
# these imply home team wins 62%, away team wins 12%, draws 25%

# convention: comparison > 0  means team1 is better, comparison < 0 means team2 is better
def sample_goals(*comparisons, advantage_type):
    """
    returns poisson sampled score applying advantage to multiple criteria
    input:
    *comparisons: integers e.g. rank, value difference
    advantage_type: strong, weak, dynamic
    """
    adv_params = {
                "strong": (lambda_home, lambda_away),
                "weak": (lambda_home_data, lambda_away_data),
                }
    
    for crit, strength in zip(comparisons, advantage_type):
        
        if strength == "dynamic":
            # manually set lam1, lam2 using values lookup tables
            #lam1, lam2 = tier_lams_lookup.get(abs(crit), (2,0.4) )
            # OR
            # use lam1, lam2 corresponding to win ex = 0.5,0.6, 0.7,0.8,0.9,0.95
            wex = round( ( 50 + abs(crit)*10 - (5 if abs(crit)==5 else 0))/100,2)
            lam1, lam2 = win_ex_lams[wex]
        else:
            lam1, lam2 = adv_params.get(strength, "weak")

        if crit > 0:
            return np.random.poisson(lam1), np.random.poisson(lam2)
        elif crit < 0:
            return np.random.poisson(lam2), np.random.poisson(lam1)
            
    return np.random.poisson(lam1), np.random.poisson(lam1)


########################################################################
# experimental value based models
########################################################################


def value_poisson(team1, team2, state):
    """
    favour higher value team strongly
    """
    val_diff = state["values"][team1] - state["values"][team2]
    return sample_goals(val_diff, advantage_type=["strong"]) 

def value_poisson_weak(team1, team2, state):
    """
    favour higher value team weakly
    """
    val_diff = state["values"][team1] - state["values"][team2]
    return sample_goals(val_diff, advantage_type=["weak"])

def value_extra_poisson(team1, team2, state):
    """
    score generator favouring higher valued teams
    explicitly gives an extra goal to higher valued teams with certain probability
    """
    val1, val2 = state["values"][team1], state["values"][team2]
    Delta = abs(val1-val2)/(val1+val2)
    P = 1 - Delta
    r = np.random.choice([0,1], p=[P, Delta])

    g1, g2 = value_poisson_weak(team1, team2, state)
    # give higher value team an extra goal with probability Delta
    # if val1 is close to val2 this is less likely
    if val1 > val2:
        team1_goals = g1 + r
        team2_goals = g2 
    else:
        team1_goals = g1
        team2_goals = g2 + r

    return team1_goals, team2_goals

def value_probs_goals(team1, team2, state):
    """
    score generator favouring higher valued teams
    assigns Poisson means as a function of the share of total value
    linearly interpolates between lam1, lam2 = 3,0.4 and 0.4, 3
    """
    val1, val2 = state["values"][team1], state["values"][team2]

    p1= val1/(val1+val2)
    lam_def = 0.4
    w = 2.6
    lam1, lam2 = lam_def + w*p1, lam_def + w*(1-p1)
    
    return np.random.poisson(lam1), np.random.poisson(lam2)

def value_probs_elo(team1, team2, state):
    """
    score generator favouring higher valued teams
    assigns Poisson means as a function of the share of total value
    treating the share of total value as an Elo win expectancy
    """
    val1, val2 = state["values"][team1], state["values"][team2]
    p1= round(val1/(val1+val2),2)
    if p1 < 0.5:
        p1 = round(1 - p1, 2)
    lam1, lam2 = win_ex_lams[p1]
    if(val1>val2): # team1 is better
        return  np.random.poisson(lam1), np.random.poisson(lam2)
    else:# team2 is better
        return np.random.poisson(lam2), np.random.poisson(lam1)
