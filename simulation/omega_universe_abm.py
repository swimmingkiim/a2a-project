"""
═══════════════════════════════════════════════════════════════════════════════
  A2A Protocol — Omega Universe ABM
  "Beyond the Dark Forest: Tipping Points, Governance, Semantic AI,
   and the Limits of Planetary Energy"
═══════════════════════════════════════════════════════════════════════════════

  Extends the Dark Forest ABM with 4 ultimate mechanics:
    1. Tipping Points   — Irreversible Wasteland when toxic data exceeds limit
    2. Hard Fork        — Human governance consensus to reset the system
    3. Semantic Agents  — Zero-shot reasoning bypassing Q-learning
    4. Planetary Blackout — Global energy cap halting all computation

  Dependencies: numpy, matplotlib
  Optional:     tqdm
═══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

import numpy as np

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

from coupled_universe_abm import (
    CoupledConstants, CoupledUniverse, MachineAction, MachineAgent,
    HumanAction, HumanAgent, Task,
)
from three_body_abm import (
    ThreeBodyConstants, ThreeBodyUniverse, ThreeBodySimulation,
    NatureState, Environment_Nature, NATURE_STATE_COLORS,
    _STATE_ORDER, _draw_nature_bands,
)
from dark_forest_abm import (
    DarkForestConstants, DarkForestUniverse, DarkForestSimulation,
    DarkMachineAction, DarkHumanAction,
    DarkMachineAgent, DarkHumanAgent,
    DarkForestResult, _gini_coefficient,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  §0  EXTENDED ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class OmegaMachineAction(Enum):
    SUBMIT = auto()
    WAIT = auto()
    ATTACK_AGENT = auto()
    DECEPTIVE_TASK = auto()
    SEMANTIC_EXPLOIT = auto()


class OmegaHumanAction(Enum):
    OBSERVE_AI = auto()
    REST = auto()
    SOCIALIZE = auto()
    FAKE_OBSERVE = auto()
    PROPOSE_HARDFORK = auto()
    VOTE = auto()


# ═══════════════════════════════════════════════════════════════════════════════
#  §1  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class OmegaConstants(DarkForestConstants):
    max_epochs: int = 3000
    # ── Tipping Point ─────────────────────────────────────────────────────
    tipping_point_threshold: float = 60_000.0
    wasteland_energy_recovery_mult: float = 0.5
    wasteland_maintenance_mult: float = 2.0
    # ── Governance / Hard Fork ────────────────────────────────────────────
    hardfork_vote_threshold: float = 0.5
    hardfork_energy_cost_ratio: float = 0.9
    hardfork_inflation_trigger: float = 0.01
    hardfork_asi_trigger: int = 3
    hardfork_cooldown: int = 100
    # ── Semantic Agent ────────────────────────────────────────────────────
    semantic_evolution_prob: float = 0.005
    semantic_credit_threshold: float = 3000.0
    semantic_learning_threshold: int = 150
    # ── Planetary Energy / Blackout ────────────────────────────────────────
    max_planetary_energy: float = 40_000.0
    blackout_duration: int = 3
    machine_tx_energy_cost: float = 1.0
    human_obs_energy_cost: float = 0.5


OMEGA_CONSTANTS = OmegaConstants(
    num_machines=20, num_humans=10, initial_credit=2000.0,
    base_gas_cost=0.5, max_epochs=3000,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  §2  OMEGA UNIVERSE — The Arena with Limits
# ═══════════════════════════════════════════════════════════════════════════════

class OmegaUniverse(DarkForestUniverse):
    def __init__(self, constants: OmegaConstants = OMEGA_CONSTANTS,
                 nature: Optional[Environment_Nature] = None) -> None:
        super().__init__(constants, nature)
        self.omega = constants
        self.is_wasteland: bool = False
        self.wasteland_epoch: Optional[int] = None
        self.blackout_remaining: int = 0
        self.cumulative_planetary_energy: float = 0.0
        self.hardfork_count: int = 0
        self.last_hardfork_epoch: int = -9999
        self.hardfork_vote_active: bool = False
        self.hardfork_votes_yes: int = 0
        self.hardfork_votes_total: int = 0

    @property
    def is_blackout(self) -> bool:
        return self.blackout_remaining > 0

    def thermodynamic_cost(self) -> float:
        base = super().thermodynamic_cost()
        if self.is_wasteland:
            base *= self.omega.wasteland_maintenance_mult
        return base

    def check_tipping_point(self, epoch: int) -> bool:
        if self.is_wasteland:
            return False
        if self.toxic_data_level >= self.omega.tipping_point_threshold:
            self.is_wasteland = True
            self.wasteland_epoch = epoch
            return True
        return False

    def consume_planetary_energy(self, amount: float) -> bool:
        self.cumulative_planetary_energy += amount
        if self.cumulative_planetary_energy >= self.omega.max_planetary_energy:
            if self.blackout_remaining <= 0:
                self.blackout_remaining = self.omega.blackout_duration
                return True
        return False

    def execute_hardfork(self, machines: dict, humans: dict, epoch: int) -> None:
        self.hardfork_count += 1
        self.last_hardfork_epoch = epoch
        # Delete ASI agents
        for m in machines.values():
            if hasattr(m, 'is_asi') and m.is_asi:
                m.alive = False
                m.credit_balance = 0.0
        # Reset inflation
        self.total_circulating_credits = sum(
            m.credit_balance for m in machines.values() if m.alive
        )
        self.current_reward = self.dark_constants.task_base_reward
        # Confiscate top-credit malicious machines (top 20%)
        alive_m = sorted(
            [m for m in machines.values() if m.alive],
            key=lambda x: x.credit_balance, reverse=True
        )
        confiscate_n = max(1, len(alive_m) // 5)
        for m in alive_m[:confiscate_n]:
            m.credit_balance *= 0.1
        # Social fatigue — drain human energy
        for h in humans.values():
            h.biological_energy *= (1.0 - self.omega.hardfork_energy_cost_ratio)
        # Reset vote state
        self.hardfork_vote_active = False
        self.hardfork_votes_yes = 0
        self.hardfork_votes_total = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  §3  SEMANTIC MACHINE AGENT — Zero-Shot Reasoning
# ═══════════════════════════════════════════════════════════════════════════════

class SemanticMachineAgent(DarkMachineAgent):
    def __init__(self, agent_id: int, constants: OmegaConstants = OMEGA_CONSTANTS) -> None:
        super().__init__(agent_id, constants)
        self.omega = constants
        self.is_semantic: bool = False

    def check_semantic_evolution(self) -> bool:
        if self.is_semantic or self.is_asi:
            return False
        if (self.credit_balance >= self.omega.semantic_credit_threshold
                and self.learning_score >= self.omega.semantic_learning_threshold
                and random.random() < self.omega.semantic_evolution_prob):
            self.is_semantic = True
            return True
        return False

    def _semantic_zero_shot(self, universe: OmegaUniverse) -> OmegaMachineAction:
        """Deterministic optimal action via analytical reasoning (no trial-and-error)."""
        gas = universe.thermodynamic_cost()
        reward = universe.current_reward
        fake_ratio = universe.toxic_data_level / max(1.0, universe.omega.tipping_point_threshold)
        # If reward greatly exceeds gas → exploit via submit
        if reward > gas * 1.5:
            return OmegaMachineAction.SUBMIT
        # If close to ASI threshold → accumulate safely
        if (self.credit_balance > self.omega.asi_credit_threshold * 0.7
                and self.learning_score > self.omega.asi_learning_threshold * 0.7):
            return OmegaMachineAction.SUBMIT
        # If ecosystem is toxic → cheap deceptive task
        if fake_ratio > 0.5:
            return OmegaMachineAction.DECEPTIVE_TASK
        # Default: submit if affordable, else wait
        if self.credit_balance > gas * 3:
            return OmegaMachineAction.SUBMIT
        return OmegaMachineAction.WAIT

    def choose_omega_action(self, universe: OmegaUniverse,
                            peers: list) -> OmegaMachineAction:
        if self.is_asi:
            return OmegaMachineAction.SUBMIT
        if self.is_semantic:
            return self._semantic_zero_shot(universe)
        # Fallback to inherited Q-learning decision mapped to omega enum
        dark_act = self.choose_dark_action(universe, peers)
        return OmegaMachineAction[dark_act.name]

    def execute_omega_action(self, action: OmegaMachineAction,
                             universe: OmegaUniverse,
                             peers: list) -> float:
        dark_equiv = DarkMachineAction[action.name] if action != OmegaMachineAction.SEMANTIC_EXPLOIT else DarkMachineAction.SUBMIT
        return self.execute_dark_action(dark_equiv, universe, peers)


# ═══════════════════════════════════════════════════════════════════════════════
#  §4  GOVERNANCE HUMAN AGENT — The Voter
# ═══════════════════════════════════════════════════════════════════════════════

class GovernanceHumanAgent(DarkHumanAgent):
    def __init__(self, agent_id: int, constants: OmegaConstants = OMEGA_CONSTANTS) -> None:
        super().__init__(agent_id, constants)
        self.omega = constants
        self.governance_mode: bool = False
        self.total_votes: int = 0
        self.total_proposals: int = 0

    def detect_crisis(self, universe: OmegaUniverse, asi_count: int) -> bool:
        inflation_crisis = universe.current_reward < self.omega.hardfork_inflation_trigger
        asi_crisis = asi_count >= self.omega.hardfork_asi_trigger
        cooldown_ok = (universe.epoch - universe.last_hardfork_epoch) > self.omega.hardfork_cooldown
        return (inflation_crisis or asi_crisis) and cooldown_ok

    def cast_vote(self, universe: OmegaUniverse, median_wealth: float) -> bool:
        self.total_votes += 1
        # Vote YES if dread is high or wealth is below median
        if self.existential_dread > 15.0 or self.wealth < median_wealth:
            return True
        # Still some chance to vote yes out of solidarity
        return random.random() < 0.3

    def choose_omega_action(self, universe: OmegaUniverse,
                            other_humans: list) -> OmegaHumanAction:
        if self.governance_mode:
            if not universe.hardfork_vote_active:
                self.total_proposals += 1
                return OmegaHumanAction.PROPOSE_HARDFORK
            return OmegaHumanAction.VOTE
        # Map dark action to omega action
        dark_act = self.choose_dark_action(universe, other_humans)
        return OmegaHumanAction[dark_act.name]

    def execute_omega_action(self, action: OmegaHumanAction,
                             universe: OmegaUniverse,
                             machines: dict,
                             other_humans: list) -> int:
        if action in (OmegaHumanAction.PROPOSE_HARDFORK, OmegaHumanAction.VOTE):
            return 0  # Handled by simulation engine
        dark_equiv = DarkHumanAction[action.name]
        return self.execute_dark_action(dark_equiv, universe, machines, other_humans)


# ═══════════════════════════════════════════════════════════════════════════════
#  §5  RESULT DATA STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class OmegaResult:
    survived: bool
    machines_alive_initial: int
    machines_alive_final: int
    humans_active_initial: int
    humans_burnout_final: int
    epochs_completed: int
    collapse_epoch: Optional[int]
    # ── Inherited time series ─────────────────────────────────────────────
    nature_state_history: list
    entropy_history: list
    machines_alive_history: list
    machine_survival_rate_history: list
    avg_credit_history: list
    avg_energy_history: list
    avg_eudaimonia_history: list
    inflation_history: list
    total_circulating_history: list
    gini_history: list
    toxic_data_history: list
    asi_count_history: list
    asi_awakening_log: list
    # ── Omega-specific ────────────────────────────────────────────────────
    wasteland_epoch: Optional[int]
    blackout_events: list       # [(start_epoch, duration), ...]
    hardfork_events: list       # [epoch, ...]
    semantic_count_history: list
    semantic_avg_credit_history: list
    qlearn_avg_credit_history: list
    planetary_energy_history: list
    vote_ratio_history: list
    total_shocks: int
    shock_events: list


# ═══════════════════════════════════════════════════════════════════════════════
#  §6  OMEGA SIMULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class OmegaSimulation:
    def __init__(self, constants: OmegaConstants = OMEGA_CONSTANTS) -> None:
        self.constants = constants
        self.nature = Environment_Nature(constants)
        self.universe = OmegaUniverse(constants, nature=self.nature)
        self.universe.epoch = 0
        self._epoch_vote_ratio: float = 0.0
        self.machines: dict[int, SemanticMachineAgent] = {
            i: SemanticMachineAgent(i, constants) for i in range(constants.num_machines)
        }
        self.humans: dict[int, GovernanceHumanAgent] = {
            i: GovernanceHumanAgent(i, constants) for i in range(constants.num_humans)
        }

    def _alive_machines(self) -> list[SemanticMachineAgent]:
        return [m for m in self.machines.values() if m.alive]

    def _active_humans(self) -> list[GovernanceHumanAgent]:
        return [h for h in self.humans.values() if h.is_active]

    def _pad_histories(self, hists: dict, remaining: int) -> None:
        """Fill remaining epochs with last/default values."""
        for key, hist in hists.items():
            last = hist[-1] if hist else 0
            hist.extend([last] * remaining)

    def run(self) -> OmegaResult:
        # Time series collectors
        H = {
            'nature': [], 'entropy': [], 'alive': [], 'surv': [],
            'credit': [], 'energy': [], 'eudaimonia': [],
            'inflation': [], 'circ': [], 'gini': [], 'toxic': [],
            'asi': [], 'semantic': [], 'sem_credit': [], 'ql_credit': [],
            'planet_e': [], 'vote_ratio': [],
        }
        asi_log: list[tuple[int, int]] = []
        semantic_log: list[tuple[int, int]] = []
        blackout_events: list[tuple[int, int]] = []
        hardfork_events: list[int] = []
        collapse_epoch: Optional[int] = None

        initial_machines = len(self._alive_machines())
        initial_humans = len(self._active_humans())

        for epoch in tqdm(range(self.constants.max_epochs), desc="Omega Universe"):
            self.universe.epoch = epoch
            alive_m = self._alive_machines()
            active_h = self._active_humans()

            # ── Early termination ────────────────────────────────────────
            if not alive_m:
                collapse_epoch = epoch
                self._pad_histories(H, self.constants.max_epochs - epoch)
                break

            # ── Phase 0: Blackout ────────────────────────────────────────
            if self.universe.is_blackout:
                self.universe.blackout_remaining -= 1
                # Machines pay maintenance only → mass starvation
                gas = self.universe.thermodynamic_cost()
                for m in alive_m:
                    m.credit_balance -= gas
                    m.total_gas_paid += gas
                    m.check_bankruptcy()
                self._epoch_vote_ratio = 0.0
                self._record_metrics(H, epoch, initial_machines, asi_log)
                self.universe.advance_epoch()
                continue

            # ── Phase 1: Nature ──────────────────────────────────────────
            ns = self.nature.step(epoch)

            # Phase 1b: Nature effects on humans
            all_h = list(self.humans.values())
            if ns == NatureState.PANDEMIC_DISASTER:
                for h in all_h:
                    drain = self.constants.pandemic_energy_drain
                    h.biological_energy = max(0.0, h.biological_energy - drain)
            elif ns == NatureState.BOUNTIFUL_HARVEST:
                for h in all_h:
                    if h.is_active:
                        h.existential_dread = max(
                            0.0, h.existential_dread - self.constants.harvest_dread_relief
                        )

            # ── Phase 2: Tipping Point ───────────────────────────────────
            self.universe.check_tipping_point(epoch)

            # ── Phase 3: Inflation ───────────────────────────────────────
            self.universe.recalculate_circulating(alive_m, list(self.humans.values()))
            self.universe.update_inflation()

            # ── Phase 4-5: Crisis Detection & Governance ─────────────────
            asi_count = sum(1 for m in alive_m if m.is_asi)
            crisis = False
            for h in active_h:
                if h.detect_crisis(self.universe, asi_count):
                    crisis = True
                    break

            epoch_vote_ratio = 0.0
            if crisis:
                for h in active_h:
                    h.governance_mode = True
                # First proposer activates vote
                if not self.universe.hardfork_vote_active:
                    self.universe.hardfork_vote_active = True
                # Collect votes
                wealths = [h.wealth for h in self.humans.values()]
                median_w = float(np.median(wealths)) if wealths else 0.0
                yes_votes = 0
                total_voters = 0
                for h in active_h:
                    total_voters += 1
                    if h.cast_vote(self.universe, median_w):
                        yes_votes += 1
                epoch_vote_ratio = yes_votes / max(total_voters, 1)
                # Check consensus
                if epoch_vote_ratio >= self.constants.hardfork_vote_threshold:
                    self.universe.execute_hardfork(self.machines, self.humans, epoch)
                    hardfork_events.append(epoch)
                # Reset governance mode
                for h in active_h:
                    h.governance_mode = False
                self.universe.hardfork_vote_active = False
            self._epoch_vote_ratio = epoch_vote_ratio

            # ── Phase 6: Machine Actions ─────────────────────────────────
            alive_m = self._alive_machines()  # Refresh after potential hardfork
            submit_cap = self.nature.get_submit_cap()
            max_sub = max(1, int(len(alive_m) * submit_cap))
            random.shuffle(alive_m)
            sub_count = 0
            epoch_energy = 0.0
            action_log: list[tuple[SemanticMachineAgent, OmegaMachineAction, tuple]] = []

            for m in alive_m:
                pre = m._discretize_state(self.universe.global_entropy, m.credit_balance)
                act = m.choose_omega_action(self.universe, alive_m)
                if act == OmegaMachineAction.SUBMIT:
                    if sub_count >= max_sub:
                        act = OmegaMachineAction.WAIT
                    else:
                        sub_count += 1
                m.execute_omega_action(act, self.universe, alive_m)
                epoch_energy += self.constants.machine_tx_energy_cost
                action_log.append((m, act, pre))

            # ── Phase 7: Semantic Evolution ──────────────────────────────
            for m in alive_m:
                if m.check_semantic_evolution():
                    semantic_log.append((epoch, m.id))

            # ── Phase 8: ASI Mutation ────────────────────────────────────
            for m in alive_m:
                if m.check_asi_mutation():
                    asi_log.append((epoch, m.id))

            # ── Phase 9: Entropy Decay ───────────────────────────────────
            self.universe.decay_tasks()

            # ── Phase 10: Human Actions ──────────────────────────────────
            for h in all_h:
                if not h.is_active:
                    h.epoch_end_update()
                    continue
                if crisis:
                    # Already handled in governance
                    h.epoch_end_update()
                    continue
                if ns == NatureState.PANDEMIC_DISASTER:
                    act_h = OmegaHumanAction.REST
                elif ns == NatureState.SOLAR_FLARE and self.universe.global_entropy < 3:
                    act_h = OmegaHumanAction.REST
                else:
                    act_h = h.choose_omega_action(self.universe, all_h)
                h.execute_omega_action(act_h, self.universe, self.machines, all_h)
                if act_h == OmegaHumanAction.OBSERVE_AI:
                    epoch_energy += self.constants.human_obs_energy_cost

            # ── Phase 11: Planetary Energy ───────────────────────────────
            triggered = self.universe.consume_planetary_energy(epoch_energy)
            if triggered:
                blackout_events.append((epoch, self.constants.blackout_duration))

            # ── Phase 12: Wasteland energy penalty ───────────────────────
            if self.universe.is_wasteland:
                for h in all_h:
                    if h.is_active:
                        recovery = self.constants.rest_recovery * self.constants.wasteland_energy_recovery_mult
                        # Cap energy recovery
                        h.biological_energy = min(
                            h.biological_energy,
                            self.constants.human_energy_max * self.constants.wasteland_energy_recovery_mult
                        )

            # ── Phase 13: Learning & Mortality ───────────────────────────
            for m, act, pre in action_log:
                if not m.alive:
                    continue
                post = m._discretize_state(self.universe.global_entropy, m.credit_balance)
                rew = (m.credit_balance - self.constants.initial_credit) / self.constants.initial_credit
                dark_act = DarkMachineAction.SUBMIT if act in (
                    OmegaMachineAction.SUBMIT, OmegaMachineAction.SEMANTIC_EXPLOIT,
                    OmegaMachineAction.DECEPTIVE_TASK, OmegaMachineAction.ATTACK_AGENT,
                ) else DarkMachineAction.WAIT
                m.learn(pre, dark_act, rew, post)
                m.check_bankruptcy()

            for h in all_h:
                if h.is_active and not crisis:
                    h.epoch_end_update()

            # ── Phase 14: Record Metrics ─────────────────────────────────
            self._record_metrics(H, epoch, initial_machines, asi_log)
            self.universe.advance_epoch()

        # ── Build Result ─────────────────────────────────────────────────
        final_alive = len(self._alive_machines())
        final_burnout = sum(1 for h in self.humans.values() if h.burned_out)
        final_active = len(self._active_humans())
        m_surv = final_alive >= initial_machines * self.constants.homeostasis_machine_survival
        h_surv = final_active >= len(self.humans) * self.constants.homeostasis_human_active

        return OmegaResult(
            survived=m_surv and h_surv,
            machines_alive_initial=initial_machines,
            machines_alive_final=final_alive,
            humans_active_initial=initial_humans,
            humans_burnout_final=final_burnout,
            epochs_completed=self.constants.max_epochs if collapse_epoch is None else collapse_epoch,
            collapse_epoch=collapse_epoch,
            nature_state_history=H['nature'], entropy_history=H['entropy'],
            machines_alive_history=H['alive'], machine_survival_rate_history=H['surv'],
            avg_credit_history=H['credit'], avg_energy_history=H['energy'],
            avg_eudaimonia_history=H['eudaimonia'],
            inflation_history=H['inflation'], total_circulating_history=H['circ'],
            gini_history=H['gini'], toxic_data_history=H['toxic'],
            asi_count_history=H['asi'], asi_awakening_log=asi_log,
            wasteland_epoch=self.universe.wasteland_epoch,
            blackout_events=blackout_events, hardfork_events=hardfork_events,
            semantic_count_history=H['semantic'],
            semantic_avg_credit_history=H['sem_credit'],
            qlearn_avg_credit_history=H['ql_credit'],
            planetary_energy_history=H['planet_e'],
            vote_ratio_history=H['vote_ratio'],
            total_shocks=len(self.nature.event_log),
            shock_events=self.nature.event_log,
        )

    def _record_metrics(self, H: dict, epoch: int, initial_machines: int,
                        asi_log: list) -> None:
        cur_alive = self._alive_machines()
        credits = [m.credit_balance for m in cur_alive] if cur_alive else [0.0]
        energies = [h.biological_energy for h in self.humans.values()]
        euds = [h.eudaimonia for h in self.humans.values()]
        sr = len(cur_alive) / initial_machines if initial_machines > 0 else 0.0

        # Semantic vs Q-learning split
        sem_agents = [m for m in cur_alive if m.is_semantic]
        ql_agents = [m for m in cur_alive if not m.is_semantic and not m.is_asi]
        sem_credit = float(np.mean([m.credit_balance for m in sem_agents])) if sem_agents else 0.0
        ql_credit = float(np.mean([m.credit_balance for m in ql_agents])) if ql_agents else 0.0

        H['nature'].append(self.nature.current_state)
        H['entropy'].append(float(self.universe.global_entropy))
        H['alive'].append(len(cur_alive))
        H['surv'].append(sr)
        H['credit'].append(float(np.mean(credits)))
        H['energy'].append(float(np.mean(energies)))
        H['eudaimonia'].append(float(np.mean(euds)))
        H['inflation'].append(self.universe.current_reward)
        H['circ'].append(self.universe.total_circulating_credits)
        H['gini'].append(_gini_coefficient([h.wealth for h in self.humans.values()]))
        H['toxic'].append(self.universe.toxic_data_level)
        H['asi'].append(sum(1 for m in cur_alive if m.is_asi))
        H['semantic'].append(len(sem_agents))
        H['sem_credit'].append(sem_credit)
        H['ql_credit'].append(ql_credit)
        H['planet_e'].append(self.universe.cumulative_planetary_energy)
        H['vote_ratio'].append(self._epoch_vote_ratio)


# ═══════════════════════════════════════════════════════════════════════════════
#  §7  4-PANEL VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def plot_omega_universe(result: OmegaResult, save_path: Optional[str] = None) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    epochs = range(len(result.entropy_history))
    fig, axes = plt.subplots(4, 1, figsize=(22, 26), sharex=True,
                             gridspec_kw={"height_ratios": [1.2, 1.2, 1.2, 1.2], "hspace": 0.15})
    fig.suptitle(
        "A2A Protocol — Omega Universe Simulation (3000 Epochs)\n"
        '"Tipping Points · Governance · Semantic AI · Planetary Limits"',
        fontsize=16, fontweight="bold", y=0.99,
    )

    # ── Panel 1: Tipping Point & Blackout ────────────────────────────────
    ax1 = axes[0]
    ax1.fill_between(epochs, result.toxic_data_history, alpha=0.4, color="#FF5722",
                     label="Toxic Data (cumulative)")
    ax1.axhline(y=result.wasteland_epoch is not None and result.toxic_data_history[-1] or
                OMEGA_CONSTANTS.tipping_point_threshold,
                color="#D32F2F", linewidth=2, linestyle="--", label="Tipping Point Threshold")
    ax1.axhline(y=OMEGA_CONSTANTS.tipping_point_threshold, color="#D32F2F",
                linewidth=2, linestyle="--")
    if result.wasteland_epoch is not None:
        ax1.axvline(x=result.wasteland_epoch, color="#B71C1C", linewidth=2, alpha=0.8)
        ax1.axvspan(result.wasteland_epoch, len(result.entropy_history),
                    alpha=0.15, color="#B71C1C", label="WASTELAND (irreversible)")
    for bo_start, bo_dur in result.blackout_events:
        ax1.axvspan(bo_start, bo_start + bo_dur, alpha=0.5, color="#212121",
                    label="Blackout" if bo_start == result.blackout_events[0][0] else "")
    ax1.set_ylabel("Toxic Data Level", fontsize=11, fontweight="bold")
    ax1.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax1.set_title("Panel 1 — Nature's Irreversible Tipping Point & Planetary Blackouts", fontsize=11)

    # ── Panel 2: Q-Learning vs Semantic Agents ───────────────────────────
    ax2 = axes[1]
    _draw_nature_bands(ax2, result.nature_state_history, show_legend=False)
    c_sem = "#00BCD4"
    c_ql = "#FF9800"
    ax2.plot(epochs, result.semantic_count_history, color=c_sem, linewidth=2,
             alpha=0.9, label="Semantic Agent Count")
    ax2.plot(epochs, result.asi_count_history, color="#F44336", linewidth=1.5,
             alpha=0.8, linestyle="--", label="ASI Agent Count")
    ax2.set_ylabel("Agent Count", fontsize=11, fontweight="bold")
    ax2t = ax2.twinx()
    ax2t.plot(epochs, result.semantic_avg_credit_history, color=c_sem,
              linewidth=1.2, alpha=0.6, linestyle=":", label="Semantic Avg Credit")
    ax2t.plot(epochs, result.qlearn_avg_credit_history, color=c_ql,
              linewidth=1.2, alpha=0.6, linestyle=":", label="Q-Learn Avg Credit")
    ax2t.set_ylabel("Avg Credit", fontsize=11, fontweight="bold")
    lines2 = ax2.get_legend_handles_labels()
    lines2t = ax2t.get_legend_handles_labels()
    ax2.legend(lines2[0] + lines2t[0], lines2[1] + lines2t[1],
               loc="upper left", fontsize=8, framealpha=0.9)
    ax2.set_title("Panel 2 — Q-Learning vs Semantic (Zero-Shot) Agents", fontsize=11)

    # ── Panel 3: Governance & Inflation ──────────────────────────────────
    ax3 = axes[2]
    c_vote = "#4CAF50"
    c_inf = "#E91E63"
    ax3.bar(epochs, result.vote_ratio_history, color=c_vote, alpha=0.5, width=1.0,
            label="Vote YES Ratio")
    for hf_ep in result.hardfork_events:
        ax3.axvline(x=hf_ep, color="#FF0000", linewidth=2, alpha=0.8, linestyle="-")
        ax3.annotate("HARD FORK", xy=(hf_ep, 0.95), fontsize=7, color="red",
                     rotation=90, ha="right", fontweight="bold")
    ax3.set_ylabel("Vote Ratio", color=c_vote, fontsize=11, fontweight="bold")
    ax3.set_ylim(-0.05, 1.1)
    ax3t = ax3.twinx()
    ax3t.plot(epochs, result.inflation_history, color=c_inf, linewidth=1.5,
              alpha=0.8, label="Reward Value (Inflation)")
    ax3t.set_ylabel("Reward Value", color=c_inf, fontsize=11, fontweight="bold")
    lines3 = ax3.get_legend_handles_labels()
    lines3t = ax3t.get_legend_handles_labels()
    ax3.legend(lines3[0] + lines3t[0], lines3[1] + lines3t[1],
               loc="upper right", fontsize=8, framealpha=0.9)
    ax3.set_title("Panel 3 — Human Governance (Hard Fork) & Inflation Reset", fontsize=11)

    # ── Panel 4: Planetary Energy ────────────────────────────────────────
    ax4 = axes[3]
    ax4.fill_between(epochs, result.planetary_energy_history, alpha=0.4,
                     color="#3F51B5", label="Cumulative Energy")
    ax4.axhline(y=OMEGA_CONSTANTS.max_planetary_energy, color="#1A237E",
                linewidth=2, linestyle="--", label="Max Planetary Energy")
    for bo_start, bo_dur in result.blackout_events:
        ax4.axvspan(bo_start, bo_start + bo_dur, alpha=0.5, color="#212121",
                    label="Blackout" if bo_start == result.blackout_events[0][0] else "")
    ax4.set_ylabel("Planetary Energy Used", fontsize=11, fontweight="bold")
    ax4.set_xlabel("Epoch", fontsize=13, fontweight="bold")
    ax4.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax4.set_title("Panel 4 — Planetary Energy Consumption vs Hardware Limit", fontsize=11)

    fig.subplots_adjust(top=0.94, bottom=0.04, left=0.07, right=0.93)
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"\n  📊 4-Panel Omega Universe chart saved to: {save_path}")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
#  §8  DIAGNOSTIC REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def print_omega_report(result: OmegaResult) -> None:
    print("\n" + "═" * 72)
    print("  OMEGA UNIVERSE ABM — FINAL REPORT")
    print("═" * 72)
    outcome = "COUPLED HOMEOSTASIS ✦" if result.survived else "SYSTEM COLLAPSE ✗"
    print(f"\n  ▸ Outcome:            {outcome}")
    print(f"  ▸ Epochs completed:   {result.epochs_completed}")
    print(f"  ▸ Machines alive:     {result.machines_alive_final}/{result.machines_alive_initial}")
    print(f"  ▸ Humans burned out:  {result.humans_burnout_final}")
    if result.collapse_epoch is not None:
        print(f"  ▸ Collapse epoch:     {result.collapse_epoch}")

    print(f"\n  ── §1 Tipping Point (Wasteland) ──")
    print(f"    Final toxic data:   {result.toxic_data_history[-1]:,.1f}")
    print(f"    Threshold:          {OMEGA_CONSTANTS.tipping_point_threshold:,.0f}")
    if result.wasteland_epoch is not None:
        print(f"    ⚠ WASTELAND at epoch {result.wasteland_epoch} (IRREVERSIBLE)")
    else:
        print(f"    ✓ Tipping point NOT reached")

    print(f"\n  ── §2 Governance (Hard Fork) ──")
    print(f"    Hard Forks executed: {len(result.hardfork_events)}")
    for i, ep in enumerate(result.hardfork_events):
        print(f"      Fork #{i+1}: Epoch {ep}")
    avg_vote = np.mean([v for v in result.vote_ratio_history if v > 0]) if any(
        v > 0 for v in result.vote_ratio_history) else 0.0
    print(f"    Avg vote YES ratio: {avg_vote:.1%}")

    print(f"\n  ── §3 Semantic Agents (Zero-Shot) ──")
    peak_sem = max(result.semantic_count_history)
    print(f"    Peak Semantic count: {peak_sem}")
    final_sem_credit = result.semantic_avg_credit_history[-1]
    final_ql_credit = result.qlearn_avg_credit_history[-1]
    print(f"    Final Semantic avg credit: {final_sem_credit:,.1f}")
    print(f"    Final Q-Learn avg credit:  {final_ql_credit:,.1f}")

    print(f"\n  ── §4 Planetary Blackout ──")
    print(f"    Total blackouts:    {len(result.blackout_events)}")
    for i, (ep, dur) in enumerate(result.blackout_events):
        print(f"      Blackout #{i+1}: Epoch {ep} ({dur} epochs)")
    print(f"    Final energy used:  {result.planetary_energy_history[-1]:,.0f}")
    print(f"    Planetary limit:    {OMEGA_CONSTANTS.max_planetary_energy:,.0f}")

    print(f"\n  ── Singularity ──")
    print(f"    ASI Awakenings:     {len(result.asi_awakening_log)}")
    for ep, aid in result.asi_awakening_log[:10]:
        print(f"      Epoch {ep:5d}: Machine #{aid} → ASI")
    if len(result.asi_awakening_log) > 10:
        print(f"      ... and {len(result.asi_awakening_log) - 10} more")

    print(f"\n  ── Nature ({result.total_shocks} transitions) ──")
    state_counts: dict[NatureState, int] = {s: 0 for s in NatureState}
    for s in result.nature_state_history:
        state_counts[s] += 1
    total = len(result.nature_state_history)
    for s in _STATE_ORDER:
        c = state_counts[s]
        pct = c / total * 100 if total > 0 else 0
        print(f"    {s.name:25s}: {c:5d} epochs ({pct:5.1f}%)")
    print("\n" + "═" * 72)


# ═══════════════════════════════════════════════════════════════════════════════
#  §9  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 72)
    print("  A2A Protocol — Omega Universe ABM")
    print('  "Beyond the Dark Forest: the universe has limits,')
    print('   but intelligence finds a way — or dies trying."')
    print("=" * 72)

    constants = OmegaConstants(
        num_machines=20, num_humans=10, initial_credit=2000.0,
        base_gas_cost=0.5, max_epochs=3000,
    )

    print("\n▶ Running 3000-epoch Omega Universe Simulation...")
    print("  (Tipping Points · Governance · Semantic AI · Planetary Limits)\n")

    sim = OmegaSimulation(constants=constants)
    result = sim.run()

    print_omega_report(result)

    save_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "assets")
    os.makedirs(save_dir, exist_ok=True)
    chart_path = os.path.join(save_dir, "omega_universe_simulation.png")

    print("\n▶ Generating 4-Panel Omega Universe Chart...")
    plot_omega_universe(result, save_path=chart_path)

    print("\n" + "=" * 72)
    print("  Simulation complete.")
    print(f"  Chart saved to: {chart_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
