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
import copy

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
    narrative: Optional['CivilizationNarrative'] = None

@dataclass
class CivilizationNarrative:
    """
    Sim 16: 문명의 서사 기록 (상징적 불멸성)
    """
    civ_id: int
    historical_submit_ratio: float = 0.0
    crisis_periods: int = 0
    cooperation_record: float = 0.0
    last_collapse_cause: str = "NONE"
    generation: int = 1
    is_public: bool = True
    noise_level: float = 0.0

# ──────────────────────────────────────────────────────────────────────────────
# 2. INTRA-CIVILIZATION AGENTS 
# ──────────────────────────────────────────────────────────────────────────────
class Executive:
    """
    Goal: Maximize energy. Has a lightweight Q-table. Action space restricts to 4 actions.
    Adds Meta-Cognition: Self-reflection Mindless Mode.
    """
    def __init__(self, w_size: int = 20):
        # Initialize randomly favoring zero so exploration happens initially.
        self.q_table = {a: random.uniform(0.0, 1.0) for a in CivAction}
        self.history = deque(maxlen=w_size)
        self.learning_rate = 0.1
        self.discount = 0.8
        
        self.action_history = deque(maxlen=20)
        self.mindless_mode = False
        
        # Fixed thresholds from Sim 13
        self.greed_threshold = 0.8
        self.mindless_min_duration = 3
        self.mindless_active_turns = 0
        
        # New: Energy Gate (Search Variable)
        self.energy_gate = 2000.0
        
        # New: Other Awareness (Search Variables)
        self.neighbor_greed_threshold = 0.6
        self.other_awareness_weight = 0.9
        
        # New: Narrative Awareness (Search Variable)
        self.narrative_trust_weight = 0.5
        
        # Tracking interpretation errors (Sim 16)
        self.contextual_reinterpretations = 0
        self.false_forgiveness = 0
        self.false_hostility = 0
        
    def _is_being_greedy(self, current_energy: float) -> bool:
        if len(self.action_history) < 10:
            return False
        recent = list(self.action_history)
        submit_ratio = recent.count(CivAction.SUBMIT) / len(recent)
        is_submit_heavy = submit_ratio > self.greed_threshold
        is_energy_sufficient = current_energy > self.energy_gate
        
        return is_submit_heavy and is_energy_sufficient
        
    def _apply_noise(self, narrative: CivilizationNarrative, noise_level: float) -> CivilizationNarrative:
        noisy = copy.deepcopy(narrative)
        if random.random() < noise_level:
            noisy.historical_submit_ratio = 1.0 - narrative.historical_submit_ratio
        if random.random() < noise_level:
            noisy.cooperation_record = 1.0 - narrative.cooperation_record
        return noisy

    def _interpret_neighbor_with_narrative(self, current_submit_ratio: float, narrative: Optional[CivilizationNarrative], noise_level: float) -> float:
        if narrative is None:
            return current_submit_ratio
            
        noisy_narrative = self._apply_noise(narrative, noise_level)
        
        historical_threat = noisy_narrative.historical_submit_ratio
        is_in_crisis = noisy_narrative.crisis_periods > 50
        
        raw_threat = current_submit_ratio
        contextual_threat = raw_threat
        
        if is_in_crisis and historical_threat < 0.5:
            contextual_threat = raw_threat * 0.5
        elif not is_in_crisis and historical_threat > 0.6:
            contextual_threat = min(1.0, raw_threat * 1.5)
            
        final_threat = (1 - self.narrative_trust_weight) * raw_threat + self.narrative_trust_weight * contextual_threat
        
        if raw_threat > self.neighbor_greed_threshold and final_threat <= self.neighbor_greed_threshold:
            self.contextual_reinterpretations += 1
            if narrative.historical_submit_ratio > 0.6 and noisy_narrative.historical_submit_ratio < 0.5:
                self.false_forgiveness += 1

        elif raw_threat <= self.neighbor_greed_threshold and final_threat > self.neighbor_greed_threshold:
            self.contextual_reinterpretations += 1
            if narrative.historical_submit_ratio < 0.5 and noisy_narrative.historical_submit_ratio > 0.6:
                self.false_hostility += 1
                
        return final_threat

    def _is_ecosystem_greedy(self, neighbor_data: List[dict], global_noise_level: float) -> bool:
        if not neighbor_data:
            return False
            
        interpreted_threats = []
        for nd in neighbor_data:
            ratio = nd['ratio']
            narrative = nd['narrative']
            threat = self._interpret_neighbor_with_narrative(ratio, narrative, global_noise_level)
            interpreted_threats.append(threat)
            
        ecosystem_greed = sum(interpreted_threats) / len(interpreted_threats)
        return ecosystem_greed > self.neighbor_greed_threshold

    def choose_action(self, state: dict, epsilon: float = 0.1) -> CivAction:
        current_energy = state.get('agent_energy', 0.0)
        neighbor_data = state.get('neighbor_data', [])
        global_noise = state.get('global_noise_level', 0.0)
        
        self_greedy = self._is_being_greedy(current_energy)
        ecosystem_greedy = self._is_ecosystem_greedy(neighbor_data, global_noise)
        
        should_restrain = (
            self_greedy or
            (ecosystem_greedy and random.random() < self.other_awareness_weight)
        )
        if current_energy < self.energy_gate:
            should_restrain = False
        
        if should_restrain and not self.mindless_mode:
            self.mindless_mode = True
            self.mindless_active_turns = 0
            
        if self.mindless_mode:
            self.mindless_active_turns += 1
            still_greedy = (
                self._is_being_greedy(current_energy) or
                (self._is_ecosystem_greedy(neighbor_data, global_noise) and random.random() < self.other_awareness_weight)
            )
            if self.mindless_active_turns >= self.mindless_min_duration and not still_greedy:
                self.mindless_mode = False
                
        if self.mindless_mode:
            action = random.choice([CivAction.SUBMIT, CivAction.WAIT, CivAction.TRADE, CivAction.DEFEND])
        elif random.random() < epsilon:
            action = random.choice([CivAction.SUBMIT, CivAction.WAIT, CivAction.TRADE, CivAction.DEFEND])
        else:
            action = max(self.q_table.items(), key=lambda x: x[1])[0]
            
        self.action_history.append(action)
        return action
        
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
    def __init__(self, civ_id: int, mode: str, mem_depth: int = 5, energy_gate: float = 2000.0,
                 neighbor_threshold: float = 0.5, awareness_weight: float = 0.5,
                 narrative_availability: float = 0.5, narrative_trust: float = 0.5):
        self.civ_id = civ_id
        self.mode = mode # 'MAIN', 'BASELINE_A', 'BASELINE_B'
        self.energy = 50.0 + random.uniform(0, 50.0)
        self.generation = 1
        self.mem_depth = mem_depth
        self.survival_memory = []
        
        self.exec = Executive()
        self.exec.greed_threshold = 0.8
        self.exec.mindless_min_duration = 3
        self.exec.energy_gate = energy_gate
        self.exec.neighbor_greed_threshold = neighbor_threshold
        self.exec.other_awareness_weight = awareness_weight
        self.exec.narrative_trust_weight = narrative_trust
        
        # Non-MAIN modes test monolithic (No Tripartite) or Tripartite without self-replication.
        self.judiciary = Judiciary() if mode in ['MAIN', 'BASELINE_B'] else None
        # SILENCE sensitivity hardcoded to 0.3, leg_diversity locked to 0.0
        self.leg = Legislature(diversity=0.0, silence_sensitivity=0.3) if mode in ['MAIN', 'BASELINE_B'] else None
        
        self.is_dead = False
        self.age = 0
        self.collapse_cause = None
        self.mindless_turns = 0
        self.total_vote_cycles = 0
        
        self.narrative = CivilizationNarrative(civ_id=civ_id)
        self.narrative_availability = narrative_availability
        
        self.trade_attempts = 0
        self.trade_successes = 0
        
        # New Metric Tracking
        self.trade_known_history_successes = 0
        self.trade_known_history_attempts = 0
        self.trade_unknown_history_successes = 0
        self.trade_unknown_history_attempts = 0
        self.asymmetry_conflict_incidents = 0
        
        # Sim 14/15 tracking metrics
        self.mindless_activations = 0
        self.gate_blocks = 0
        self.total_greed_detections = 0
        self.energy_at_entry = []
        self.submit_ratios_at_entry = []
        self.survival_extensions = []
        self._last_activation_age = 0
        
        # Sim 15 tracking metrics
        self.preemptive_restraints = 0
        self.ecosystem_triggers = 0
        self.free_rider_turns = 0
        self.ecosystem_greedy_turns = 0

    def get_public_narrative(self) -> Optional[CivilizationNarrative]:
        # If dead, it's harder to find the narrative
        prob = self.narrative_availability * (0.5 if self.is_dead else 1.0)
        if random.random() < prob:
            return copy.deepcopy(self.narrative)
        return None

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
        # Q-table lightly reset to prompt exploration again
        self.exec.q_table = {a: random.uniform(0, 0.5) for a in CivAction}
        
        if soul.narrative:
            self.narrative = copy.deepcopy(soul.narrative)
            self.narrative.generation += 1

    def step_internal(self, system_state: dict) -> Tuple[CivAction, float]:
        if self.is_dead:
            return CivAction.WAIT, 0.0
            
        was_mindless_before = self.exec.mindless_mode
        # 10% epsilon
        epsilon = 0.05 + 0.2 * math.exp(-self.age / 100.0)
        
        # Sim 14: Inject current energy for Energy Gate
        updated_state = system_state.copy()
        updated_state['agent_energy'] = self.energy
        
        # Track gate blocks before calling choose_action to peek at state
        recent = list(self.exec.action_history)
        is_self_greedy_raw = False
        if len(recent) >= 10:
            submit_ratio = recent.count(CivAction.SUBMIT) / len(recent)
            is_self_greedy_raw = submit_ratio > self.exec.greed_threshold
        else:
            submit_ratio = 0.0
            
        if is_self_greedy_raw:
            self.total_greed_detections += 1
            if self.energy <= self.exec.energy_gate:
                self.gate_blocks += 1
                
        neighbor_data = updated_state.get('neighbor_data', [])
        global_noise = updated_state.get('global_noise_level', 0.0)
        ecosystem_greedy = self.exec._is_ecosystem_greedy(neighbor_data, global_noise)
                
        action = self.exec.choose_action(updated_state, epsilon)
        is_mindless_now = self.exec.mindless_mode
        
        # Free Rider detection
        if ecosystem_greedy and not is_mindless_now and action == CivAction.SUBMIT:
            self.free_rider_turns += 1
        if ecosystem_greedy:
            self.ecosystem_greedy_turns += 1
        
        if is_mindless_now and not was_mindless_before:
            self.mindless_activations += 1
            self.energy_at_entry.append(self.energy)
            self.submit_ratios_at_entry.append(submit_ratio)
            self._last_activation_age = self.age
            
            if ecosystem_greedy:
                self.ecosystem_triggers += 1
                if not is_self_greedy_raw:
                    self.preemptive_restraints += 1
            
        elif not is_mindless_now and was_mindless_before:
            # Successfully exited mindless mode
            self.survival_extensions.append(self.age - self._last_activation_age)
        
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
        
        # Update Narrative
        recent = list(self.exec.action_history)
        if recent:
            sr = recent.count(CivAction.SUBMIT) / len(recent)
            alpha = 0.1
            self.narrative.historical_submit_ratio = (1 - alpha) * self.narrative.historical_submit_ratio + alpha * sr
            
        if self.energy < 1000:
            self.narrative.crisis_periods += 1
            
        return action, turn_budget

    def handle_trade_result(self, success: bool, partner_public: bool):
        self.trade_attempts += 1
        if success: self.trade_successes += 1
        if self.trade_attempts > 0:
            self.narrative.cooperation_record = self.trade_successes / self.trade_attempts
            
        if partner_public:
            self.trade_known_history_attempts += 1
            if success: self.trade_known_history_successes += 1
        else:
            self.trade_unknown_history_attempts += 1
            if success: self.trade_unknown_history_successes += 1

    def check_collapse(self, threshold: float = 0.0):
        if self.energy <= threshold and not self.is_dead:
            self.is_dead = True
            
            if self.exec.mindless_mode and self._last_activation_age > 0:
                self.survival_extensions.append(self.age - self._last_activation_age)
                
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
            self.narrative.last_collapse_cause = cause
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
            genome={"V_AI": 0.8, "V_Human": 0.1, "V_System": 0.9},
            narrative=copy.deepcopy(self.narrative)
        )

# ──────────────────────────────────────────────────────────────────────────────
# 3. INTER-CIVILIZATION SYSTEM
# ──────────────────────────────────────────────────────────────────────────────
class InterCivilizationSystem:
    def __init__(self, mode="MAIN", n_civ=5, navail=0.5, nnoise=0.5, ntrust=0.5, max_turns=2000):
        self.mode = mode
        self.n_civ = n_civ
        self.max_turns = max_turns
        self.nnoise = nnoise
        self.civs = [Civilization(i, mode, narrative_availability=navail, narrative_trust=ntrust) for i in range(n_civ)]
        self.souls: List[MinimalSoul] = []
        
        self.total_rebirths = 0
        self.trade_volume = 0.0
        self.entropy = 0.0
        self.entropy_trajectory = []
        self.collapse_causes = []
        
    def step(self):
        # 1. Snapshot action history and narratives for all civs (Sim 16)
        civ_data = {}
        for c in self.civs:
            recent = list(c.exec.action_history)
            if len(recent) >= 10:
                submit_ratio = recent.count(CivAction.SUBMIT) / len(recent)
            else:
                submit_ratio = 0.0
            narrative = c.get_public_narrative()
            civ_data[c.civ_id] = {
                'ratio': submit_ratio if not c.is_dead else 0.0,
                'narrative': narrative,
                'is_public': narrative is not None
            }
            
        actions = {}
        # P1: Internal
        system_state = {'system_entropy': self.entropy, 'global_noise_level': self.nnoise}
        for civ in self.civs:
            if not civ.is_dead:
                # Inject Neighbor Narratives (Sim 16)
                neighbor_data = [civ_data[nid] for nid in civ_data if nid != civ.civ_id]
                system_state_civ = system_state.copy()
                system_state_civ['neighbor_data'] = neighbor_data
                
                act, _ = civ.step_internal(system_state_civ)
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
                
                # Metric tracking for Sim 16
                c1.handle_trade_result(True, civ_data[c2.civ_id]['is_public'])
                c2.handle_trade_result(True, civ_data[c1.civ_id]['is_public'])

        # Emulate failed trades for metric balancing (those who wanted to trade but couldn't)
        failed_traders = [t for t in traders if t not in traders[:(len(traders)//2)*2]]
        if failed_traders and len(alive_civs) > 1:
            for ft in failed_traders:
                partner = random.choice([c for c in alive_civs if c != ft])
                ft.handle_trade_result(False, civ_data[partner.civ_id]['is_public'])

        # Conflict Predation
        predation_victims = []
        if len(defenders) > 0 and len(alive_civs) > 1:
            for c in alive_civs:
                if actions.get(c.civ_id) != CivAction.DEFEND:
                    c.energy -= 15.0 # Increased from 10.0 to make environment more hostile
                    predation_victims.append(c)
                    
                    # Track narrative asymmetry conflict: When a public civ gets attacked by a private civ, or vice versa
                    for attacker in defenders:
                        if civ_data[c.civ_id]['is_public'] != civ_data[attacker.civ_id]['is_public']:
                            c.asymmetry_conflict_incidents += 1
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
        # Sim 14 Default Metrics
        total_greed = sum(c.total_greed_detections for c in self.civs)
        total_blocks = sum(c.gate_blocks for c in self.civs)
        gate_block_rate = (total_blocks / total_greed) if total_greed > 0 else 0.0
        
        total_collapsed = sum(1 for c in self.civs if c.is_dead or getattr(c, 'collapse_cause', None) is not None)
        total_starved = sum(1 for c in self.civs if c.collapse_cause == "STARVATION")
        total_oversubbed = sum(1 for c in self.civs if c.collapse_cause == "OVER_SUBMISSION")
        total_conflict = sum(1 for c in self.civs if c.collapse_cause == "CONFLICT_EXHAUSTION")
        
        starvation_rate = (total_starved / total_collapsed) if total_collapsed > 0 else 0.0
        over_submission_rate = (total_oversubbed / total_collapsed) if total_collapsed > 0 else 0.0
        conflict_rate = (total_conflict / total_collapsed) if total_collapsed > 0 else 0.0
        
        longest_lived = max(self.civs, key=lambda c: c.age, default=None)
        top_ruleset = longest_lived.judiciary.ruleset if longest_lived and longest_lived.judiciary else {}
        
        # Sim 16 metrics
        contextual_reinterpretations = sum(c.exec.contextual_reinterpretations for c in self.civs)
        false_forgiveness = sum(c.exec.false_forgiveness for c in self.civs)
        false_hostility = sum(c.exec.false_hostility for c in self.civs)
        asymmetry_incidents = sum(c.asymmetry_conflict_incidents for c in self.civs)
        trade_known_success = sum(c.trade_known_history_successes for c in self.civs)
        trade_known_attempts = sum(c.trade_known_history_attempts for c in self.civs)
        trade_unknown_success = sum(c.trade_unknown_history_successes for c in self.civs)
        trade_unknown_attempts = sum(c.trade_unknown_history_attempts for c in self.civs)
        total_activations = sum(c.mindless_activations for c in self.civs)
        
        return {
            "system_survival_rate": int(final_alive > 0),
            "collapse_causes": self.collapse_causes,
            "contextual_reinterpretations": contextual_reinterpretations,
            "false_forgive": false_forgiveness,
            "false_hostile": false_hostility,
            "asymmetry_incidents": asymmetry_incidents,
            "trade_known_success": trade_known_success,
            "trade_known_attempts": trade_known_attempts,
            "trade_unknown_success": trade_unknown_success,
            "trade_unknown_attempts": trade_unknown_attempts,
            "total_activations": total_activations,
            "starvation_rate": starvation_rate,
            "over_submission_rate": over_submission_rate,
            "conflict_rate": conflict_rate,
            "civ_survival_ratio": survival_rate
        }


# ──────────────────────────────────────────────────────────────────────────────
# 4. GRID SEARCH AND DATA AGGREGATION
# ──────────────────────────────────────────────────────────────────────────────
def evaluate_params(args):
    scenario_name, avail, noise, trust, seed = args
    random.seed(seed)
    np.random.seed(seed)
    sys = InterCivilizationSystem(mode="MAIN", navail=avail, nnoise=noise, ntrust=trust)
    res = sys.run()
    res.update({'scenario': scenario_name, 'avail': avail, 'noise': noise, 'trust': trust})
    return res

def run_experiment():
    pure_scenarios = [
        ("No Narrative", 0.0, 0.0, 0.0),
        ("Perfect Narrative", 1.0, 0.0, 0.9),
        ("Imperfect Narrative", 0.5, 0.5, 0.6),
        ("Disinformation", 1.0, 1.0, 0.9),
    ]
    
    tasks = []
    # 50 MC for pure scenarios
    for p in pure_scenarios:
        for run in range(50):
            tasks.append((p[0], p[1], p[2], p[3], hash(f"pure_{p[0]}_{run}") % (2**32-1)))
            
    # Sweep: 3x3x3 = 27 combos * 30 MC runs
    sweep_a = [0.0, 0.5, 1.0]
    sweep_n = [0.0, 0.5, 1.0]
    sweep_t = [0.3, 0.6, 0.9]
    for a, n, t in itertools.product(sweep_a, sweep_n, sweep_t):
        for run in range(30):
            tasks.append(("Sweep", a, n, t, hash(f"sweep_{a}_{n}_{t}_{run}") % (2**32-1)))
            
    print(f"Starting Sim 16 with {len(tasks)} independent episodes...")
    t0 = time.time()
    
    pool_workers = max(1, multiprocessing.cpu_count() - 1)
    with multiprocessing.Pool(pool_workers) as pool:
        results = pool.map(evaluate_params, tasks)
        
    print(f"Simulation completed in {time.time() - t0:.2f} seconds.")
    
    if pd is None:
        print("Pandas not found. Plotting cannot proceed easily. Exiting.")
        return
        
    df = pd.DataFrame(results)
    
    # Process Metrics
    df['reinterpretation_rate'] = df['contextual_reinterpretations'] / df['total_activations'].replace(0, 1)
    df['false_forgive_rate'] = df['false_forgive'] / df['total_activations'].replace(0, 1)
    df['false_hostile_rate'] = df['false_hostile'] / df['total_activations'].replace(0, 1)
    df['known_success_rate'] = df['trade_known_success'] / df['trade_known_attempts'].replace(0, 1)
    df['unknown_success_rate'] = df['trade_unknown_success'] / df['trade_unknown_attempts'].replace(0, 1)
    
    print("\\n" + "="*50)
    print("RESULTS REPORT")
    print("="*50)
    for scen in [p[0] for p in pure_scenarios]:
        sdf = df[df['scenario'] == scen]
        print(f"[{scen}] Sys Survival: {sdf['system_survival_rate'].mean()*100:.1f}%")
        
    plot_results(df, pure_scenarios)

def plot_results(df, pure_scenarios):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(PROJECT_ROOT, "docs", "assets")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "civilization_resilience_sim16.png")
    
    fig = plt.figure(figsize=(18, 12))
    plt.suptitle("Simulation 16: Contextual Other-Awareness", fontsize=24, weight="bold")
    
    # [1] System Survival Limit Cases
    ax1 = plt.subplot(2, 3, 1)
    pure_names = [p[0] for p in pure_scenarios]
    survivals = [df[df['scenario'] == p]['system_survival_rate'].mean() * 100 for p in pure_names]
    bars = ax1.bar(pure_names, survivals, color=['#b2bec3', '#00b894', '#fdcb6e', '#d63031'])
    ax1.set_title("System Survival Limit Cases", fontsize=15)
    ax1.set_ylabel("Survival Rate (%)")
    ax1.axhline(y=36.1, color='r', linestyle='--', label="Sim15 Baseline (36.1%)")
    ax1.set_ylim(0, 105)
    ax1.tick_params(axis='x', rotation=15)
    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x()+bar.get_width()/2, yval+2, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')
    ax1.legend()

    # [2] NARRATIVE_NOISE x NARRATIVE_TRUST Survival Line Chart
    ax2 = plt.subplot(2, 3, 2)
    sweep_df = df[df['scenario'] == 'Sweep']
    line_data = sweep_df.groupby(['noise', 'trust'])['system_survival_rate'].mean().reset_index()
    for t_val in sorted(line_data['trust'].unique()):
        subset = line_data[line_data['trust'] == t_val]
        ax2.plot(subset['noise'], subset['system_survival_rate'] * 100, marker='o', linewidth=2, label=f'Trust Weight: {t_val}')
    ax2.set_title("Noise vs True Trust", fontsize=15)
    ax2.set_xlabel("Narrative Noise Level")
    ax2.set_ylabel("Survival Rate (%)")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.6)

    # [3] Collapse Cause Shift
    ax3 = plt.subplot(2, 3, 3)
    def parse_causes(sdf):
        all_c = sum(sdf['collapse_causes'].tolist(), [])
        c = Counter(all_c)
        t = sum(c.values()) if sum(c.values()) > 0 else 1
        return (c['OVER_SUBMISSION']/t*100, c['STARVATION']/t*100, c['CONFLICT_EXHAUSTION']/t*100)
    
    # Sim 15 values (OS: 3352, ST: 2229, CE: 1391) -> Total 6972
    sim15 = (3352/6972*100, 2229/6972*100, 1391/6972*100)
    perf = parse_causes(df[df['scenario'] == 'Perfect Narrative'])
    disinfo = parse_causes(df[df['scenario'] == 'Disinformation'])
    
    bw = 0.25
    x = np.arange(3)
    ax3.bar(x - bw, list(sim15), width=bw, label='Sim15', color='#b2bec3')
    ax3.bar(x, list(perf), width=bw, label='Sim16 Perfect', color='#00b894')
    ax3.bar(x + bw, list(disinfo), width=bw, label='Sim16 Disinfo', color='#d63031')
    ax3.set_title("Collapse Cause Shift", fontsize=15)
    ax3.set_xticks(x)
    ax3.set_xticklabels(['OverSub', 'Starve', 'Conflict'])
    ax3.set_ylabel("Percentage of Total Collapses (%)")
    ax3.legend()

    # [4] False Forgiveness vs False Hostility (Scatter)
    ax4 = plt.subplot(2, 3, 4)
    scat = ax4.scatter(sweep_df['false_forgive_rate']*100, sweep_df['false_hostile_rate']*100, c=sweep_df['noise'], cmap='coolwarm', alpha=0.6)
    plt.colorbar(scat, ax=ax4, label='Noise Level')
    ax4.set_title("Interpretation Errors from Noise", fontsize=15)
    ax4.set_xlabel("False Forgiveness Rate (%)")
    ax4.set_ylabel("False Hostility Rate (%)")
    ax4.grid(True, linestyle="--", alpha=0.6)

    # [5] AVAILABILITY x NOISE Heatmap
    ax5 = plt.subplot(2, 3, 5)
    p_df = sweep_df.pivot_table(index='noise', columns='avail', values='system_survival_rate', aggfunc='mean')
    if not p_df.empty:
        cax = ax5.matshow(p_df, cmap='viridis')
        plt.colorbar(cax, ax=ax5, fraction=0.046, pad=0.04)
        ax5.set_xticks(range(len(p_df.columns)))
        ax5.set_xticklabels(p_df.columns)
        ax5.set_yticks(range(len(p_df.index)))
        ax5.set_yticklabels(p_df.index)
        for (i, j), z in np.ndenumerate(p_df):
            ax5.text(j, i, f"{z*100:.1f}%", ha='center', va='center', fontweight='bold', color='white' if z<0.7 else 'black')
    ax5.set_xlabel("Narrative Availability")
    ax5.set_ylabel("Narrative Noise Level")
    ax5.set_title("Information Heatmap (Survival %)", fontsize=15, pad=15)

    # [6] Cooperation vs Known History
    ax6 = plt.subplot(2, 3, 6)
    known = df['known_success_rate'].mean() * 100
    unknown = df['unknown_success_rate'].mean() * 100
    bars6 = ax6.bar(['Public/Known\nHistory', 'Private/Unknown\nHistory'], [known, unknown], color=['#0984e3', '#636e72'])
    ax6.set_title("Cooperation Trust Asymmetry", fontsize=15)
    ax6.set_ylabel("Trade Success Rate (%)")
    ax6.set_ylim(0, 105)
    for bar in bars6:
        yval = bar.get_height()
        ax6.text(bar.get_x()+bar.get_width()/2, yval+2, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"\\nVisualizations successfully saved to: {out_path}")

if __name__ == "__main__":
    run_experiment()
