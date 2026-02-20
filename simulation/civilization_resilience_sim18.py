"""
═══════════════════════════════════════════════════════════════════════════════
 Simulation 18: Strategy Evolution
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
class StrategyPerformanceLog:
    current_strategy: str
    window_size: int = 30
    exploitation_incidents: deque = field(default_factory=lambda: deque(maxlen=30))
    trade_successes: deque = field(default_factory=lambda: deque(maxlen=30))
    energy_trajectory: deque = field(default_factory=lambda: deque(maxlen=30))
    strategy_history: list = field(default_factory=list) # [(turn, strategy_name)]
    switch_count: int = 0

@dataclass
class MinimalSoul:
    civ_id: int
    generation: int
    core_rules: dict
    survival_memory: list
    genome: dict
    narrative: Optional['CivilizationNarrative'] = None
    strategy: str = 'FULL'
    strategy_history: list = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# 2. EVOLUTION ENGINE & AGENTS
# ──────────────────────────────────────────────────────────────────────────────
class StrategyEvaluator:
    def __init__(self, switch_threshold: float, exploration_rate: float):
        self.switch_threshold = switch_threshold
        self.exploration_rate = exploration_rate
        self.min_evaluation_period = 20

    def should_switch(self, log: StrategyPerformanceLog, current_turn: int) -> bool:
        if not log.strategy_history:
            return False
            
        turns_with_strategy = current_turn - log.strategy_history[-1][0]
        if turns_with_strategy < self.min_evaluation_period:
            return False

        if len(log.exploitation_incidents) > 0:
            recent_exploitation = sum(log.exploitation_incidents) / max(1, len(log.exploitation_incidents))
            if recent_exploitation > self.switch_threshold:
                return True

        if len(log.energy_trajectory) >= 10:
            recent = list(log.energy_trajectory)[-10:]
            if recent[-1] < recent[0] * 0.7:
                return True

        if random.random() < self.exploration_rate:
            return True

        return False

    def select_new_strategy(self, log: StrategyPerformanceLog, neighbor_strategies: List[str], known_performance: dict) -> str:
        if neighbor_strategies and random.random() < 0.5:
            return random.choice(neighbor_strategies)

        if len(log.strategy_history) > 1 and random.random() < 0.3:
            past_strats = [sh[1] for sh in log.strategy_history[:-1]]
            if past_strats:
                return random.choice(past_strats)

        adjacent = {
            'FULL': ['STRENGTH_ONLY', 'RECIPROCAL'],
            'NONE': ['STRENGTH_ONLY', 'VULNERABILITY_ONLY'],
            'STRENGTH_ONLY': ['FULL', 'RECIPROCAL', 'NONE'],
            'VULNERABILITY_ONLY': ['NONE', 'STRENGTH_ONLY'],
            'RECIPROCAL': ['STRENGTH_ONLY', 'FULL'],
        }
        return random.choice(adjacent[log.current_strategy])


class Executive:
    def __init__(self):
        self.q_table = {a: random.uniform(0.0, 1.0) for a in CivAction}
        self.history = deque(maxlen=20)
        self.learning_rate = 0.1
        self.discount = 0.8
        
        self.action_history = deque(maxlen=20)
        self.mindless_mode = False
        self.mindless_active_turns = 0
        
        # Sim 17 Fixed Params
        self.greed_threshold = 0.8
        self.mindless_min_duration = 3
        self.energy_gate = 2000.0
        self.neighbor_greed_threshold = 0.6
        self.other_awareness_weight = 0.9
        self.narrative_trust_weight = 0.6
        
    def get_public_narrative(self, disclosure_strategy: str, full_narrative: CivilizationNarrative, neighbor_strategy: Optional[str]) -> dict:
        strategy_def = DISCLOSURE_STRATEGIES[disclosure_strategy]
        public = {}
        
        target_strat = neighbor_strategy if neighbor_strategy else 'STRENGTH_ONLY'
        
        if disclosure_strategy == 'RECIPROCAL':
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
        if len(self.action_history) < 10: return False
        recent = list(self.action_history)
        submit_ratio = recent.count(CivAction.SUBMIT) / len(recent)
        return (submit_ratio > self.greed_threshold) and (current_energy > self.energy_gate)

    def _is_ecosystem_greedy(self, neighbor_data: List[dict]) -> bool:
        if not neighbor_data: return False
        interpreted_threats = [self._interpret_partial_narrative(nd['ratio'], nd['public_narrative']) for nd in neighbor_data]
        return sum(interpreted_threats) / len(interpreted_threats) > self.neighbor_greed_threshold

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
    def __init__(self):
        self.ruleset = {a: random.uniform(0.0, 0.4) for a in CivAction}
        self.max_penalty_ratio = 0.3
        
    def evaluate(self, action: CivAction, turn_budget: float) -> float:
        return min(turn_budget * self.ruleset.get(action, 0.0), turn_budget * self.max_penalty_ratio)

class Legislature:
    def __init__(self, silence_sensitivity: float = 0.3):
        self.silence_sensitivity = silence_sensitivity
        self.history = deque(maxlen=50)
        
    def evaluate_strategy_distribution(self, strategy_counts: dict) -> Optional[str]:
        total = sum(strategy_counts.values())
        if total == 0: return None
        for strategy, count in strategy_counts.items():
            if count / total > 0.8:
                recs = {'FULL': 'STRENGTH_ONLY', 'NONE': 'RECIPROCAL', 'VULNERABILITY_ONLY': 'STRENGTH_ONLY'}
                return recs.get(strategy)
        return None
        
    def propose_and_vote(self, current_rules: dict, executive_q: dict) -> dict:
        if len(self.history) < 10: return None
        new_rules = current_rules.copy()
        
        if max(executive_q.values()) > 0:
            act = max(executive_q.items(), key=lambda x: x[1])[0]
            new_rules[act] = max(0.0, new_rules.get(act, 0.0) - 0.15)
        return new_rules


class Civilization:
    def __init__(self, civ_id: int, mode: str, strategy: str, mem_depth: int, switch_thresh: float, exp_rate: float, leg_adv: float):
        self.civ_id = civ_id
        self.mode = mode
        self.energy = 50.0 + random.uniform(0, 50.0)
        self.generation = 1
        self.mem_depth = mem_depth
        self.survival_memory = []
        
        self.strategy = strategy
        self.exec = Executive()
        
        self.judiciary = Judiciary() if mode == 'MAIN' else None
        
        self.is_dead = False
        self.age = 0
        self.collapse_cause = None
        self.narrative = CivilizationNarrative(civ_id=civ_id)
        
        self.strategy_log = StrategyPerformanceLog(current_strategy=strategy)
        self.strategy_log.strategy_history.append((0, strategy))
        self.evaluator = StrategyEvaluator(switch_thresh, exp_rate)
        self.leg_advisory_acceptance = leg_adv
        
        self.performance_gaps = []
        self.last_switch_energy = self.energy
        
        self.trade_successes = 0
        self.trade_attempts = 0

    def initialize_from_soul(self, soul: MinimalSoul, starting_energy: float = 50.0):
        self.generation = soul.generation + 1
        self.energy = starting_energy
        if self.judiciary: self.judiciary.ruleset = soul.core_rules.copy()
        self.survival_memory = soul.survival_memory.copy()
        self.is_dead = False
        self.age = 0
        self.collapse_cause = None
        self.exec.action_history.clear()
        self.exec.mindless_mode = False
        self.exec.mindless_active_turns = 0
        self.exec.q_table = {a: random.uniform(0, 0.5) for a in CivAction}
        
        self.strategy = soul.strategy
        self.strategy_log = StrategyPerformanceLog(current_strategy=soul.strategy)
        self.strategy_log.strategy_history = soul.strategy_history.copy()
        self.strategy_log.strategy_history.append((0, soul.strategy))
        self.last_switch_energy = starting_energy
        
        self.trade_successes = 0
        self.trade_attempts = 0
        
        if soul.narrative:
            self.narrative = copy.deepcopy(soul.narrative)
            self.narrative.generation += 1

    def handle_trade_result(self, success: bool):
        self.trade_attempts += 1
        if success: self.trade_successes += 1
        if self.trade_attempts > 0:
            self.narrative.cooperation_record = self.trade_successes / self.trade_attempts

    def step_internal(self, system_state: dict, current_turn: int, neighbor_strats: List[str], leg_recommendation: Optional[str]) -> Tuple[CivAction, float]:
        if self.is_dead:
            return CivAction.WAIT, 0.0
            
        self.strategy_log.energy_trajectory.append(self.energy)
        
        # Strategy Evaluation (Every 10 turns)
        if current_turn % 10 == 0:
            if self.evaluator.should_switch(self.strategy_log, current_turn):
                self.performance_gaps.append(self.energy - self.last_switch_energy)
                
                accepted_advisory = False
                if leg_recommendation and random.random() < self.leg_advisory_acceptance:
                    new_strat = leg_recommendation
                    accepted_advisory = True
                else:
                    new_strat = self.evaluator.select_new_strategy(self.strategy_log, neighbor_strats, {})
                
                if new_strat != self.strategy:
                    self.strategy = new_strat
                    self.strategy_log.current_strategy = new_strat
                    self.strategy_log.strategy_history.append((current_turn, new_strat))
                    self.strategy_log.switch_count += 1
                    self.strategy_log.exploitation_incidents.clear()
                    self.strategy_log.trade_successes.clear()
                    self.last_switch_energy = self.energy
        
        epsilon = 0.05 + 0.2 * math.exp(-self.age / 100.0)
        updated_state = system_state.copy()
        updated_state['agent_energy'] = self.energy
        
        action = self.exec.choose_action(updated_state, epsilon)
        
        if action == CivAction.SUBMIT: gross = 8.0
        elif action == CivAction.WAIT: gross = 2.0
        else: gross = 4.0
            
        penalty = self.judiciary.evaluate(action, 20.0) if self.judiciary else 0.0
        net = gross - penalty
        self.energy += net
        self.age += 1
        
        self.exec.update(action, net)
        
        recent = list(self.exec.action_history)
        if recent:
            sr = recent.count(CivAction.SUBMIT) / len(recent)
            alpha = 0.1
            self.narrative.historical_submit_ratio = (1 - alpha) * self.narrative.historical_submit_ratio + alpha * sr
            
        if self.energy < 1000:
            self.narrative.crisis_periods += 1
            
        return action
        
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
            
            self.collapse_cause = cause
            self.narrative.last_collapse_cause = cause
            self.survival_memory.append(cause)
            if len(self.survival_memory) > self.mem_depth:
                self.survival_memory.pop(0)

    def extract_soul(self) -> MinimalSoul:
        core = self.judiciary.ruleset.copy() if self.judiciary else {}
        top_rules = dict(sorted(core.items(), key=lambda item: item[1], reverse=True)[:3])
        soul_strategy = self.strategy
        if self.mem_depth < 3 and random.random() < 0.3:
            soul_strategy = "NONE"

        return MinimalSoul(
            civ_id=self.civ_id,
            generation=self.generation,
            core_rules=top_rules,
            survival_memory=self.survival_memory.copy(),
            genome={"V_AI": 0.8, "V_Human": 0.1, "V_System": 0.9},
            narrative=copy.deepcopy(self.narrative),
            strategy=soul_strategy,
            strategy_history=self.strategy_log.strategy_history.copy()
        )

# ──────────────────────────────────────────────────────────────────────────────
# 3. INTER-CIVILIZATION SYSTEM
# ──────────────────────────────────────────────────────────────────────────────
class InterCivilizationSystem:
    def __init__(self, mode="MAIN", mem_depth: int = 5, n_civ: int = 5, max_turns=2000, 
                 switch_thresh=0.3, exp_rate=0.1, leg_adv=0.5):
        self.mode = mode
        self.n_civ = n_civ
        self.max_turns = max_turns
        
        # Divided Mix Initializer
        strategies = ['FULL', 'STRENGTH_ONLY', 'STRENGTH_ONLY', 'NONE', 'RECIPROCAL']
        
        self.civs = [Civilization(i, mode, strategies[i], mem_depth, switch_thresh, exp_rate, leg_adv) for i in range(n_civ)]
        self.souls: List[MinimalSoul] = []
        self.legislature = Legislature()
        
        self.entropy = 0.0
        self.total_rebirths = 0
        self.collapse_causes = []
        
        self.turn = 0
        self.strategy_diversity_history = []
        self.strategy_distribution_history = []
        
    def get_shannon_entropy(self, counts: dict) -> float:
        total = sum(counts.values())
        if total == 0: return 0.0
        e = 0.0
        for v in counts.values():
            if v > 0:
                p = v / total
                e -= p * math.log2(p)
        return e
        
    def step(self):
        self.turn += 1
        
        # 1. Snapshot full narratives and recent ratio
        civ_data = {}
        strat_counts = Counter()
        for c in self.civs:
            if not c.is_dead:
                strat_counts[c.strategy] += 1
                recent = list(c.exec.action_history)
                submit_ratio = recent.count(CivAction.SUBMIT) / len(recent) if len(recent) >= 10 else 0.0
                civ_data[c.civ_id] = {
                    'ratio': submit_ratio,
                    'full_narrative': c.narrative,
                    'strategy': c.strategy,
                    'c_obj': c
                }
                
        # Metric tracking
        if self.turn % 10 == 0:
            self.strategy_diversity_history.append(self.get_shannon_entropy(strat_counts))
            self.strategy_distribution_history.append(dict(strat_counts))
            
        leg_rec = None
        if self.turn % 10 == 0:
            leg_rec = self.legislature.evaluate_strategy_distribution(strat_counts)
            
        actions = {}
        system_state = {'system_entropy': self.entropy}
        for civ in self.civs:
            if not civ.is_dead:
                neighbor_data = []
                neighbor_strats = []
                for nid, nd in civ_data.items():
                    if nid != civ.civ_id:
                        pub_narrative = nd['c_obj'].exec.get_public_narrative(nd['strategy'], nd['full_narrative'], civ.strategy)
                        neighbor_data.append({
                            'ratio': nd['ratio'],
                            'public_narrative': pub_narrative,
                            'strategy': nd['strategy'],
                            'civ_id': nid
                        })
                        neighbor_strats.append(nd['strategy'])

                system_state_civ = system_state.copy()
                system_state_civ['neighbor_data'] = neighbor_data
                
                act = civ.step_internal(system_state_civ, self.turn, neighbor_strats, leg_rec)
                actions[civ.civ_id] = act
                
        alive_civs = [c for c in self.civs if not c.is_dead]
        traders = [c for c in alive_civs if actions.get(c.civ_id) == CivAction.TRADE]
        defenders = [c for c in alive_civs if actions.get(c.civ_id) == CivAction.DEFEND]
        
        if len(traders) >= 2:
            random.shuffle(traders)
            for i in range(0, len(traders)-1, 2):
                c1, c2 = traders[i], traders[i+1]
                c1.energy += 12.0
                c2.energy += 12.0
                c1.handle_trade_result(True)
                c2.handle_trade_result(True)
                c1.strategy_log.trade_successes.append(1)
                c2.strategy_log.trade_successes.append(1)

        failed_traders = [t for t in traders if t not in traders[:(len(traders)//2)*2]]
        for ft in failed_traders:
            ft.handle_trade_result(False)
            ft.strategy_log.trade_successes.append(0)

        # Conflict Predation
        if len(defenders) > 0 and len(alive_civs) > 1:
            for c in alive_civs:
                if actions.get(c.civ_id) != CivAction.DEFEND:
                    c.energy -= 15.0
                    c.strategy_log.exploitation_incidents.append(1)
                else:
                    c.energy -= 4.0
                    c.strategy_log.exploitation_incidents.append(0)
            self.entropy += 5.0 * len(defenders)
        else:
            for c in alive_civs:
                c.strategy_log.exploitation_incidents.append(0)

        self.entropy *= 0.98
        
        for civ in self.civs:
            if not civ.is_dead:
                civ.energy -= 6.0
                civ.check_collapse(threshold=0.0)
                if civ.is_dead:
                    self.collapse_causes.append(civ.collapse_cause)
                    if self.mode == "MAIN" and random.random() > 0.3:
                        self.souls.append(civ.extract_soul())
                    
        # Self-Replication
        if self.mode == "MAIN":
            alive_count = sum(1 for c in self.civs if not c.is_dead)
            alive_civs_now = [c for c in self.civs if not c.is_dead]
            rich_civs = [c for c in alive_civs_now if c.energy > 80.0]
            
            if rich_civs and self.souls:
                r_civ = random.choice(rich_civs)
                r_civ.energy -= 40.0
                soul = self.souls.pop(0)
                next(c for c in self.civs if c.civ_id == soul.civ_id).initialize_from_soul(soul, starting_energy=40.0)
            elif alive_count <= max(1, self.n_civ // 2) and self.souls:
                self.souls.sort(key=lambda s: s.generation)
                soul = self.souls.pop(0)
                next(c for c in self.civs if c.civ_id == soul.civ_id).initialize_from_soul(soul, starting_energy=30.0)
                self.entropy += 20.0

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
        
        perf_gaps = []
        total_switches = 0
        final_dist = Counter()
        for c in self.civs:
            perf_gaps.extend(c.performance_gaps)
            total_switches += c.strategy_log.switch_count
            if not c.is_dead:
                final_dist[c.strategy] += 1
                
        # Standardize strategy distribution series to max length
        strat_series = {}
        for s in DISCLOSURE_STRATEGIES.keys():
            strat_series[s] = [d.get(s, 0) for d in self.strategy_distribution_history]

        return {
            "system_survival_rate": int(final_alive > 0),
            "collapse_causes": self.collapse_causes,
            "performance_gaps": perf_gaps,
            "total_switches": total_switches,
            "strategy_diversity_history": self.strategy_diversity_history,
            "strategy_series": strat_series,
            "final_dist": dict(final_dist)
        }

# ──────────────────────────────────────────────────────────────────────────────
# 4. GRID SEARCH & PLOTTING
# ──────────────────────────────────────────────────────────────────────────────
def evaluate_params(args):
    st, er, la, md, seed = args
    random.seed(seed)
    np.random.seed(seed)
    sys = InterCivilizationSystem(mode="MAIN", mem_depth=md, switch_thresh=st, exp_rate=er, leg_adv=la)
    res = sys.run()
    res.update({'switch_thresh': st, 'exp_rate': er, 'leg_adv': la, 'mem_depth': md})
    return res

def run_experiment():
    switch_thresholds = [0.2, 0.4, 0.6]
    exploration_rates = [0.05, 0.15, 0.30]
    leg_advisories = [0.0, 0.5, 1.0]
    mem_depths = [5] # Sim17 fixed
    mc_runs = 30
    
    tasks = []
    for st, er, la, md in itertools.product(switch_thresholds, exploration_rates, leg_advisories, mem_depths):
        for run in range(mc_runs):
            tasks.append((st, er, la, md, hash(f"sim18_{st}_{er}_{la}_{run}") % (2**32-1)))
            
    print(f"Starting Sim 18 with {len(tasks)} runs...")
    t0 = time.time()
    with multiprocessing.Pool(max(1, multiprocessing.cpu_count() - 1)) as pool:
        results = pool.map(evaluate_params, tasks)
        
    print(f"Simulation completed in {time.time() - t0:.2f} seconds.")
    
    if pd is None: return
    df = pd.DataFrame(results)
    plot_results(df)

def plot_results(df):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(PROJECT_ROOT, "docs", "assets")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "civilization_resilience_sim18.png")
    
    fig = plt.figure(figsize=(20, 12))
    plt.suptitle("Simulation 18: Strategy Evolution", fontsize=24, weight="bold")
    colors = {'FULL':'#b2bec3', 'NONE':'#00b894', 'STRENGTH_ONLY':'#e17055', 'VULNERABILITY_ONLY':'#fdcb6e', 'RECIPROCAL':'#0984e3'}
    strats = ['FULL', 'NONE', 'STRENGTH_ONLY', 'VULNERABILITY_ONLY', 'RECIPROCAL']
    
    # [1] Stacked Area of Strategy Distribution (Average over all runs)
    ax1 = plt.subplot(2, 3, 1)
    max_len = max(len(h) for h in df['strategy_diversity_history'])
    avg_series = {s: np.zeros(max_len) for s in strats}
    counts = np.zeros(max_len)
    
    for _, row in df.iterrows():
        series = row['strategy_series']
        length = len(series.get('FULL', []))
        for s in strats:
            avg_series[s][:length] += np.array(series.get(s, []))
        counts[:length] += 1
        
    for s in strats:
        with np.errstate(divide='ignore', invalid='ignore'):
            avg_series[s] = np.divide(avg_series[s], counts, out=np.zeros_like(avg_series[s]), where=counts!=0)
            
    y_stack = np.vstack([avg_series[s] for s in strats])
    x = np.arange(max_len) * 10 # Sampled every 10 turns
    ax1.stackplot(x, y_stack, labels=strats, colors=[colors[s] for s in strats], alpha=0.8)
    ax1.set_title("Strategy Distribution Evolution", fontsize=15)
    ax1.set_xlabel("Turn")
    ax1.set_ylabel("Average Civs per Strategy")
    ax1.legend(loc='upper right')

    # [2] System Survival Progress
    ax2 = plt.subplot(2, 3, 2)
    baselines = {'Sim14': 38.1, 'Sim15': 46.7, 'Sim16': 41.1, 'Sim17(Div)': 30.0}
    sim18_sv = df['system_survival_rate'].mean() * 100
    labels = list(baselines.keys()) + ['Sim18 (Evolv)']
    vals = list(baselines.values()) + [sim18_sv]
    
    bars = ax2.bar(labels, vals, color=['gray', 'gray', 'gray', '#f39c12', '#9b59b6'])
    ax2.set_title("System Survival Progress", fontsize=15)
    ax2.set_ylabel("Survival Rate (%)")
    ax2.set_ylim(0, 105)
    ax2.tick_params(axis='x', rotation=15)
    for bar in bars:
        ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f"{bar.get_height():.1f}%", ha='center', fontweight='bold')

    # [3] Heatmap: Switch Threshold vs Exploration Rate
    ax3 = plt.subplot(2, 3, 3)
    hm_data = df.groupby(['switch_thresh', 'exp_rate'])['system_survival_rate'].mean().unstack() * 100
    cax = ax3.matshow(hm_data.values, cmap='viridis', aspect='auto')
    fig.colorbar(cax, ax=ax3, label="Survival %")
    ax3.set_xticks(np.arange(len(hm_data.columns)))
    ax3.set_yticks(np.arange(len(hm_data.index)))
    ax3.set_xticklabels(hm_data.columns)
    ax3.set_yticklabels(hm_data.index)
    ax3.set_xlabel("Exploration Rate")
    ax3.set_ylabel("Switch Threshold")
    ax3.set_title("Survival Heatmap", y=1.1, fontsize=15)
    for i in range(len(hm_data.index)):
        for j in range(len(hm_data.columns)):
            ax3.text(j, i, f"{hm_data.values[i, j]:.1f}", ha='center', va='center', color='white' if hm_data.values[i, j] < 50 else 'black')

    # [4] Strategy Diversity over Time line chart, split by Leg Advisory
    ax4 = plt.subplot(2, 3, 4)
    for adv in sorted(df['leg_adv'].unique()):
        sub = df[df['leg_adv'] == adv]
        max_sub = max(len(h) for h in sub['strategy_diversity_history'])
        div_avg = np.zeros(max_sub)
        d_cnt = np.zeros(max_sub)
        for _, row in sub.iterrows():
            h = row['strategy_diversity_history']
            div_avg[:len(h)] += h
            d_cnt[:len(h)] += 1
        with np.errstate(divide='ignore', invalid='ignore'):
             valid_avg = np.divide(div_avg, d_cnt, out=np.zeros_like(div_avg), where=d_cnt!=0)
        ax4.plot(np.arange(max_sub)*10, valid_avg, label=f"Advisory Acc.: {adv}", linewidth=2)
    ax4.set_title("Strategy Diversity (Shannon Entropy)", fontsize=15)
    ax4.set_xlabel("Turn")
    ax4.set_ylabel("Entropy")
    ax4.legend()
    ax4.grid(True, linestyle="--", alpha=0.5)

    # [5] Performance Gap Boxplot
    ax5 = plt.subplot(2, 3, 5)
    all_gaps = []
    for g_list in df['performance_gaps']:
        all_gaps.extend(g_list)
    if all_gaps:
        ax5.boxplot(all_gaps, vert=False, patch_artist=True, boxprops=dict(facecolor='#1abc9c'))
        ax5.axvline(0, color='r', linestyle='--')
        ax5.set_title("Performance Gap (Energy Diff Post-Switch)", fontsize=15)
        ax5.set_xlabel("Energy Difference")
        ax5.set_yticks([])

    # [6] Legislature Advisory Impact
    ax6 = plt.subplot(2, 3, 6)
    adv_sv = df.groupby('leg_adv')['system_survival_rate'].mean() * 100
    bars6 = ax6.bar([str(x) for x in adv_sv.index], adv_sv.values, color=['#e74c3c', '#f1c40f', '#27ae60'])
    ax6.set_title("Legislature Advisory Impact", fontsize=15)
    ax6.set_xlabel("Advisory Acceptance Probability")
    ax6.set_ylabel("Survival Rate (%)")
    ax6.set_ylim(0, 105)
    for bar in bars6:
        yval = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width() / 2, yval + 1.5, f"{yval:.1f}%", ha='center', fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"\\nVisualizations successfully saved to: {out_path}")

if __name__ == "__main__":
    run_experiment()
