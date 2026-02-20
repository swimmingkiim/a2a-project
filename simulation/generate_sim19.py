"""
═══════════════════════════════════════════════════════════════════════════════
 Simulation 19: Shock Resilience of Evolved ESS
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


# ─ SHOCKS ─────────────────────────────────────────────────────────────────────
class ShockType(Enum):
    SOLAR_FLARE = "solar_flare"
    BLACKOUT = "blackout"
    PANDEMIC = "pandemic"
    INFORMATION_COLLAPSE = "info_collapse"
    CASCADE = "cascade"

@dataclass
class ShockSchedule:
    scenario_name: str
    shocks: list  # [(turn, ShockType)]

SHOCK_SCENARIOS = {
    'EARLY': ShockSchedule(
        scenario_name='Early Shock',
        shocks=[(200, ShockType.SOLAR_FLARE), (400, ShockType.BLACKOUT)]
    ),
    'PEAK': ShockSchedule(
        scenario_name='Peak Shock',
        shocks=[(800, ShockType.PANDEMIC), (900, ShockType.INFORMATION_COLLAPSE)]
    ),
    'CASCADE': ShockSchedule(
        scenario_name='Cascade Shock',
        shocks=[(600, ShockType.CASCADE)]
    ),
    'NONE': ShockSchedule(
        scenario_name='No Shock',
        shocks=[]
    ),
}

class ShockEngine:
    def __init__(self, schedule: ShockSchedule):
        self.schedule = copy.deepcopy(schedule) # Important: Deepcopy to allow dynamic append (CASCADE)
        self.active_shocks = []

    def tick(self, current_turn: int, civilization_system) -> list[str]:
        triggered = []
        
        # New Shocks
        new_shocks = [s_type for s_turn, s_type in self.schedule.shocks if s_turn == current_turn]
        for shock_type in new_shocks:
            self._apply_shock(shock_type, civilization_system)
            triggered.append(shock_type.value)

        # Ongoing Shocks effects
        self._apply_ongoing_effects(civilization_system)
        
        return triggered

    def _apply_shock(self, shock_type: ShockType, system) -> None:
        if shock_type == ShockType.SOLAR_FLARE:
            for civ in system.civs:
                if not civ.is_dead:
                    civ.energy *= 0.5
            system.soul_corruption_prob = 0.6
            self.active_shocks.append({"type": shock_type, "remaining": 50})

        elif shock_type == ShockType.BLACKOUT:
            system.blackout_active = True
            self.active_shocks.append({"type": shock_type, "remaining": 30})

        elif shock_type == ShockType.PANDEMIC:
            system.pandemic_active = True
            self.active_shocks.append({"type": shock_type, "remaining": 80})

        elif shock_type == ShockType.INFORMATION_COLLAPSE:
            system.info_collapse_active = True
            for civ in system.civs:
                if civ.strategy == 'RECIPROCAL' and not civ.is_dead:
                    civ.strategy = 'NONE'
                    civ.strategy_log.current_strategy = 'NONE'
                    civ.strategy_log.strategy_history.append((system.turn, 'NONE'))
                    civ.strategy_log.switch_count += 1
            self.active_shocks.append({"type": shock_type, "remaining": 40})

        elif shock_type == ShockType.CASCADE:
            self._apply_shock(ShockType.BLACKOUT, system)
            self.schedule.shocks.append((system.turn + 10, ShockType.PANDEMIC))

    def _apply_ongoing_effects(self, system) -> None:
        still_active = []
        for shock in self.active_shocks:
            shock["remaining"] -= 1
            if shock["remaining"] > 0:
                still_active.append(shock)
            else:
                self._clear_shock(shock["type"], system)
        self.active_shocks = still_active

    def _clear_shock(self, shock_type: ShockType, system) -> None:
        if shock_type == ShockType.SOLAR_FLARE:
            system.soul_corruption_prob = 0.3
        elif shock_type == ShockType.BLACKOUT:
            system.blackout_active = False
        elif shock_type == ShockType.PANDEMIC:
            system.pandemic_active = False
        elif shock_type == ShockType.INFORMATION_COLLAPSE:
            system.info_collapse_active = False


# ──────────────────────────────────────────────────────────────────────────────
# 2. EVOLUTION ENGINE & AGENTS (Modified for Sim19 fixed optimal configs)
# ──────────────────────────────────────────────────────────────────────────────
class StrategyEvaluator:
    def __init__(self, switch_threshold: float, exploration_rate: float):
        self.switch_threshold = switch_threshold
        self.exploration_rate = exploration_rate
        self.min_evaluation_period = 20

    def should_switch(self, log: StrategyPerformanceLog, current_turn: int) -> bool:
        if not log.strategy_history: return False
        turns_with_strategy = current_turn - log.strategy_history[-1][0]
        if turns_with_strategy < self.min_evaluation_period: return False

        if len(log.exploitation_incidents) > 0:
            recent_exploitation = sum(log.exploitation_incidents) / max(1, len(log.exploitation_incidents))
            if recent_exploitation > self.switch_threshold: return True

        if len(log.energy_trajectory) >= 10:
            recent = list(log.energy_trajectory)[-10:]
            if recent[-1] < recent[0] * 0.7: return True

        if random.random() < self.exploration_rate: return True
        return False

    def select_new_strategy(self, log: StrategyPerformanceLog, neighbor_strategies: List[str], known_performance: dict) -> str:
        if neighbor_strategies and random.random() < 0.5:
            return random.choice(neighbor_strategies)

        if len(log.strategy_history) > 1 and random.random() < 0.3:
            past_strats = [sh[1] for sh in log.strategy_history[:-1]]
            if past_strats: return random.choice(past_strats)

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
        self.greed_threshold = 0.8
        self.mindless_min_duration = 3
        self.energy_gate = 2000.0
        self.neighbor_greed_threshold = 0.6
        self.other_awareness_weight = 0.9
        self.narrative_trust_weight = 0.6
        
    def get_public_narrative(self, disclosure_strategy: str, full_narrative: CivilizationNarrative, neighbor_strategy: Optional[str], info_collapse: bool = False) -> dict:
        if info_collapse: return {} # No visibility during info collapse

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
        hist_submit = public_narrative.get('historical_submit_ratio', 0.5)
        
        if coop > 0.6 and current_submit_ratio > 0.6: threat = current_submit_ratio * 0.6
        elif hist_submit > 0.6: threat = min(1.0, current_submit_ratio * 1.4)
        else: threat = current_submit_ratio
            
        return (1 - self.narrative_trust_weight) * current_submit_ratio + self.narrative_trust_weight * threat

    def _is_being_greedy(self, current_energy: float) -> bool:
        if len(self.action_history) < 10: return False
        recent = list(self.action_history)
        return (recent.count(CivAction.SUBMIT) / len(recent) > self.greed_threshold) and (current_energy > self.energy_gate)

    def _is_ecosystem_greedy(self, neighbor_data: List[dict]) -> bool:
        if not neighbor_data: return False
        interpreted_threats = [self._interpret_partial_narrative(nd['ratio'], nd['public_narrative']) for nd in neighbor_data]
        return sum(interpreted_threats) / len(interpreted_threats) > self.neighbor_greed_threshold

    def choose_action(self, state: dict, epsilon: float = 0.1, is_blackout: bool = False) -> CivAction:
        if is_blackout:
            self.action_history.append(CivAction.WAIT)
            return CivAction.WAIT

        current_energy = state.get('agent_energy', 0.0)
        neighbor_data = state.get('neighbor_data', [])
        
        self_greedy = self._is_being_greedy(current_energy)
        ecosystem_greedy = self._is_ecosystem_greedy(neighbor_data)
        
        should_restrain = self_greedy or (ecosystem_greedy and random.random() < self.other_awareness_weight)
        if current_energy < self.energy_gate: should_restrain = False
        
        if should_restrain and not self.mindless_mode:
            self.mindless_mode = True
            self.mindless_active_turns = 0
            
        if self.mindless_mode:
            self.mindless_active_turns += 1
            if self.mindless_active_turns >= self.mindless_min_duration and not (self._is_being_greedy(current_energy) or (self._is_ecosystem_greedy(neighbor_data) and random.random() < self.other_awareness_weight)):
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
    def evaluate_strategy_distribution(self, strategy_counts: dict) -> Optional[str]:
        total = sum(strategy_counts.values())
        if total == 0: return None
        for strategy, count in strategy_counts.items():
            if count / total > 0.8:
                recs = {'FULL': 'STRENGTH_ONLY', 'NONE': 'RECIPROCAL', 'VULNERABILITY_ONLY': 'STRENGTH_ONLY'}
                return recs.get(strategy)
        return None

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

    def step_internal(self, system_state: dict, current_turn: int, neighbor_strats: List[str], leg_recommendation: Optional[str], is_blackout: bool) -> Tuple[CivAction, float]:
        if self.is_dead: return CivAction.WAIT, 0.0
            
        self.strategy_log.energy_trajectory.append(self.energy)
        
        if current_turn % 10 == 0:
            if self.evaluator.should_switch(self.strategy_log, current_turn):
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
        
        epsilon = 0.05 + 0.2 * math.exp(-self.age / 100.0)
        updated_state = system_state.copy()
        updated_state['agent_energy'] = self.energy
        
        action = self.exec.choose_action(updated_state, epsilon, is_blackout)
        
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
            
        if self.energy < 1000: self.narrative.crisis_periods += 1
        return action
        
    def check_collapse(self, threshold: float = 0.0):
        if self.energy <= threshold and not self.is_dead:
            self.is_dead = True
            cause = "STARVATION"
            if len(self.exec.history) > 0:
                last_acts = [h[0] for h in self.exec.history][-5:]
                if last_acts.count(CivAction.DEFEND) >= 3: cause = "CONFLICT_EXHAUSTION"
                elif last_acts.count(CivAction.SUBMIT) >= 3: cause = "OVER_SUBMISSION"
            
            self.collapse_cause = cause
            self.narrative.last_collapse_cause = cause
            self.survival_memory.append(cause)
            if len(self.survival_memory) > self.mem_depth: self.survival_memory.pop(0)

    def extract_soul(self, corruption_prob: float) -> MinimalSoul:
        core = self.judiciary.ruleset.copy() if self.judiciary else {}
        top_rules = dict(sorted(core.items(), key=lambda item: item[1], reverse=True)[:3])
        soul_strategy = self.strategy
        if random.random() < corruption_prob:
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
    def __init__(self, shock_scenario: str, recovery_assist: bool, n_civ: int = 5, max_turns=2000):
        self.mode = "MAIN"
        self.n_civ = n_civ
        self.max_turns = max_turns
        self.recovery_assist = recovery_assist
        self.scenario_name = shock_scenario
        
        # Sim 18 Optimal config
        st, er, la, md = 0.2, 0.15, 0.0, 5
        
        strategies = ['FULL', 'STRENGTH_ONLY', 'STRENGTH_ONLY', 'NONE', 'RECIPROCAL']
        self.civs = [Civilization(i, self.mode, strategies[i], md, st, er, la) for i in range(n_civ)]
        self.souls: List[MinimalSoul] = []
        self.legislature = Legislature()
        self.shock_engine = ShockEngine(SHOCK_SCENARIOS[shock_scenario])
        
        self.entropy = 0.0
        self.turn = 0
        self.survival_density_history = []
        self.strategy_distribution_history = []
        
        # Shock State Variables
        self.soul_corruption_prob = 0.3
        self.blackout_active = False
        self.pandemic_active = False
        self.info_collapse_active = False
        self.pandemic_extra_cost = 0.0
        
        # Metrics Tracking Over Time
        self.reciprocal_fraction_history = []
        self.shock_turns = [t for t, _ in SHOCK_SCENARIOS[shock_scenario].shocks]
        self.donated_energy_total = 0.0

    def step(self):
        self.turn += 1
        
        # 1. Apply Shocks
        self.shock_engine.tick(self.turn, self)
        
        # 2. Snapshot
        civ_data = {}
        strat_counts = Counter()
        alive_count = 0
        for c in self.civs:
            if not c.is_dead:
                alive_count += 1
                strat_counts[c.strategy] += 1
                recent = list(c.exec.action_history)
                submit_ratio = recent.count(CivAction.SUBMIT) / len(recent) if len(recent) >= 10 else 0.0
                civ_data[c.civ_id] = {
                    'ratio': submit_ratio,
                    'full_narrative': c.narrative,
                    'strategy': c.strategy,
                    'c_obj': c
                }
                
        self.survival_density_history.append(alive_count / self.n_civ)
        if self.turn % 10 == 0:
            self.strategy_distribution_history.append(dict(strat_counts))
        
        if alive_count > 0:
            self.reciprocal_fraction_history.append(strat_counts.get('RECIPROCAL', 0) / alive_count)
        else:
            self.reciprocal_fraction_history.append(0)
            
        leg_rec = self.legislature.evaluate_strategy_distribution(strat_counts) if self.turn % 10 == 0 else None
            
        actions = {}
        system_state = {'system_entropy': self.entropy}
        for civ in self.civs:
            if not civ.is_dead:
                neighbor_data = []
                neighbor_strats = []
                for nid, nd in civ_data.items():
                    if nid != civ.civ_id:
                        pub_narrative = nd['c_obj'].exec.get_public_narrative(nd['strategy'], nd['full_narrative'], civ.strategy, self.info_collapse_active)
                        if pub_narrative:
                            neighbor_data.append({
                                'ratio': nd['ratio'],
                                'public_narrative': pub_narrative,
                                'strategy': nd['strategy'],
                                'civ_id': nid
                            })
                        neighbor_strats.append(nd['strategy'])

                sys_c = system_state.copy()
                sys_c['neighbor_data'] = neighbor_data
                act = civ.step_internal(sys_c, self.turn, neighbor_strats, leg_rec, self.blackout_active)
                actions[civ.civ_id] = act
                
        alive_civs = [c for c in self.civs if not c.is_dead]
        traders = [c for c in alive_civs if actions.get(c.civ_id) == CivAction.TRADE]
        defenders = [c for c in alive_civs if actions.get(c.civ_id) == CivAction.DEFEND]
        
        # Trade Resolution (Affected by Pandemic)
        trade_success_prob = 0.5 if self.pandemic_active else 1.0
        if len(traders) >= 2:
            random.shuffle(traders)
            for i in range(0, len(traders)-1, 2):
                c1, c2 = traders[i], traders[i+1]
                if random.random() < trade_success_prob:
                    c1.energy += 12.0; c2.energy += 12.0
                    c1.handle_trade_result(True); c2.handle_trade_result(True)
                    c1.strategy_log.trade_successes.append(1); c2.strategy_log.trade_successes.append(1)
                else:
                    c1.handle_trade_result(False); c2.handle_trade_result(False)
                    c1.strategy_log.trade_successes.append(0); c2.strategy_log.trade_successes.append(0)

        # Conflict
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
            for c in alive_civs: c.strategy_log.exploitation_incidents.append(0)

        self.entropy *= 0.98
        
        living_cost = 6.0 + (self.pandemic_extra_cost if self.pandemic_active else 0.0)
        for civ in self.civs:
            if not civ.is_dead and not self.blackout_active:
                civ.energy -= living_cost
                civ.check_collapse(threshold=0.0)
                if civ.is_dead and random.random() > self.soul_corruption_prob:
                    self.souls.append(civ.extract_soul(self.soul_corruption_prob))
                    
        # Self-Replication & RECOVERY_ASSIST
        alive_civs_now = [c for c in self.civs if not c.is_dead]
        
        if self.recovery_assist and len(alive_civs_now) > 0 and self.souls:
             # Find donors
             donors = [c for c in alive_civs_now if c.energy > 4000.0] # > ENERGY_GATE * 2
             if donors:
                 for donor in donors:
                     if self.souls:
                         donation = donor.energy * 0.10
                         donor.energy -= donation
                         self.donated_energy_total += donation
                         
                         soul = self.souls.pop(0)
                         # Reduced energy threshold for rebirth thanks to donation
                         rebirth_civ = next(c for c in self.civs if c.civ_id == soul.civ_id)
                         rebirth_civ.initialize_from_soul(soul, starting_energy=30.0 + donation) # Need less base energy
                         
        # Normal Reproduction (if not assisted or no donors)
        alive_civs_now = [c for c in self.civs if not c.is_dead] # Refresh
        rich_civs = [c for c in alive_civs_now if c.energy > 80.0]
        if rich_civs and self.souls:
            r_civ = random.choice(rich_civs)
            r_civ.energy -= 40.0
            soul = self.souls.pop(0)
            next(c for c in self.civs if c.civ_id == soul.civ_id).initialize_from_soul(soul, starting_energy=40.0)

    def run(self):
        last_e = 0.0
        steady = 0
        for _ in range(self.max_turns):
            self.step()
            al = sum(1 for c in self.civs if not c.is_dead)
            if al == 0 and not self.souls: break
            if abs(self.entropy - last_e) < 0.001: steady += 1
            else: steady = 0
            if steady >= 150: break # Increased wait for stability due to shocks
            last_e = self.entropy
            
        final_alive = sum(1 for c in self.civs if not c.is_dead)
        final_dist = Counter()
        for c in self.civs:
            if not c.is_dead:
                final_dist[c.strategy] += 1
                
        # Store pre-shock distribution for CASCADE scenario
        pre_shock_dist = {}
        if self.scenario_name == 'CASCADE' and len(self.strategy_distribution_history) > 60:
             pre_shock_dist = self.strategy_distribution_history[59] # Right before 600

        strat_series = {}
        for s in DISCLOSURE_STRATEGIES.keys():
            strat_series[s] = [d.get(s, 0) for d in self.strategy_distribution_history]

        return {
            "system_survival_rate": int(final_alive > 0),
            "survival_density_history": self.survival_density_history,
            "strategy_series": strat_series,
            "final_dist": dict(final_dist),
            "pre_shock_dist": pre_shock_dist,
            "reciprocal_fraction": self.reciprocal_fraction_history,
            "donated_energy": self.donated_energy_total,
            "final_pop": final_alive,
            "lengths": len(self.survival_density_history)
        }

# ──────────────────────────────────────────────────────────────────────────────
# 4. GRID SEARCH & PLOTTING
# ──────────────────────────────────────────────────────────────────────────────
def evaluate_params(args):
    scenario, assist, seed = args
    random.seed(seed)
    np.random.seed(seed)
    sys = InterCivilizationSystem(shock_scenario=scenario, recovery_assist=assist, max_turns=1500)
    res = sys.run()
    res.update({'scenario': scenario, 'assist': assist})
    return res

def run_experiment():
    scenarios = ['NONE', 'EARLY', 'PEAK', 'CASCADE']
    assists = [True, False]
    mc_runs = 50
    
    tasks = []
    for s, a in itertools.product(scenarios, assists):
        for run in range(mc_runs):
            tasks.append((s, a, hash(f"sim19_{s}_{a}_{run}") % (2**32-1)))
            
    print(f"Starting Sim 19 with {len(tasks)} runs...")
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
    out_path = os.path.join(out_dir, "civilization_resilience_sim19.png")
    
    fig = plt.figure(figsize=(22, 14))
    plt.suptitle("Simulation 19: Shock Resilience of Evolved ESS", fontsize=24, weight="bold")
    colors = {'FULL':'#b2bec3', 'NONE':'#00b894', 'STRENGTH_ONLY':'#e17055', 'VULNERABILITY_ONLY':'#fdcb6e', 'RECIPROCAL':'#0984e3'}
    strats = ['FULL', 'NONE', 'STRENGTH_ONLY', 'VULNERABILITY_ONLY', 'RECIPROCAL']
    
    # [1] Survival by Scenario & Assist
    ax1 = plt.subplot(2, 3, 1)
    df_sv = df.groupby(['scenario', 'assist'])['system_survival_rate'].mean().unstack() * 100
    df_sv = df_sv.reindex(['NONE', 'EARLY', 'PEAK', 'CASCADE'])
    
    x = np.arange(len(df_sv))
    width = 0.35
    ax1.bar(x - width/2, df_sv[False], width, label='No Assist', color='#e74c3c')
    ax1.bar(x + width/2, df_sv[True], width, label='Assist', color='#2ecc71')
    ax1.axhline(y=35.9, color='k', linestyle='--', label='Sim18 Baseline')
    
    ax1.set_ylabel('Survival Rate (%)')
    ax1.set_title('Survival by Shock Scenario', fontsize=14)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_sv.index)
    ax1.legend()

    # [2] Strategy Distribution Evolution (4 subplots for each scenario, Assist=False)
    # To fit into 6 panels easily, we'll plot the CASCADE (the most extreme) distribution here
    ax2 = plt.subplot(2, 3, 2)
    casc_df = df[(df['scenario'] == 'CASCADE') & (df['assist'] == False)]
    max_len = int(casc_df['lengths'].max() / 10)
    avg_series = {s: np.zeros(max_len) for s in strats}
    counts = np.zeros(max_len)
    
    for _, row in casc_df.iterrows():
        series = row['strategy_series']
        length = len(series.get('FULL', []))
        for s in strats:
             avg_series[s][:length] += np.array(series.get(s, []))
        counts[:length] += 1
        
    for s in strats:
        with np.errstate(divide='ignore', invalid='ignore'):
            avg_series[s] = np.divide(avg_series[s], counts, out=np.zeros_like(avg_series[s]), where=counts!=0)
    
    y_stack = np.vstack([avg_series[s] for s in strats])
    x_turn = np.arange(max_len) * 10
    ax2.stackplot(x_turn, y_stack, labels=strats, colors=[colors[s] for s in strats], alpha=0.8)
    ax2.axvline(x=600, color='red', linestyle='--', linewidth=2, label="Shock")
    ax2.set_title("Distribution: CASCADE (No Assist)", fontsize=14)
    ax2.set_xlabel("Turn")
    ax2.set_ylabel("Civs")

    # [3] Survival Recovery Trajectory (Avg fraction alive)
    ax3 = plt.subplot(2, 3, 3)
    for scen in ['NONE', 'CASCADE', 'PEAK']:
        sub = df[(df['scenario'] == scen) & (df['assist'] == True)]
        m_len = sub['lengths'].max()
        avg_pop = np.zeros(m_len)
        p_cnt = np.zeros(m_len)
        for _, row in sub.iterrows():
            arr = np.array(row['survival_density_history'])
            avg_pop[:len(arr)] += arr
            p_cnt[:len(arr)] += 1
        with np.errstate(divide='ignore', invalid='ignore'):
            final_arr = np.divide(avg_pop, p_cnt, out=np.zeros_like(avg_pop), where=p_cnt!=0)
        ax3.plot(np.arange(m_len), final_arr * 100, label=f"{scen} (Assist)", linewidth=2)
        
    ax3.set_title("Population Density Trajectory", fontsize=14)
    ax3.set_xlabel("Turn")
    ax3.set_ylabel("Alive Fraction (%)")
    ax3.legend()

    # [4] Pre vs Post Shock ESS (Pie Charts) - CASCADE Scenario
    ax4 = plt.subplot(2, 3, 4)
    c_df = df[df['scenario'] == 'CASCADE']
    
    pre_sum = Counter()
    post_sum = Counter()
    for _, row in c_df.iterrows():
        for k, v in row['pre_shock_dist'].items(): pre_sum[k] += v
        for k, v in row['final_dist'].items(): post_sum[k] += v
        
    labels1, sizes1 = list(pre_sum.keys()), list(pre_sum.values())
    labels2, sizes2 = list(post_sum.keys()), list(post_sum.values())
    
    col_pre = [colors.get(l, '#000') for l in labels1]
    col_post = [colors.get(l, '#000') for l in labels2]
    
    ax4.pie(sizes1, labels=labels1, colors=col_pre, autopct='%1.1f%%', center=(0,0), frame=False, radius=0.45)
    ax4.pie(sizes2, labels=labels2, colors=col_post, autopct='%1.1f%%', center=(1.2,0), frame=False, radius=0.45)
    ax4.text(0, 0.6, "Pre-Shock (Turn 590)", ha='center', fontweight='bold')
    ax4.text(1.2, 0.6, "Post-Shock Final", ha='center', fontweight='bold')
    ax4.axis('equal')
    ax4.set_title("Strategy ESS Reset (CASCADE)", fontsize=14)

    # [5] Solidarity Cost-Benefit (Energy Donated vs System Survival Gain rate)
    ax5 = plt.subplot(2, 3, 5)
    non_assist = df[df['assist'] == False].groupby('scenario')['system_survival_rate'].mean()
    assist_gains = []
    energy_costs = []
    valid_scens = ['EARLY', 'PEAK', 'CASCADE'] # Exclude NONE since no shocks usually means no big collapses to assist
    
    for _, row in df[(df['assist'] == True) & (df['scenario'].isin(valid_scens))].iterrows():
        base = non_assist[row['scenario']]
        diff = row['system_survival_rate'] - base
        assist_gains.append(diff * 100) # Convert to %
        energy_costs.append(row['donated_energy'])
        
    ax5.scatter(energy_costs, assist_gains, alpha=0.5, color='#9b59b6')
    ax5.axhline(0, color='r', linestyle='--')
    ax5.set_title("Solidarity Impact Profile", fontsize=14)
    ax5.set_xlabel("Total Energy Donated")
    ax5.set_ylabel("Survival Probability Gain (%) vs Base")

    # [6] Information Collapse: Reciprocal Resilience
    ax6 = plt.subplot(2, 3, 6)
    peak_df = df[df['scenario'] == 'PEAK']
    m_len = peak_df['lengths'].max()
    avg_recip = np.zeros(m_len)
    rcnt = np.zeros(m_len)
    
    for _, row in peak_df.iterrows():
        arr = np.array(row['reciprocal_fraction'])
        avg_recip[:len(arr)] += arr
        rcnt[:len(arr)] += 1
        
    with np.errstate(divide='ignore', invalid='ignore'):
         val_recip = np.divide(avg_recip, rcnt, out=np.zeros_like(avg_recip), where=rcnt!=0)
    
    ax6.plot(np.arange(m_len), val_recip * 100, color='#0984e3', linewidth=2)
    ax6.axvspan(900, 940, color='gray', alpha=0.3, label="Info Collapse")
    ax6.set_title("RECIPROCAL Fraction under PEAK Shock", fontsize=14)
    ax6.set_xlabel("Turn")
    ax6.set_ylabel("% Pop using RECIPROCAL")
    ax6.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"\nVisualizations successfully saved to: {out_path}")

if __name__ == "__main__":
    run_experiment()
