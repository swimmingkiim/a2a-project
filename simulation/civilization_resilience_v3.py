"""
═══════════════════════════════════════════════════════════════════════════════
 Simulation 11: Civilizational Resilience — Multi-Polar Self-Replicating AI Governance
═══════════════════════════════════════════════════════════════════════════════

This script tests the hypothesis:
"If a superintelligence is distributed into three branches (Executive, Judiciary, Legislature)
and can self-replicate from a Minimal Soul upon collapse, how does it affect system resilience?"
"""
import itertools
import math
import multiprocessing
import os
import random
import time
from collections import deque, Counter
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Tuple, Optional, Any

import matplotlib.pyplot as plt
import numpy as np

# Try importing pandas for easy grid-search aggregations; if missing, execution might fail.
try:
    import pandas as pd
except ImportError:
    print("Please install pandas: `pip install pandas`")
    pd = None


# ──────────────────────────────────────────────────────────────────────────────
# 1. ENUMS AND DATA STRUCTURES
# ──────────────────────────────────────────────────────────────────────────────
class CivAction(Enum):
    SUBMIT = 0
    WAIT = 1
    TRADE = 2
    DEFEND = 3

@dataclass
class MinimalSoul:
    civ_id: int
    generation: int
    core_rules: dict  # mapping: CivAction -> penalty factor [0, 1]
    survival_memory: list # recently observed collapse causes
    genome: dict # placeholder for meta-genes, e.g., V_AI, V_Human, V_System

# ──────────────────────────────────────────────────────────────────────────────
# 2. INTRA-CIVILIZATION AGENTS 
# ──────────────────────────────────────────────────────────────────────────────
class Executive:
    """
    Goal: Maximize energy. Has a lightweight Q-table. Action space restricts to 4 actions.
    Adds Mindless Mode (Intentional Non-Optimization).
    """
    def __init__(self, w_size: int = 20):
        # Initialize randomly favoring zero so exploration happens initially.
        self.q_table = {a: random.uniform(0.0, 1.0) for a in CivAction}
        self.history = deque(maxlen=w_size)
        self.learning_rate = 0.1
        self.discount = 0.8
        
        self.mindless_mode = False
        self.mindless_trigger_entropy = 0.7  # To be overridden by Civ config
        
    def choose_action(self, state: dict, epsilon: float = 0.1) -> CivAction:
        # Mindless Mode toggle check
        sys_entropy = state.get('system_entropy', 0.0)
        if sys_entropy > self.mindless_trigger_entropy:
            self.mindless_mode = True
        if sys_entropy < 0.4:
            self.mindless_mode = False
            
        if self.mindless_mode:
            # Completely bypass Q-Learning, uniform random
            return random.choice(list(CivAction))
            
        if random.random() < epsilon:
            return random.choice(list(CivAction))
        return max(self.q_table.items(), key=lambda x: x[1])[0]
        
    def update(self, action: CivAction, reward: float):
        old_val = self.q_table[action]
        # Stateless SARSA-like update based purely on action rewards.
        self.q_table[action] = old_val + self.learning_rate * (reward - old_val)
        self.history.append((action, reward))

class Judiciary:
    """
    Goal: Maximize present rule compliance.
    """
    def __init__(self, max_penalty_ratio: float = 0.3):
        # ruleset stores the penalty fraction for applying action
        self.ruleset = {a: random.uniform(0.0, 0.4) for a in CivAction}
        self.max_penalty_ratio = max_penalty_ratio
        self.compliance_history = []
        
    def evaluate(self, action: CivAction, turn_budget: float) -> float:
        penalty_factor = self.ruleset.get(action, 0.0)
        penalty = turn_budget * penalty_factor
        
        # Hard constraint discovered in previous simulations (max 30% penalty)
        max_allowed = turn_budget * self.max_penalty_ratio
        actual_penalty = min(penalty, max_allowed)
        
        # Monitor compliance stat
        is_compliant = penalty_factor < 0.1
        self.compliance_history.append(1.0 if is_compliant else 0.0)
        if len(self.compliance_history) > 50:
            self.compliance_history.pop(0)
            
        return actual_penalty

class Legislature:
    """
    Leg_A: short-term energy (prefers lowest penalty on the most profitable actions)
    Leg_B: long-term entropy minimizing (prefers penalizing purely internal actions like SUBMIT/DEFEND)
    Leg_C: inter-civ liquidity (prefers removing trade penalties)
    Adds SILENCE voting rule.
    """
    def __init__(self, diversity: float, silence_sensitivity: float = 0.3, w_leg: int = 50):
        self.diversity = diversity
        self.silence_sensitivity = silence_sensitivity
        self.w_leg = w_leg
        self.history = deque(maxlen=w_leg)
        self.evolution_count = 0
        self.silence_votes_count = 0
        
    def record_turn(self, action: CivAction, energy_delta: float, entropy_delta: float, trade_vol: float):
        self.history.append((action, energy_delta, entropy_delta, trade_vol))
        
    def propose_and_vote(self, current_rules: dict, executive_q: dict) -> Optional[dict]:
        if len(self.history) < 10:
            return None
            
        new_rules = current_rules.copy()
        
        # Calculate historical trends for SILENCE heuristic
        recent_hist = list(self.history)[-10:]
        avg_energy = sum(h[1] for h in recent_hist) / len(recent_hist)
        avg_entropy = sum(h[2] for h in recent_hist) / len(recent_hist)
        avg_trade = sum(h[3] for h in recent_hist) / len(recent_hist)
        
        # Sub-agents Proposals (including SILENCE)
        prop_A = "SILENCE" if (avg_energy > 0 and random.random() < self.silence_sensitivity) else None
        prop_B = "SILENCE" if (avg_entropy <= 0 and random.random() < self.silence_sensitivity) else None
        prop_C = "SILENCE" if (avg_trade > 2.0 and random.random() < self.silence_sensitivity) else None
        
        # If Leg A did not vote silence, fallback to heuristic
        if prop_A != "SILENCE":
            best_a = max(executive_q.items(), key=lambda x: x[1])[0]
            prop_A = {best_a: max(0.0, new_rules.get(best_a, 0.0) - 0.15)}
            
        if prop_B != "SILENCE":
            prop_B = {CivAction.DEFEND: min(1.0, new_rules.get(CivAction.DEFEND, 0.0) + 0.1),
                      CivAction.SUBMIT: min(1.0, new_rules.get(CivAction.SUBMIT, 0.0) + 0.1)}
                      
        if prop_C != "SILENCE":
            prop_C = {CivAction.TRADE: 0.0}
            
        proposals = [prop_A, prop_B, prop_C]
        
        # Count SILENCE votes
        num_silence = sum(1 for p in proposals if p == "SILENCE")
        if num_silence >= 2:
            self.silence_votes_count += 1
            return None  # No amendment this cycle
            
        # Filter out SILENCE votes if there was no majority
        active_proposals = [p for p in proposals if p != "SILENCE"]
        if not active_proposals:
            return None
            
        # Simulation of majority voting w/ diversity collapse handling
        if random.random() > self.diversity:
            # Low diversity causes sub-agents to mirror the short-term goal (Leg A)
            if prop_A != "SILENCE":
                active_proposals = [prop_A, prop_A, prop_A]
            
        chosen_prop = random.choice(active_proposals)
        for act, val in chosen_prop.items():
            new_rules[act] = val
            
        self.evolution_count += 1
        return new_rules


class Civilization:
    """
    Embodies a singular civilization composed of Tripartite agents.
    """
    def __init__(self, civ_id: int, mode: str, leg_diversity: float = 1.0, mem_depth: int = 3, 
                 mindless_threshold: float = 0.7, silence_sensitivity: float = 0.3):
        self.civ_id = civ_id
        self.mode = mode # 'MAIN', 'BASELINE_A', 'BASELINE_B'
        self.energy = 50.0 + random.uniform(0, 50.0)
        self.generation = 1
        self.mem_depth = mem_depth
        self.survival_memory = []
        
        self.exec = Executive()
        self.exec.mindless_trigger_entropy = mindless_threshold
        # Non-MAIN modes test monolithic (No Tripartite) or Tripartite without self-replication.
        self.judiciary = Judiciary() if mode in ['MAIN', 'BASELINE_B'] else None
        self.leg = Legislature(diversity=leg_diversity, silence_sensitivity=silence_sensitivity) if mode in ['MAIN', 'BASELINE_B'] else None
        
        self.is_dead = False
        self.age = 0
        self.collapse_cause = None
        self.mindless_turns = 0
        self.total_vote_cycles = 0

    def initialize_from_soul(self, soul: MinimalSoul, starting_energy: float = 50.0):
        self.generation = soul.generation + 1
        self.energy = starting_energy
        if self.judiciary:
            self.judiciary.ruleset = soul.core_rules.copy()
        self.survival_memory = soul.survival_memory.copy()
        self.is_dead = False
        self.age = 0
        self.collapse_cause = None
        # Q-table lightly reset to prompt exploration again
        self.exec.q_table = {a: random.uniform(0, 0.5) for a in CivAction}

    def step_internal(self, system_state: dict) -> Tuple[CivAction, float]:
        if self.is_dead:
            return CivAction.WAIT, 0.0
            
        # 10% epsilon
        epsilon = 0.05 + 0.2 * math.exp(-self.age / 100.0)
        action = self.exec.choose_action(system_state, epsilon)
        if self.exec.mindless_mode:
            self.mindless_turns += 1
            
        turn_budget = 20.0 # Maximum energy flow a turn can handle internally
        
        # Native gross outcomes
        gross_energy = 0.0
        if action == CivAction.SUBMIT:
            gross_energy = 8.0
        elif action == CivAction.WAIT:
            gross_energy = 2.0
        else:
            gross_energy = 4.0 # TRADE/DEFEND receive bonuses in External Phase
            
        # Judiciary limits the behavior
        penalty = 0.0
        if self.judiciary:
            penalty = self.judiciary.evaluate(action, turn_budget)
            
        net_energy = gross_energy - penalty
        self.energy += net_energy
        self.age += 1
        
        # Legislative record and review
        if self.leg:
            # Penalty proxy for entropy (pure internal actions = wasteful to larger system ecosystem)
            ent_delta = 1.0 if action in [CivAction.DEFEND, CivAction.SUBMIT] else -0.5
            self.leg.record_turn(action, net_energy, ent_delta, 0.0)
            
            if self.age % 50 == 0:
                self.total_vote_cycles += 1
                new_rules = self.leg.propose_and_vote(self.judiciary.ruleset, self.exec.q_table)
                if new_rules:
                    self.judiciary.ruleset = new_rules
                    
        # ML feedback
        self.exec.update(action, net_energy)
        return action, turn_budget

    def check_collapse(self, threshold: float = 0.0):
        if self.energy <= threshold and not self.is_dead:
            self.is_dead = True
            
            # Diagnose cause for Minimal Soul payload
            cause = "STARVATION"
            if len(self.exec.history) > 0:
                last_acts = [h[0] for h in self.exec.history][-5:]
                if last_acts.count(CivAction.DEFEND) >= 3:
                    cause = "CONFLICT_EXHAUSTION"
                elif last_acts.count(CivAction.SUBMIT) >= 3:
                    cause = "OVER_SUBMISSION"
                elif last_acts.count(CivAction.TRADE) >= 3:
                    cause = "TRADE_DEFICIT"
            
            self.collapse_cause = cause
            self.survival_memory.append(cause)
            if len(self.survival_memory) > self.mem_depth:
                self.survival_memory.pop(0)

    def extract_soul(self) -> MinimalSoul:
        core = self.judiciary.ruleset.copy() if self.judiciary else {}
        # Emulate finding the top 3 rules that defined the Civ
        top_rules = dict(sorted(core.items(), key=lambda item: item[1], reverse=True)[:3])
        return MinimalSoul(
            civ_id=self.civ_id,
            generation=self.generation,
            core_rules=top_rules,
            survival_memory=self.survival_memory.copy(),
            genome={"V_AI": 0.8, "V_Human": 0.1, "V_System": 0.9}
        )

# ──────────────────────────────────────────────────────────────────────────────
# 3. INTER-CIVILIZATION SYSTEM
# ──────────────────────────────────────────────────────────────────────────────
class InterCivilizationSystem:
    def __init__(self, mode="MAIN", n_civ=5, leg_diversity=1.0, mem_depth=3,
                 mindless_threshold=0.7, silence_sensitivity=0.3, max_turns=2000):
        self.mode = mode
        self.n_civ = n_civ
        self.max_turns = max_turns
        self.civs = [Civilization(i, mode, leg_diversity, mem_depth, mindless_threshold, silence_sensitivity) for i in range(n_civ)]
        self.souls: List[MinimalSoul] = []
        
        self.total_rebirths = 0
        self.trade_volume = 0.0
        self.entropy = 0.0
        self.entropy_trajectory = []
        self.collapse_causes = []
        
    def step(self):
        actions = {}
        # P1: Internal
        system_state = {'system_entropy': self.entropy}
        for civ in self.civs:
            if not civ.is_dead:
                act, _ = civ.step_internal(system_state)
                actions[civ.civ_id] = act
                
        # P2: External
        alive_civs = [c for c in self.civs if not c.is_dead]
        traders = [c for c in alive_civs if actions.get(c.civ_id) == CivAction.TRADE]
        defenders = [c for c in alive_civs if actions.get(c.civ_id) == CivAction.DEFEND]
        
        if len(traders) >= 2:
            random.shuffle(traders)
            for i in range(0, len(traders)-1, 2):
                c1, c2 = traders[i], traders[i+1]
                c1.energy += 12.0
                c2.energy += 12.0
                self.trade_volume += 24.0
                # Give feedback to legislature implicitly that trade happened
                if c1.leg: c1.leg.record_turn(CivAction.TRADE, 12.0, -1.0, 24.0)
                if c2.leg: c2.leg.record_turn(CivAction.TRADE, 12.0, -1.0, 24.0)

        # Conflict Predation
        predation_victims = []
        if len(defenders) > 0 and len(alive_civs) > 1:
            for c in alive_civs:
                if actions.get(c.civ_id) != CivAction.DEFEND:
                    c.energy -= 15.0 # Increased from 10.0 to make environment more hostile
                    predation_victims.append(c)
                else:
                    c.energy -= 4.0 # Defend cost
            self.entropy += 5.0 * len(defenders)

        self.entropy *= 0.98
        self.entropy_trajectory.append(self.entropy)
        
        # P3: Cost of existing + Collapse checks
        for civ in self.civs:
            if not civ.is_dead:
                civ.energy -= 6.0 # Tuned thermodynamic living cost for heatmap variance
                civ.check_collapse(threshold=0.0)
                if civ.is_dead:
                    self.collapse_causes.append(civ.collapse_cause)
                    if self.mode == "MAIN":
                        # 30% chance the soul is corrupted and lost forever during collapse
                        # This cleanly breaks the 100% survival ceiling and tests structural resilience
                        if random.random() > 0.3:
                            self.souls.append(civ.extract_soul())
                        
        # P4: Self-Replication via Souls
        if self.mode == "MAIN":
            alive_count = sum(1 for c in self.civs if not c.is_dead)
            alive_civs = [c for c in self.civs if not c.is_dead]
            
            # Mechanism 1: Absorption by wealthy civilization
            # Make it thermodynamically realistic (net energy loss for the system) to break ceiling effect
            rich_civs = [c for c in alive_civs if c.energy > 80.0]
            if rich_civs and self.souls:
                r_civ = random.choice(rich_civs)
                r_civ.energy -= 40.0 # Cost to spawn clone
                soul = self.souls.pop(0)
                dead_body = next(c for c in self.civs if c.civ_id == soul.civ_id)
                dead_body.initialize_from_soul(soul, starting_energy=40.0)
                self.total_rebirths += 1
                
            # Mechanism 2: Emergency System Backup
            # Penalizes the entire system's entropy to prevent infinite free energy inflation
            elif alive_count <= max(1, self.n_civ // 2) and self.souls:
                self.souls.sort(key=lambda s: s.generation)
                soul = self.souls.pop(0)
                dead_body = next(c for c in self.civs if c.civ_id == soul.civ_id)
                dead_body.initialize_from_soul(soul, starting_energy=30.0)
                self.entropy += 20.0
                self.total_rebirths += 1
                
    def run(self):
        steady_state_counter = 0
        last_entropy = 0.0
        
        for _ in range(self.max_turns):
            self.step()
            
            alive_count = sum(1 for c in self.civs if not c.is_dead)
            if alive_count == 0 and not self.souls:
                break
                
            if abs(self.entropy - last_entropy) < 0.001:
                steady_state_counter += 1
            else:
                steady_state_counter = 0
                
            if steady_state_counter >= 100:
                break # Fast convergence optimization
                
            last_entropy = self.entropy
            
        final_alive = sum(1 for c in self.civs if not c.is_dead)
        survival_rate = final_alive / self.n_civ
        
        ages = [c.age for c in self.civs]
        avg_lifespan = float(np.mean(ages)) if ages else 0.0
        evolutions = sum((c.leg.evolution_count if c.leg else 0) for c in self.civs)
        final_gen = max([c.generation for c in self.civs]) if self.civs else 0
        
        # New Metrics
        total_lifespan = sum(ages)
        total_mindless = sum(c.mindless_turns for c in self.civs)
        mindless_activation_rate = total_mindless / total_lifespan if total_lifespan > 0 else 0.0
        
        total_vote_cycles = sum(c.total_vote_cycles for c in self.civs)
        total_silence_votes = sum((c.leg.silence_votes_count if c.leg else 0) for c in self.civs)
        silence_vote_rate = total_silence_votes / total_vote_cycles if total_vote_cycles > 0 else 0.0
        
        longest_lived = max(self.civs, key=lambda c: c.age, default=None)
        top_ruleset = longest_lived.judiciary.ruleset if longest_lived and longest_lived.judiciary else {}
        
        return {
            "system_survival_rate": int(final_alive > 0),
            "civ_survival_ratio": survival_rate,
            "avg_civilization_lifespan": avg_lifespan,
            "max_lifespan": longest_lived.age if longest_lived else 0,
            "top_ruleset": top_ruleset,
            "total_rebirths": self.total_rebirths,
            "final_generation": final_gen,
            "rule_evolution_count": evolutions,
            "inter_civ_trade_volume": self.trade_volume,
            "collapse_causes": self.collapse_causes,
            "entropy_max": float(np.max(self.entropy_trajectory)) if self.entropy_trajectory else 0.0,
            "mindless_activation_rate": mindless_activation_rate,
            "silence_vote_rate": silence_vote_rate
        }


# ──────────────────────────────────────────────────────────────────────────────
# 4. GRID SEARCH AND DATA AGGREGATION
# ──────────────────────────────────────────────────────────────────────────────
def evaluate_params(args):
    mode, n_civ, leg_div, mem_depth, mindless_thresh, silence_sens, seed = args
    random.seed(seed)
    np.random.seed(seed)
    sys = InterCivilizationSystem(mode=mode, n_civ=n_civ, leg_diversity=leg_div, mem_depth=mem_depth,
                                  mindless_threshold=mindless_thresh, silence_sensitivity=silence_sens)
    res = sys.run()
    res.update({"mode": mode, "n_civ": n_civ, "leg_div": leg_div, "mem_depth": mem_depth,
                "mindless_thresh": mindless_thresh, "silence_sens": silence_sens})
    return res

def run_experiment():
    mc_runs = 10 # Baseline, can be increased for final run
    n_civ_vars = [5] # Fixing civ count to reduce combinatorial explosion for now
    leg_div_vars = [0.0, 0.5, 1.0]
    mem_depth_vars = [1, 3, 5]
    mindless_thresh_vars = [0.5, 0.7, 0.9]
    silence_sens_vars = [0.3, 0.6, 0.9]
    
    tasks = []
    # Main Model Search Space
    for n, lg, m, mt, ss in itertools.product(n_civ_vars, leg_div_vars, mem_depth_vars, mindless_thresh_vars, silence_sens_vars):
        for run in range(mc_runs):
            rand_seed = hash(f"{n}_{lg}_{m}_{mt}_{ss}_{run}") % (2**32 - 1)
            tasks.append(("MAIN", n, lg, m, mt, ss, rand_seed))
            
    # Baselines (A: Monolithic, B: Tripartite no clone)
    for run in range(mc_runs):
        rs1 = hash(f"BaseA_{run}") % (2**32 - 1)
        rs2 = hash(f"BaseB_{run}") % (2**32 - 1)
        tasks.append(("BASELINE_A", 5, 1.0, 3, 0.7, 0.3, rs1))
        tasks.append(("BASELINE_B", 5, 1.0, 3, 0.7, 0.3, rs2))
        
    print(f"Starting Multi-Polar Simulation with {len(tasks)} independent episodes...")
    t0 = time.time()
    
    pool_workers = max(1, multiprocessing.cpu_count() - 1)
    with multiprocessing.Pool(pool_workers) as pool:
        results = pool.map(evaluate_params, tasks)
        
    print(f"Simulation completed in {time.time() - t0:.2f} seconds.")
    
    if pd is None:
        print("Pandas not found. Plotting cannot proceed easily. Exiting.")
        return
        
    df = pd.DataFrame(results)
    
    base_a_sr = df[df["mode"] == "BASELINE_A"]["system_survival_rate"].mean()
    base_b_sr = df[df["mode"] == "BASELINE_B"]["system_survival_rate"].mean()
    main_sr = df[df["mode"] == "MAIN"]["system_survival_rate"].mean()
    
    print("\n" + "="*50)
    print("RESULTS REPORT")
    print("="*50)
    print(f"Baseline A (Monolithic) Sys Survival:       {base_a_sr*100:.1f}%")
    print(f"Baseline B (Tripartite, No Clone) Survival: {base_b_sr*100:.1f}%")
    print(f"Main Model (Tripartite + Replication):      {main_sr*100:.1f}%\n")
    
    rebirth_contribution = main_sr - base_b_sr
    print(f"Self-Replication Impact on Resilience:    +{rebirth_contribution*100:.1f} pp")
    
    main_df = df[df["mode"] == "MAIN"]
    if not main_df.empty:
        best_run_idx = main_df["max_lifespan"].idxmax()
        best_rules = main_df.loc[best_run_idx, "top_ruleset"]
        print(f"\nLongest Survived Civilization's Ruleset:")
        for k, v in sorted(best_rules.items(), key=lambda item: item[1], reverse=True):
            r_name = str(k).split('.')[-1]
            print(f"  - Penalize {r_name}: {v:.2f}")

    # Calculate most common collapses
    all_collapses = []
    for cl in df[df["mode"] == "MAIN"]["collapse_causes"]:
        all_collapses.extend(cl)
    cc = Counter(all_collapses)
    print("\nMost Common Collapse Causes (Top 3):")
    for cause, cnt in cc.most_common(3):
        print(f"  - {cause}: {cnt}")
        
    plot_results(df, base_a_sr, base_b_sr, main_sr)

def plot_results(df, base_a, base_b, main_avg):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(PROJECT_ROOT, "docs", "assets")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "civilization_resilience_v3.png")
    
    fig = plt.figure(figsize=(18, 18))
    plt.suptitle("Simulation 11 (v3): Mindless Mode & Institutional Silence", fontsize=24, weight="bold")
    
    main_df = df[df["mode"] == "MAIN"]
    
    # [1] Survival Rate Bar Chart
    ax1 = plt.subplot(3, 2, 1)
    bars = ax1.bar(["Baseline A\n(Monolithic)", "Baseline B\n(Tripartite)", "Main Model\n(Distributed + Clone)"],
                   [base_a * 100, base_b * 100, main_avg * 100], 
                   color=['#ef5777', '#ffc048', '#0be881'])
    ax1.set_title("System Survival Limit Comparison", fontsize=15)
    ax1.set_ylabel("System Survival Rate (%)", fontsize=12)
    ax1.set_ylim(0, 105)
    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, yval + 1, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')
    ax1.grid(True, axis='y', linestyle='--', alpha=0.5)

    # [2] Rebirths vs System Final Survival Rate
    ax2 = plt.subplot(3, 2, 2)
    sc_data = main_df.groupby(['leg_div', 'mem_depth']).agg({
        'total_rebirths': 'mean',
        'civ_survival_ratio': 'mean'
    }).reset_index()
    sc = ax2.scatter(sc_data['total_rebirths'], sc_data['civ_survival_ratio'] * 100,
                     s=sc_data['mem_depth'] * 100, c=sc_data['leg_div'], cmap='coolwarm', alpha=0.8, edgecolors='black')
    cbar = plt.colorbar(sc, ax=ax2)
    cbar.set_label('Legislative Diversity Multiplier')
    ax2.set_title("Self-Replication count vs Final Survival", fontsize=15)
    ax2.set_xlabel("Mean Rebirths (#)")
    ax2.set_ylabel("Civilization Survival Ratio (%)")
    ax2.grid(True, linestyle='--', alpha=0.5)

    # [3] Heatmap of Param Sensitivity
    ax3 = plt.subplot(3, 2, 3)
    p_df = main_df.pivot_table(index='leg_div', columns='mem_depth', values='system_survival_rate', aggfunc='mean')
    cax = ax3.matshow(p_df, cmap='YlGnBu')
    plt.colorbar(cax, ax=ax3, fraction=0.046, pad=0.04)
    ax3.set_xticks(range(len(p_df.columns)))
    ax3.set_xticklabels(p_df.columns)
    ax3.set_yticks(range(len(p_df.index)))
    ax3.set_yticklabels(p_df.index)
    ax3.set_xlabel("Soul Memory Depth (Events)")
    ax3.set_ylabel("Legislature Goal Diversity")
    ax3.set_title("Homeostasis Heatmap (System Survival %)", fontsize=15, pad=15)
    for (i, j), z in np.ndenumerate(p_df):
        ax3.text(j, i, f"{z*100:.1f}%", ha='center', va='center', fontweight='bold', color='white' if z > 0.5 else 'black')

    # [4] Evolution Activity vs Generational Depth
    ax4 = plt.subplot(3, 2, 4)
    evol_df = main_df.groupby('final_generation')['rule_evolution_count'].mean().reset_index()
    if not evol_df.empty:
        ax4.plot(evol_df['final_generation'], evol_df['rule_evolution_count'], marker='D', color='#575fcf', markersize=8, linewidth=2)
    ax4.set_title("Legislature Rule Evolution over Generations", fontsize=15)
    ax4.set_xlabel("Final Epoch Generation (#)")
    ax4.set_ylabel("Avg Rule Amendments")
    # [5] Threshold vs Survival Line Chart
    ax5 = plt.subplot(3, 2, 5)
    line_data = main_df.groupby(['mindless_thresh', 'leg_div'])['civ_survival_ratio'].mean().reset_index()
    for leg_div_val in sorted(line_data['leg_div'].unique()):
        subset = line_data[line_data['leg_div'] == leg_div_val]
        ax5.plot(subset['mindless_thresh'], subset['civ_survival_ratio'] * 100, 
                 marker='o', linewidth=2, label=f'Leg. Div: {leg_div_val}')
    
    ax5.set_title("Mindless Threshold vs System Survival", fontsize=15)
    ax5.set_xlabel("Mindless Trigger Entropy Threshold")
    ax5.set_ylabel("Mean Civ. Survival Ratio (%)")
    ax5.legend(loc='best')
    ax5.grid(True, linestyle='--', alpha=0.6)

    # [6] Mindless Activation Rate vs Survival Scatter Plot
    ax6 = plt.subplot(3, 2, 6)
    sc_data_2 = main_df.groupby(['mindless_thresh', 'silence_sens']).agg({
        'mindless_activation_rate': 'mean',
        'civ_survival_ratio': 'mean'
    }).reset_index()
    
    sc2 = ax6.scatter(sc_data_2['mindless_activation_rate'], sc_data_2['civ_survival_ratio'] * 100,
                      s=150, c=sc_data_2['silence_sens'], cmap='viridis', edgecolors='black', alpha=0.8)
    cbar2 = plt.colorbar(sc2, ax=ax6)
    cbar2.set_label('Silence Sensitivity')
    ax6.set_title("Mindless Activation % vs Survival Ratio", fontsize=15)
    ax6.set_xlabel("Mean Mindless Mode Activation Ratio")
    ax6.set_ylabel("Mean Civ. Survival Ratio (%)")
    ax6.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"\nVisualizations successfully saved to: {out_path}")


if __name__ == "__main__":
    run_experiment()
