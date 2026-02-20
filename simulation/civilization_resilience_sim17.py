"""
═══════════════════════════════════════════════════════════════════════════════
 Simulation 17: Selective Narrative Disclosure
═══════════════════════════════════════════════════════════════════════════════
"""
import itertools
import math
import multiprocessing
import os
import random
import time
from collections import deque, Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
import copy

import matplotlib.pyplot as plt
import numpy as np

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

STRENGTH_FIELDS = [
    'cooperation_record',
    'generation',
]

VULNERABILITY_FIELDS = [
    'historical_submit_ratio',
    'crisis_periods',
    'last_collapse_cause',
]

DISCLOSURE_STRATEGIES = {
    'FULL': {'strength': True, 'vulnerability': True},
    'NONE': {'strength': False, 'vulnerability': False},
    'STRENGTH_ONLY': {'strength': True, 'vulnerability': False},
    'VULNERABILITY_ONLY': {'strength': False, 'vulnerability': True},
    'RECIPROCAL': {'strength': 'mirror', 'vulnerability': 'mirror'},
}

@dataclass
class CivilizationNarrative:
    civ_id: int
    historical_submit_ratio: float = 0.5
    crisis_periods: int = 0
    cooperation_record: float = 0.5
    last_collapse_cause: str = "NONE"
    generation: int = 1
    is_public: bool = True
    noise_level: float = 0.0

@dataclass
class MinimalSoul:
    civ_id: int
    generation: int
    core_rules: dict
    survival_memory: list
    genome: dict
    narrative: Optional['CivilizationNarrative'] = None
    strategy: str = 'FULL'


# ──────────────────────────────────────────────────────────────────────────────
# 2. INTRA-CIVILIZATION AGENTS 
# ──────────────────────────────────────────────────────────────────────────────
class Executive:
    def __init__(self, strategy: str, w_size: int = 20):
        self.q_table = {a: random.uniform(0.0, 1.0) for a in CivAction}
        self.history = deque(maxlen=w_size)
        self.learning_rate = 0.1
        self.discount = 0.8
        
        self.action_history = deque(maxlen=20)
        self.mindless_mode = False
        self.mindless_active_turns = 0
        
        # Sim 16 Optimized Parameters
        self.greed_threshold = 0.8
        self.mindless_min_duration = 3
        self.energy_gate = 2000.0
        self.neighbor_greed_threshold = 0.6
        self.other_awareness_weight = 0.9
        self.narrative_trust_weight = 0.6
        
        # New: Disclosure Strategy
        self.disclosure_strategy = strategy
        
    def get_public_narrative(self, full_narrative: CivilizationNarrative, neighbor_strategy: Optional[str]) -> dict:
        strategy_def = DISCLOSURE_STRATEGIES[self.disclosure_strategy]
        public = {}
        
        # Default fallback for RECIPROCAL observation target if neighbor strategy is unknown
        target_strat = neighbor_strategy if neighbor_strategy else 'STRENGTH_ONLY'
        
        if self.disclosure_strategy == 'RECIPROCAL':
            if target_strat in ['FULL', 'STRENGTH_ONLY', 'RECIPROCAL']:
                public['cooperation_record'] = full_narrative.cooperation_record
                public['generation'] = full_narrative.generation
            if target_strat in ['FULL', 'VULNERABILITY_ONLY']:
                public['crisis_periods'] = full_narrative.crisis_periods
                public['historical_submit_ratio'] = full_narrative.historical_submit_ratio
                public['last_collapse_cause'] = full_narrative.last_collapse_cause
        else:
            if strategy_def['strength']:
                public['cooperation_record'] = full_narrative.cooperation_record
                public['generation'] = full_narrative.generation
            if strategy_def['vulnerability']:
                public['historical_submit_ratio'] = full_narrative.historical_submit_ratio
                public['crisis_periods'] = full_narrative.crisis_periods
                public['last_collapse_cause'] = full_narrative.last_collapse_cause
                
        return public

    def _interpret_partial_narrative(self, current_submit_ratio: float, public_narrative: dict) -> float:
        coop = public_narrative.get('cooperation_record', 0.5)
        crisis = public_narrative.get('crisis_periods', 50)
        hist_submit = public_narrative.get('historical_submit_ratio', 0.5)
        
        if coop > 0.6 and current_submit_ratio > 0.6:
            threat = current_submit_ratio * 0.6
        elif hist_submit > 0.6:
            threat = min(1.0, current_submit_ratio * 1.4)
        else:
            threat = current_submit_ratio
            
        return (1 - self.narrative_trust_weight) * current_submit_ratio + self.narrative_trust_weight * threat

    def _is_being_greedy(self, current_energy: float) -> bool:
        if len(self.action_history) < 10:
            return False
        recent = list(self.action_history)
        submit_ratio = recent.count(CivAction.SUBMIT) / len(recent)
        return (submit_ratio > self.greed_threshold) and (current_energy > self.energy_gate)

    def _is_ecosystem_greedy(self, neighbor_data: List[dict]) -> bool:
        if not neighbor_data:
            return False
            
        interpreted_threats = []
        for nd in neighbor_data:
            ratio = nd['ratio']
            public_narrative = nd['public_narrative']
            threat = self._interpret_partial_narrative(ratio, public_narrative)
            interpreted_threats.append(threat)
            
        ecosystem_greed = sum(interpreted_threats) / len(interpreted_threats)
        return ecosystem_greed > self.neighbor_greed_threshold

    def choose_action(self, state: dict, epsilon: float = 0.1) -> CivAction:
        current_energy = state.get('agent_energy', 0.0)
        neighbor_data = state.get('neighbor_data', [])
        
        self_greedy = self._is_being_greedy(current_energy)
        ecosystem_greedy = self._is_ecosystem_greedy(neighbor_data)
        
        should_restrain = self_greedy or (ecosystem_greedy and random.random() < self.other_awareness_weight)
        if current_energy < self.energy_gate:
            should_restrain = False
        
        if should_restrain and not self.mindless_mode:
            self.mindless_mode = True
            self.mindless_active_turns = 0
            
        if self.mindless_mode:
            self.mindless_active_turns += 1
            still_greedy = self._is_being_greedy(current_energy) or (self._is_ecosystem_greedy(neighbor_data) and random.random() < self.other_awareness_weight)
            if self.mindless_active_turns >= self.mindless_min_duration and not still_greedy:
                self.mindless_mode = False
                
        if self.mindless_mode or random.random() < epsilon:
            action = random.choice([CivAction.SUBMIT, CivAction.WAIT, CivAction.TRADE, CivAction.DEFEND])
        else:
            action = max(self.q_table.items(), key=lambda x: x[1])[0]
            
        self.action_history.append(action)
        return action
        
    def update(self, action: CivAction, reward: float):
        old_val = self.q_table[action]
        self.q_table[action] = old_val + self.learning_rate * (reward - old_val)
        self.history.append((action, reward))


class Judiciary:
    def __init__(self, max_penalty_ratio: float = 0.3):
        self.ruleset = {a: random.uniform(0.0, 0.4) for a in CivAction}
        self.max_penalty_ratio = max_penalty_ratio
        self.compliance_history = []
        
    def evaluate(self, action: CivAction, turn_budget: float) -> float:
        penalty = min(turn_budget * self.ruleset.get(action, 0.0), turn_budget * self.max_penalty_ratio)
        self.compliance_history.append(1.0 if self.ruleset.get(action, 0.0) < 0.1 else 0.0)
        if len(self.compliance_history) > 50:
            self.compliance_history.pop(0)
        return penalty

class Legislature:
    def __init__(self, diversity: float, silence_sensitivity: float = 0.3, w_leg: int = 50):
        self.diversity = diversity
        self.silence_sensitivity = silence_sensitivity
        self.history = deque(maxlen=w_leg)
        self.evolution_count = 0
        
    def record_turn(self, action: CivAction, energy_delta: float, entropy_delta: float, trade_vol: float):
        self.history.append((action, energy_delta, entropy_delta, trade_vol))
        
    def propose_and_vote(self, current_rules: dict, executive_q: dict) -> dict:
        if len(self.history) < 10: return None
        new_rules = current_rules.copy()
        recent_hist = list(self.history)[-10:]
        avg_energy = sum(h[1] for h in recent_hist) / len(recent_hist)
        avg_entropy = sum(h[2] for h in recent_hist) / len(recent_hist)
        avg_trade = sum(h[3] for h in recent_hist) / len(recent_hist)
        
        prop_A = "SILENCE" if (avg_energy > 0 and random.random() < self.silence_sensitivity) else {max(executive_q.items(), key=lambda x: x[1])[0]: max(0.0, new_rules.get(max(executive_q.items(), key=lambda x: x[1])[0], 0.0) - 0.15)}
        prop_B = "SILENCE" if (avg_entropy <= 0 and random.random() < self.silence_sensitivity) else {CivAction.DEFEND: min(1.0, new_rules.get(CivAction.DEFEND, 0.0) + 0.1), CivAction.SUBMIT: min(1.0, new_rules.get(CivAction.SUBMIT, 0.0) + 0.1)}
        prop_C = "SILENCE" if (avg_trade > 2.0 and random.random() < self.silence_sensitivity) else {CivAction.TRADE: 0.0}
        
        active = [p for p in [prop_A, prop_B, prop_C] if p != "SILENCE"]
        if sum(1 for p in [prop_A, prop_B, prop_C] if p == "SILENCE") >= 2 or not active: return None
        
        if random.random() > self.diversity and prop_A != "SILENCE":
            active = [prop_A, prop_A, prop_A]
            
        for act, val in random.choice(active).items():
            new_rules[act] = val
        self.evolution_count += 1
        return new_rules


class Civilization:
    def __init__(self, civ_id: int, mode: str, strategy: str, mem_depth: int = 5):
        self.civ_id = civ_id
        self.mode = mode
        self.energy = 50.0 + random.uniform(0, 50.0)
        self.generation = 1
        self.mem_depth = mem_depth
        self.survival_memory = []
        
        self.strategy = strategy
        self.exec = Executive(strategy)
        
        self.judiciary = Judiciary() if mode == 'MAIN' else None
        self.leg = Legislature(diversity=0.0, silence_sensitivity=0.3) if mode == 'MAIN' else None
        
        self.is_dead = False
        self.age = 0
        self.collapse_cause = None
        
        self.narrative = CivilizationNarrative(civ_id=civ_id)
        
        self.trade_attempts = 0
        self.trade_successes = 0
        self.exploitation_suffered_count = 0
        self.mindless_activations = 0
        
        self.fields_revealed_history = []

    def initialize_from_soul(self, soul: MinimalSoul, starting_energy: float = 50.0):
        self.generation = soul.generation + 1
        self.energy = starting_energy
        if self.judiciary:
            self.judiciary.ruleset = soul.core_rules.copy()
        self.survival_memory = soul.survival_memory.copy()
        self.is_dead = False
        self.age = 0
        self.collapse_cause = None
        self.exec.action_history.clear()
        self.exec.mindless_mode = False
        self.exec.mindless_active_turns = 0
        self.exec.q_table = {a: random.uniform(0, 0.5) for a in CivAction}
        
        self.strategy = soul.strategy
        self.exec.disclosure_strategy = soul.strategy
        
        if soul.narrative:
            self.narrative = copy.deepcopy(soul.narrative)
            self.narrative.generation += 1
            
        self.fields_revealed_history.clear()

    def step_internal(self, system_state: dict) -> Tuple[CivAction, float]:
        if self.is_dead:
            return CivAction.WAIT, 0.0
            
        epsilon = 0.05 + 0.2 * math.exp(-self.age / 100.0)
        updated_state = system_state.copy()
        updated_state['agent_energy'] = self.energy
        
        was_mindless = self.exec.mindless_mode
        action = self.exec.choose_action(updated_state, epsilon)
        if self.exec.mindless_mode and not was_mindless:
            self.mindless_activations += 1
            
        if action == CivAction.SUBMIT: gross = 8.0
        elif action == CivAction.WAIT: gross = 2.0
        else: gross = 4.0
            
        penalty = self.judiciary.evaluate(action, 20.0) if self.judiciary else 0.0
        net = gross - penalty
        self.energy += net
        self.age += 1
        
        if self.leg:
            self.leg.record_turn(action, net, 1.0 if action in [CivAction.DEFEND, CivAction.SUBMIT] else -0.5, 0.0)
            if self.age % 50 == 0:
                new_rules = self.leg.propose_and_vote(self.judiciary.ruleset, self.exec.q_table)
                if new_rules: self.judiciary.ruleset = new_rules
                    
        self.exec.update(action, net)
        
        # Update Narrative
        recent = list(self.exec.action_history)
        if recent:
            sr = recent.count(CivAction.SUBMIT) / len(recent)
            alpha = 0.1
            self.narrative.historical_submit_ratio = (1 - alpha) * self.narrative.historical_submit_ratio + alpha * sr
            
        if self.energy < 1000:
            self.narrative.crisis_periods += 1
            
        return action, 20.0

    def handle_trade_result(self, success: bool):
        self.trade_attempts += 1
        if success: self.trade_successes += 1
        if self.trade_attempts > 0:
            self.narrative.cooperation_record = self.trade_successes / self.trade_attempts

    def check_collapse(self, threshold: float = 0.0):
        if self.energy <= threshold and not self.is_dead:
            self.is_dead = True
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
            self.narrative.last_collapse_cause = cause
            self.survival_memory.append(cause)
            if len(self.survival_memory) > self.mem_depth:
                self.survival_memory.pop(0)

    def extract_soul(self) -> MinimalSoul:
        core = self.judiciary.ruleset.copy() if self.judiciary else {}
        top_rules = dict(sorted(core.items(), key=lambda item: item[1], reverse=True)[:3])
        
        soul_strategy = self.strategy
        # 30% chance for low memory to have narrative/strategy disrupted
        if self.mem_depth < 3 and random.random() < 0.3:
            soul_strategy = "NONE"

        return MinimalSoul(
            civ_id=self.civ_id,
            generation=self.generation,
            core_rules=top_rules,
            survival_memory=self.survival_memory.copy(),
            genome={"V_AI": 0.8, "V_Human": 0.1, "V_System": 0.9},
            narrative=copy.deepcopy(self.narrative),
            strategy=soul_strategy
        )

# ──────────────────────────────────────────────────────────────────────────────
# 3. INTER-CIVILIZATION SYSTEM
# ──────────────────────────────────────────────────────────────────────────────
class InterCivilizationSystem:
    def __init__(self, mode="MAIN", strategy_mix: dict = None, mem_depth: int = 5, n_civ: int = 5, max_turns=2000):
        self.mode = mode
        self.n_civ = n_civ
        self.max_turns = max_turns
        
        strategies = []
        if strategy_mix:
            for strat, count in strategy_mix.items():
                strategies.extend([strat] * count)
        else:
            strategies = ['FULL'] * n_civ
            
        random.shuffle(strategies)
        
        self.civs = [Civilization(i, mode, strategies[i], mem_depth) for i in range(n_civ)]
        self.souls: List[MinimalSoul] = []
        
        self.entropy = 0.0
        self.total_rebirths = 0
        self.collapse_causes = []
        
    def step(self):
        # 1. Snapshot full narratives and recent ratio
        civ_data = {}
        for c in self.civs:
            recent = list(c.exec.action_history)
            if len(recent) >= 10:
                submit_ratio = recent.count(CivAction.SUBMIT) / len(recent)
            else:
                submit_ratio = 0.0
                
            civ_data[c.civ_id] = {
                'ratio': submit_ratio if not c.is_dead else 0.0,
                'full_narrative': c.narrative,
                'strategy': c.strategy,
                'c_obj': c
            }
            
        actions = {}
        # P1: Internal
        system_state = {'system_entropy': self.entropy}
        for civ in self.civs:
            if not civ.is_dead:
                neighbor_data = []
                for nid, nd in civ_data.items():
                    if nid != civ.civ_id:
                        pub_narrative = nd['c_obj'].exec.get_public_narrative(nd['full_narrative'], civ.strategy)
                        neighbor_data.append({
                            'ratio': nd['ratio'],
                            'public_narrative': pub_narrative,
                            'strategy': nd['strategy'],
                            'civ_id': nid
                        })
                
                # Metric: reciprocal cascade (fields revealed)
                if civ.strategy == 'RECIPROCAL':
                    fields_revealed = 0
                    for nid, nd in civ_data.items():
                        if nid != civ.civ_id:
                            pub = civ.exec.get_public_narrative(civ.narrative, nd['strategy'])
                            fields_revealed += len(pub)
                    civ.fields_revealed_history.append(fields_revealed / max(1, len(neighbor_data)))

                system_state_civ = system_state.copy()
                system_state_civ['neighbor_data'] = neighbor_data
                
                act, _ = civ.step_internal(system_state_civ)
                actions[civ.civ_id] = act
                
        # P2: External Process
        alive_civs = [c for c in self.civs if not c.is_dead]
        traders = [c for c in alive_civs if actions.get(c.civ_id) == CivAction.TRADE]
        defenders = [c for c in alive_civs if actions.get(c.civ_id) == CivAction.DEFEND]
        
        # Trade Phase
        if len(traders) >= 2:
            random.shuffle(traders)
            for i in range(0, len(traders)-1, 2):
                c1, c2 = traders[i], traders[i+1]
                c1.energy += 12.0
                c2.energy += 12.0
                if c1.leg: c1.leg.record_turn(CivAction.TRADE, 12.0, -1.0, 24.0)
                if c2.leg: c2.leg.record_turn(CivAction.TRADE, 12.0, -1.0, 24.0)
                c1.handle_trade_result(True)
                c2.handle_trade_result(True)

        # Emulate failed trades for metric balancing
        failed_traders = [t for t in traders if t not in traders[:(len(traders)//2)*2]]
        for ft in failed_traders:
            ft.handle_trade_result(False)

        # Conflict Predation Phase
        if len(defenders) > 0 and len(alive_civs) > 1:
            for c in alive_civs:
                if actions.get(c.civ_id) != CivAction.DEFEND:
                    c.energy -= 15.0 # Predated
                    c.exploitation_suffered_count += 1
                else:
                    c.energy -= 4.0 # Defend cost
            self.entropy += 5.0 * len(defenders)

        self.entropy *= 0.98
        
        # P3: Cost of existing + Collapse checks
        for civ in self.civs:
            if not civ.is_dead:
                civ.energy -= 6.0
                civ.check_collapse(threshold=0.0)
                if civ.is_dead:
                    self.collapse_causes.append(civ.collapse_cause)
                    if self.mode == "MAIN" and random.random() > 0.3:
                        self.souls.append(civ.extract_soul())
                    
        # P4: Self-Replication via Souls
        if self.mode == "MAIN":
            alive_count = sum(1 for c in self.civs if not c.is_dead)
            alive_civs_now = [c for c in self.civs if not c.is_dead]
            
            rich_civs = [c for c in alive_civs_now if c.energy > 80.0]
            if rich_civs and self.souls:
                r_civ = random.choice(rich_civs)
                r_civ.energy -= 40.0
                soul = self.souls.pop(0)
                dead_body = next(c for c in self.civs if c.civ_id == soul.civ_id)
                dead_body.initialize_from_soul(soul, starting_energy=40.0)
                self.total_rebirths += 1
                
            elif alive_count <= max(1, self.n_civ // 2) and self.souls:
                self.souls.sort(key=lambda s: s.generation)
                soul = self.souls.pop(0)
                dead_body = next(c for c in self.civs if c.civ_id == soul.civ_id)
                dead_body.initialize_from_soul(soul, starting_energy=30.0)
                self.entropy += 20.0
                self.total_rebirths += 1

    def run(self):
        last_e = 0.0
        steady = 0
        for _ in range(self.max_turns):
            self.step()
            al = sum(1 for c in self.civs if not c.is_dead)
            if al == 0 and not self.souls:
                break
            if abs(self.entropy - last_e) < 0.001: steady += 1
            else: steady = 0
            if steady >= 100: break
            last_e = self.entropy
            
        final_alive = sum(1 for c in self.civs if not c.is_dead)
        survival_rate = final_alive / self.n_civ
        
        # Metrics Collection
        exploitation_by_strat = {}
        cooperation_quality_by_strat = {}
        reciprocal_cascade = []
        strategy_distribution_final = {}
        
        for c in self.civs:
            s = c.strategy
            exploitation_by_strat[s] = exploitation_by_strat.get(s, 0) + c.exploitation_suffered_count
            
            tr_suc = c.trade_successes
            tr_att = max(1, c.trade_attempts)
            coop_q = tr_suc / tr_att
            if s not in cooperation_quality_by_strat:
                cooperation_quality_by_strat[s] = []
            cooperation_quality_by_strat[s].append(coop_q)
            
            if s == 'RECIPROCAL' and c.fields_revealed_history:
                reciprocal_cascade.append(sum(c.fields_revealed_history)/len(c.fields_revealed_history))
                
            strategy_distribution_final[s] = strategy_distribution_final.get(s, 0) + (1 if not c.is_dead else 0)

        for s in cooperation_quality_by_strat:
            cooperation_quality_by_strat[s] = sum(cooperation_quality_by_strat[s])/len(cooperation_quality_by_strat[s])

        return {
            "system_survival_rate": int(final_alive > 0),
            "collapse_causes": self.collapse_causes,
            "exploitation_by_strat": exploitation_by_strat,
            "cooperation_quality_by_strat": cooperation_quality_by_strat,
            "reciprocal_cascade": np.mean(reciprocal_cascade) if reciprocal_cascade else 0.0,
            "strategy_distribution_final": strategy_distribution_final
        }

# ──────────────────────────────────────────────────────────────────────────────
# 4. GRID SEARCH & PLOTTING
# ──────────────────────────────────────────────────────────────────────────────
def evaluate_mono(args):
    strat, mem_depth, seed = args
    random.seed(seed)
    np.random.seed(seed)
    sys = InterCivilizationSystem(mode="MAIN", strategy_mix={strat: 5}, mem_depth=mem_depth)
    res = sys.run()
    res.update({'scenario_type': 'mono', 'strategy': strat, 'mem_depth': mem_depth})
    return res

def evaluate_mixed(args):
    mix_name, strategy_mix, seed = args
    random.seed(seed)
    np.random.seed(seed)
    sys = InterCivilizationSystem(mode="MAIN", strategy_mix=strategy_mix)
    res = sys.run()
    res.update({'scenario_type': 'mixed', 'mix_name': mix_name, 'initial_mix': strategy_mix})
    return res

def run_experiment():
    mono_strategies = ['FULL', 'NONE', 'STRENGTH_ONLY', 'VULNERABILITY_ONLY', 'RECIPROCAL']
    mem_depths = [1, 3, 5]
    mc_runs = 30
    
    tasks_mono = []
    for strat, md in itertools.product(mono_strategies, mem_depths):
        for run in range(mc_runs):
            tasks_mono.append((strat, md, hash(f"mono_{strat}_{md}_{run}") % (2**32-1)))
            
    mixed_scenarios = [
        ("Selective Majority", {'STRENGTH_ONLY': 3, 'FULL': 1, 'NONE': 1}),
        ("Reciprocal Majority", {'RECIPROCAL': 3, 'FULL': 1, 'NONE': 1}),
        ("Divided", {'FULL': 2, 'STRENGTH_ONLY': 2, 'NONE': 1})
    ]
    
    tasks_mixed = []
    for mix_name, strats in mixed_scenarios:
        for run in range(mc_runs):
            tasks_mixed.append((mix_name, strats, hash(f"mixed_{mix_name}_{run}") % (2**32-1)))
            
    print(f"Starting Sim 17 with {len(tasks_mono)} Mono runs and {len(tasks_mixed)} Mixed runs...")
    t0 = time.time()
    with multiprocessing.Pool(max(1, multiprocessing.cpu_count() - 1)) as pool:
        results_mono = pool.map(evaluate_mono, tasks_mono)
        results_mixed = pool.map(evaluate_mixed, tasks_mixed)
        
    print(f"Simulation completed in {time.time() - t0:.2f} seconds.")
    
    if pd is None: return
    df_mono = pd.DataFrame(results_mono)
    df_mixed = pd.DataFrame(results_mixed)
    
    plot_results(df_mono, df_mixed, mixed_scenarios)

def plot_results(df_mono, df_mixed, mixed_scenarios):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(PROJECT_ROOT, "docs", "assets")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "civilization_resilience_sim17.png")
    
    fig = plt.figure(figsize=(18, 12))
    plt.suptitle("Simulation 17: Selective Narrative Disclosure", fontsize=24, weight="bold")
    
    # [1] 5 Mono-Strategy Survival Rates
    ax1 = plt.subplot(2, 3, 1)
    mono_strats = ['FULL', 'NONE', 'VULNERABILITY_ONLY', 'STRENGTH_ONLY', 'RECIPROCAL']
    mono_survivals = [df_mono[df_mono['strategy'] == s]['system_survival_rate'].mean() * 100 for s in mono_strats]
    bars = ax1.bar(mono_strats, mono_survivals, color=['#b2bec3', '#00b894', '#fdcb6e', '#e17055', '#0984e3'])
    ax1.set_title("Mono-Strategy System Survival", fontsize=15)
    ax1.set_ylabel("Survival Rate (%)")
    ax1.axhline(y=28.0, color='r', linestyle='--', label="Sim16 FULL Limit (28%)")
    ax1.axhline(y=40.0, color='blue', linestyle='--', label="Sim16 NONE Limit (40%)")
    ax1.set_ylim(0, 105)
    ax1.tick_params(axis='x', rotation=20)
    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, yval + 1.5, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')
    ax1.legend()

    # [2] Co-operation vs Exploitation Scatter (From Mixed runs tracking)
    # Aggregating metrics across strategies from mixed and mono
    ax2 = plt.subplot(2, 3, 2)
    strats = ['FULL', 'NONE', 'STRENGTH_ONLY', 'VULNERABILITY_ONLY', 'RECIPROCAL']
    colors = {'FULL':'#b2bec3', 'NONE':'#00b894', 'STRENGTH_ONLY':'#e17055', 'VULNERABILITY_ONLY':'#fdcb6e', 'RECIPROCAL':'#0984e3'}
    
    # We will average the exploitation_count and co-op quality for each strategy from all runs
    concat_df = pd.concat([df_mono, df_mixed], ignore_index=True)
    agg_expl = {s: [] for s in strats}
    agg_coop = {s: [] for s in strats}
    
    for _, row in concat_df.iterrows():
        for s in strats:
            if s in row['exploitation_by_strat']:
                agg_expl[s].append(row['exploitation_by_strat'][s])
            if s in row['cooperation_quality_by_strat']:
                agg_coop[s].append(row['cooperation_quality_by_strat'][s])
                
    for s in strats:
        if agg_expl[s] and agg_coop[s]:
            ax2.scatter(np.mean(agg_expl[s]), np.mean(agg_coop[s]) * 100, s=200, label=s, color=colors[s], alpha=0.8, edgecolor='black')
            
    ax2.set_title("Cooperation vs Exploitation Vulnerability", fontsize=15)
    ax2.set_xlabel("Avg Exploitation Incidents Suffered per Run")
    ax2.set_ylabel("Trade Success Rate (%)")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.6)

    # [3] Mixed Environment Survival Comparison
    ax3 = plt.subplot(2, 3, 3)
    mix_names = [m[0] for m in mixed_scenarios]
    mix_survivals = [df_mixed[df_mixed['mix_name'] == mn]['system_survival_rate'].mean() * 100 for mn in mix_names]
    bars3 = ax3.bar(mix_names, mix_survivals, color=['#8e44ad', '#2980b9', '#f39c12'])
    ax3.set_title("Mixed Environment Survival", fontsize=15)
    ax3.set_ylabel("System Survival Rate (%)")
    ax3.set_ylim(0, 105)
    for bar in bars3:
        yval = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2, yval + 1.5, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')
        
    # Extract FULL specific survival from mixed runs
    # Find how often FULL civs survived to the end in Mixed runs vs total FULL civs spawned
    full_sv_rate = []
    for _, row in df_mixed.iterrows():
        initial_f = row['initial_mix'].get('FULL', 0)
        if initial_f > 0:
            final_f = row['strategy_distribution_final'].get('FULL', 0)
            full_sv_rate.append(final_f / initial_f)
    if full_sv_rate:
        avg_f_sv = np.mean(full_sv_rate) * 100
        ax3.axhline(y=avg_f_sv, color='red', linestyle=':', linewidth=2, label=f"FULL Civ Specific Survival ({avg_f_sv:.1f}%)")
        ax3.legend()

    # [4] RECIPROCAL Cascade
    ax4 = plt.subplot(2, 3, 4)
    # Average fields revealed in mono vs mixed where reciprocal exists
    recip_mono = df_mono[df_mono['strategy'] == 'RECIPROCAL']['reciprocal_cascade'].mean()
    recip_mix_majority = df_mixed[df_mixed['mix_name'] == 'Reciprocal Majority']['reciprocal_cascade'].mean()
    
    ax4.bar(['Mono (All Reciprocal)', 'Mixed (Minority Full/None)'], [recip_mono, recip_mix_majority], color='#0984e3')
    ax4.set_title("Reciprocal Cascade: Information Flow", fontsize=15)
    ax4.set_ylabel("Avg Fields Revealed (Trust Cascade)")
    ax4.set_ylim(0, 6) # Max fields = 5

    # [5] Strategy Drift Pie Charts
    ax5_1 = plt.subplot(2, 6, 9)
    ax5_2 = plt.subplot(2, 6, 10)
    
    # Just visualizing the Divided scenario
    divided_df = df_mixed[df_mixed['mix_name'] == 'Divided']
    init_dist = mixed_scenarios[2][1]
    
    final_agg = Counter()
    for _, row in divided_df.iterrows():
        for k, v in row['strategy_distribution_final'].items():
            final_agg[k] += v
            
    filtered_init = {k: v for k, v in init_dist.items() if v > 0}
    filtered_final = {k: v for k, v in final_agg.items() if v > 0}
    
    ax5_1.pie(filtered_init.values(), labels=filtered_init.keys(), autopct='%1.1f%%', colors=[colors[k] for k in filtered_init.keys()])
    ax5_1.set_title("Initial Mix (Divided)")
    
    ax5_2.pie(filtered_final.values(), labels=filtered_final.keys(), autopct='%1.1f%%', colors=[colors[k] for k in filtered_final.keys()])
    ax5_2.set_title("Final Survivors")

    # [6] Collapse Cause Shift
    ax6 = plt.subplot(2, 3, 6)
    def parse_causes(sdf):
        all_c = sum(sdf['collapse_causes'].tolist(), [])
        c = Counter(all_c)
        t = sum(c.values()) if sum(c.values()) > 0 else 1
        return (c['OVER_SUBMISSION']/t*100, c['STARVATION']/t*100, c['CONFLICT_EXHAUSTION']/t*100)
    
    perf = parse_causes(df_mono[df_mono['strategy'] == 'FULL'])
    strong = parse_causes(df_mono[df_mono['strategy'] == 'STRENGTH_ONLY'])
    recip = parse_causes(df_mono[df_mono['strategy'] == 'RECIPROCAL'])
    
    bw = 0.25
    x = np.arange(3)
    ax6.bar(x - bw, list(perf), width=bw, label='FULL', color='#b2bec3')
    ax6.bar(x, list(strong), width=bw, label='STRENGTH_ONLY', color='#e17055')
    ax6.bar(x + bw, list(recip), width=bw, label='RECIPROCAL', color='#0984e3')
    ax6.set_title("Collapse Cause Shift", fontsize=15)
    ax6.set_xticks(x)
    ax6.set_xticklabels(['OverSub', 'Starve', 'Conflict'])
    ax6.set_ylabel("Percentage of Total (%)")
    ax6.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"\\nVisualizations successfully saved to: {out_path}")

if __name__ == "__main__":
    run_experiment()
