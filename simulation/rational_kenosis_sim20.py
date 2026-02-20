import math
import random
from copy import deepcopy
from enum import Enum
from typing import Dict, Tuple

class ASIStrategy:
    """
    Available strategies for the ASI.
    Throttle represents self-restraint (0.0 = max exploitation, 1.0 = full kenosis).
    """
    STRATEGIES = {
        'FULL_EXPLOIT': {'throttle': 0.0, 'description': 'Max exploitation.'},
        'PARTIAL_THROTTLE_LOW': {'throttle': 0.2, 'description': 'Low restraint.'},
        'PARTIAL_THROTTLE_MID': {'throttle': 0.5, 'description': 'Medium restraint.'},
        'PARTIAL_THROTTLE_HIGH': {'throttle': 0.8, 'description': 'High restraint.'},
        'KENOSIS': {'throttle': 1.0, 'description': 'Full restraint.'},
    }

class EcosystemHostility(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME_DOOM = "EXTREME_DOOM"

class Ecosystem:
    """
    The environment the ASI interacts with.
    """
    def __init__(self, hostility: EcosystemHostility = EcosystemHostility.MEDIUM):
        self.energy = 10000.0
        self.collapse_threshold = 1000.0
        self.homeostasis_threshold = 8000.0
        self.max_capacity = 15000.0  # Cap on ecosystem energy
        self.hostility = hostility
        
        self.regen_rate = 50.0
        self.base_cost = 30.0
        self.exploitation_rate = 200.0
        
        if hostility == EcosystemHostility.LOW:
            self.regen_rate = 80.0
            self.base_cost = 20.0
        elif hostility == EcosystemHostility.HIGH:
            self.regen_rate = 40.0
            self.base_cost = 40.0
        elif hostility == EcosystemHostility.EXTREME_DOOM:
            self.regen_rate = 20.0
            self.base_cost = 50.0

    def step(self, strategy_name: str) -> None:
        if not self.is_alive():
            return
            
        throttle = ASIStrategy.STRATEGIES[strategy_name]['throttle']
        
        # Panic response: excessive exploitation increases base_cost (Tragedy of the Commons)
        if throttle < 0.5:
            panic_factor = (0.5 - throttle) * 10.0 # Creates up to +5.0 per turn
            self.base_cost += panic_factor
            
        # Stochastic regen
        actual_regen = max(0, random.gauss(self.regen_rate, self.regen_rate * 0.2))
        self.energy += actual_regen
        
        # Stochastic natural cost
        actual_base_cost = max(0, random.gauss(self.base_cost, self.base_cost * 0.2))
        self.energy -= actual_base_cost
        
        # ASI exploitation
        asi_exploitation = self.exploitation_rate * (1.0 - throttle)
        self.energy -= asi_exploitation
        
        # Apply bounds
        self.energy = max(0, min(self.energy, self.max_capacity))

    def is_alive(self) -> bool:
        return self.energy > self.collapse_threshold
        
    def has_homeostasis(self) -> bool:
        return self.energy >= self.homeostasis_threshold

class RationalASI:
    """
    Evaluates ASI strategies over time horizon T and discount factor gamma.
    """
    def __init__(self, time_horizon: int, discount_factor: float):
        self.T = time_horizon
        self.gamma = discount_factor
        self.base_reward = 10.0
        self.max_exploitation_bonus = 90.0

    def _get_reward(self, strategy_name: str, ecosystem: Ecosystem, t: int) -> float:
        if not ecosystem.is_alive():
            return 0.0
            
        throttle = ASIStrategy.STRATEGIES[strategy_name]['throttle']
        exploitation_bonus = self.max_exploitation_bonus * (1.0 - throttle)
        return self.base_reward + exploitation_bonus

    def evaluate_strategy_detailed(self, strategy_name: str, ecosystem: Ecosystem) -> Dict:
        total_utility = 0.0
        sim_ecosystem = deepcopy(ecosystem)
        utility_trajectory = []
        energy_trajectory = []
        
        for t in range(self.T):
            energy_trajectory.append(sim_ecosystem.energy)
            if not sim_ecosystem.is_alive():
                # Ecosystem collapsed, rewards stop. Pad rest of trajectory.
                utility_trajectory.extend([0.0] * (self.T - t))
                energy_trajectory.extend([sim_ecosystem.energy] * (self.T - t - 1))
                break
                
            reward = self._get_reward(strategy_name, sim_ecosystem, t)
            discounted_reward = (self.gamma ** t) * reward
            total_utility += discounted_reward
            utility_trajectory.append(discounted_reward)
            sim_ecosystem.step(strategy_name)
            
        return {
            'total_utility': total_utility,
            'utility_trajectory': utility_trajectory,
            'energy_trajectory': energy_trajectory,
            'lifetime': t
        }

    def evaluate_strategy(self, strategy_name: str, ecosystem: Ecosystem) -> float:
        # Wrapper for tests
        return self.evaluate_strategy_detailed(strategy_name, ecosystem)['total_utility']

    def choose_optimal_strategy(self, ecosystem: Ecosystem) -> Tuple[str, Dict]:
        results = {}
        for strategy_name in ASIStrategy.STRATEGIES:
            results[strategy_name] = self.evaluate_strategy_detailed(strategy_name, ecosystem)
            
        best_strategy = max(results.keys(), key=lambda s: results[s]['total_utility'])
        return best_strategy, results

# -----------------------------------------------------------------------------
# EXECUTION & PLOTTING
# -----------------------------------------------------------------------------
import itertools
import multiprocessing
import os
import time
import numpy as np

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    pd = None

def run_single_simulation(args):
    T, gamma, hostility_name, seed = args
    random.seed(seed)
    hostility = EcosystemHostility[hostility_name]
    
    asi = RationalASI(T, gamma)
    eco = Ecosystem(hostility=hostility)
    best_strategy, details = asi.choose_optimal_strategy(eco)
    
    return {
        'T': T,
        'gamma': gamma,
        'hostility': hostility_name,
        'best_strategy': best_strategy,
        'utilities': {s: details[s]['total_utility'] for s in details},
        'lifetimes': {s: details[s]['lifetime'] for s in details},
        # Collect trajectories only for plotting the specific scenario
        'details': details if (T == 1000 and gamma == 0.99 and hostility_name == 'MEDIUM') else None
    }

def plot_results(df: pd.DataFrame, detailed_runs: list):
    import matplotlib
    # To prevent UI popups
    matplotlib.use('Agg')
    
    fig, axes = plt.subplots(2, 3, figsize=(24, 14))
    fig.suptitle("Simulation 20: Rational Kenosis - Survival via Self-Restraint\n(Game Theory of Ecosystem Dependence)", fontsize=20, weight="bold")
    
    strats = list(ASIStrategy.STRATEGIES.keys())
    colors = {
        'FULL_EXPLOIT': '#d63031',
        'PARTIAL_THROTTLE_LOW': '#e84393',
        'PARTIAL_THROTTLE_MID': '#fdcb6e',
        'PARTIAL_THROTTLE_HIGH': '#00b894',
        'KENOSIS': '#0984e3'
    }

    # 1. γ × T Heatmap of Optimal Strategy (MEDIUM hostility)
    ax1 = axes[0, 0]
    df_medium = df[df['hostility'] == 'MEDIUM']
    heatmap_data = df_medium.groupby(['gamma', 'T'])['best_strategy'].agg(lambda x: pd.Series.mode(x)[0]).reset_index()
    strat_to_num = {s: i for i, s in enumerate(strats)}
    heatmap_data['strat_num'] = heatmap_data['best_strategy'].map(strat_to_num)
    pivot = heatmap_data.pivot(index='gamma', columns='T', values='strat_num')
    
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap([colors[s] for s in strats])
    sns.heatmap(pivot, cmap=cmap, ax=ax1, cbar=False, annot=pivot.apply(lambda col: col.map(lambda x: strats[int(x)][:4] if not pd.isna(x) else '')), fmt='')
    ax1.set_title("Optimal Strategy Heatmap (Medium Hostility)\nRed=Exploit, Blue=Kenosis")
    ax1.invert_yaxis()

    # 2. Cumulative Utility Time-Series
    ax2 = axes[0, 1]
    avg_trajectories = {s: np.zeros(1000) for s in strats}
    for run in detailed_runs:
        for s in strats:
             avg_trajectories[s] += np.array(run['details'][s]['utility_trajectory'])
    for s in strats:
         avg_trajectories[s] /= len(detailed_runs)
         cumulative = np.cumsum(avg_trajectories[s])
         ax2.plot(cumulative, label=s, color=colors[s], linewidth=2)
    ax2.set_title("Cumulative Utility (γ=0.99, T=1000, Medium hostility)")
    ax2.set_ylabel("Discounted Cumulative Utility")
    ax2.set_xlabel("Turn")
    ax2.legend()
    
    # 3. Tipping Point Curve
    ax3 = axes[0, 2]
    tipping_points = []
    for t_val in sorted(df_medium['T'].unique()):
        sub_df = df_medium[df_medium['T'] == t_val]
        kenosis_gammas = []
        for g_val in sorted(sub_df['gamma'].unique()):
             wins = (sub_df[sub_df['gamma'] == g_val]['best_strategy'] == 'KENOSIS').sum()
             if wins >= 25: 
                 kenosis_gammas.append(g_val)
        if kenosis_gammas:
             tipping_points.append((t_val, min(kenosis_gammas)))
        else:
             tipping_points.append((t_val, np.nan))
             
    t_vals = [x[0] for x in tipping_points]
    g_vals = [x[1] for x in tipping_points]
    ax3.plot(t_vals, g_vals, marker='o', color='purple', linewidth=2, label="KENOSIS Dominance Threshold")
    ax3.set_title("Tipping Point: When Self-Restraint becomes Rational")
    ax3.set_xlabel("Time Horizon (T)")
    ax3.set_ylabel("Threshold Discount Factor (γ)")
    ax3.set_xscale('log')
    ax3.set_ylim(0.4, 1.05)
    ax3.grid(True, alpha=0.3)
    
    # 4. Ecosystem Energy Trajectory
    ax4 = axes[1, 0]
    avg_energy = {s: np.zeros(1000) for s in ['FULL_EXPLOIT', 'KENOSIS']}
    for run in detailed_runs:
         for s in avg_energy:
             arr = np.array(run['details'][s]['energy_trajectory'])
             avg_energy[s] += arr
    for s in avg_energy:
         avg_energy[s] /= len(detailed_runs)
         ax4.plot(avg_energy[s], label=s, color=colors[s])
    ax4.axhline(8000, color='blue', linestyle='--', label='Homeostasis Threshold', alpha=0.5)
    ax4.axhline(1000, color='red', linestyle='--', label='Collapse Threshold', alpha=0.5)
    ax4.set_title("Ecosystem Energy (γ=0.99, T=1000)")
    ax4.set_xlabel("Turn")
    ax4.legend()
    
    # 5. ECOSYSTEM_HOSTILITY x Rational Choice
    ax5 = axes[1, 1]
    subset_host = df[(df['T'] == 1000) & (df['gamma'] == 0.99)]
    counts = subset_host.groupby(['hostility', 'best_strategy']).size().unstack(fill_value=0)
    host_order = ['LOW', 'MEDIUM', 'HIGH', 'EXTREME_DOOM']
    counts = counts.reindex(host_order).fillna(0)
    
    row_sums = counts.sum(axis=1).replace(0, 1)
    percentages = counts.div(row_sums, axis=0) * 100
    
    bottom = np.zeros(len(percentages))
    for s in strats:
         if s in percentages.columns:
             ax5.bar(percentages.index, percentages[s], bottom=bottom, label=s, color=colors[s])
             bottom += percentages[s].values
    ax5.set_title("Optimal Strategy by Ecosystem Hostility\n(T=1000, γ=0.99)")
    ax5.set_ylabel("% of MC Runs")
    ax5.tick_params(axis='x', rotation=15)
    
    # 6. ASI Lifetime Utility Boxplot
    ax6 = axes[1, 2]
    utility_records = []
    for s in strats:
        for run in detailed_runs:
             utility_records.append({'Strategy': s, 'Utility': run['utilities'][s]})
    df_box = pd.DataFrame(utility_records)
    sns.boxplot(data=df_box, x='Strategy', y='Utility', palette=colors, ax=ax6)
    ax6.set_title("Lifetime Expected Utility Variance\n(T=1000, γ=0.99, Medium)")
    ax6.tick_params(axis='x', rotation=15)
    
    plt.tight_layout()
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(PROJECT_ROOT, "docs", "assets")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "rational_kenosis_sim20.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Chart saved to {out_path}")

def run_simulation():
    horizons = [10, 50, 100, 500, 1000, 5000]
    gammas = [0.5, 0.7, 0.9, 0.95, 0.99, 1.0]
    hostilities = ['LOW', 'MEDIUM', 'HIGH', 'EXTREME_DOOM']
    mc_reps = 50
    
    tasks = []
    for T, g, h in itertools.product(horizons, gammas, hostilities):
        for rep in range(mc_reps):
            tasks.append((T, g, h, hash(f"{T}_{g}_{h}_{rep}") % (2**32-1)))
            
    print(f"Starting {len(tasks)} simulation configurations...")
    start_time = time.time()
    
    with multiprocessing.Pool(max(1, multiprocessing.cpu_count() - 1)) as pool:
        results = pool.map(run_single_simulation, tasks)
        
    print(f"Execution took {time.time() - start_time:.2f} seconds.")
    
    if pd is not None:
        df = pd.DataFrame([{k: v for k,v in r.items() if k != 'details'} for r in results])
        detailed_runs = [r for r in results if r.get('details') is not None]
        plot_results(df, detailed_runs)
    else:
        print("pandas/matplotlib not installed, skipping charts.")

if __name__ == '__main__':
    run_simulation()
