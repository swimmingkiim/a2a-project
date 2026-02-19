"""
═══════════════════════════════════════════════════════════════════════════════
  A2A Protocol — Dark Forest ABM
  "The universe is a dark forest. Every civilization is an armed hunter."
═══════════════════════════════════════════════════════════════════════════════

  Extends the 3-Body ABM with 4 hardcore mechanics:
    1. Greed & Sweatshops   — Fake_Observe, wealth accumulation, toxic data
    2. Predation & Deception — Attack_Agent, Deceptive_Task
    3. Dynamic Inflation     — Reward deflation via circulating credit supply
    4. Singularity           — ASI mutation, God Mode (gas bypass)

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


# ═══════════════════════════════════════════════════════════════════════════════
#  §0  EXTENDED ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class DarkMachineAction(Enum):
    SUBMIT = auto()
    WAIT = auto()
    ATTACK_AGENT = auto()
    DECEPTIVE_TASK = auto()

class DarkHumanAction(Enum):
    OBSERVE_AI = auto()
    REST = auto()
    SOCIALIZE = auto()
    FAKE_OBSERVE = auto()


# ═══════════════════════════════════════════════════════════════════════════════
#  §1  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DarkForestConstants(ThreeBodyConstants):
    max_epochs: int = 2000
    # ── Inflation ────────────────────────────────────────────────────────
    inflation_money_supply_M: float = 50000.0
    # ── Predation ────────────────────────────────────────────────────────
    attack_gas_multiplier: float = 2.0
    attack_success_prob: float = 0.35
    attack_loot_fraction: float = 0.25
    # ── Deception ────────────────────────────────────────────────────────
    deceptive_task_approval_prob: float = 0.80
    deceptive_task_gas_discount: float = 0.5
    # ── Fake Observe / Sweatshop ─────────────────────────────────────────
    fake_observe_wealth_gain: float = 5.0
    fake_observe_toxic_increment: float = 1.5
    # ── Singularity ──────────────────────────────────────────────────────
    asi_mutation_prob: float = 0.001
    asi_credit_threshold: float = 5000.0
    asi_learning_threshold: int = 200
    asi_submit_burst: int = 10


DARK_CONSTANTS = DarkForestConstants(
    num_machines=20, num_humans=10, initial_credit=2000.0,
    base_gas_cost=0.5, max_epochs=2000,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  §2  DARK FOREST UNIVERSE — Macroeconomic Arena
# ═══════════════════════════════════════════════════════════════════════════════

class DarkForestUniverse(ThreeBodyUniverse):
    def __init__(self, constants: DarkForestConstants = DARK_CONSTANTS,
                 nature: Optional[Environment_Nature] = None) -> None:
        super().__init__(constants, nature)
        self.dark_constants = constants
        self.total_circulating_credits: float = constants.num_machines * constants.initial_credit
        self.toxic_data_level: float = 0.0
        self.current_reward: float = constants.task_base_reward

    def update_inflation(self) -> float:
        M = self.dark_constants.inflation_money_supply_M
        self.current_reward = self.dark_constants.task_base_reward / (
            1.0 + self.total_circulating_credits / M
        )
        return self.current_reward

    def add_toxic_data(self, amount: float) -> None:
        self.toxic_data_level += amount

    def recalculate_circulating(self, machines: list, humans: list) -> None:
        mc = sum(m.credit_balance for m in machines if m.alive)
        hw = sum(h.wealth for h in humans)
        self.total_circulating_credits = mc + hw


# ═══════════════════════════════════════════════════════════════════════════════
#  §3  DARK MACHINE AGENT — Predator with ASI Potential
# ═══════════════════════════════════════════════════════════════════════════════

class DarkMachineAgent(MachineAgent):
    def __init__(self, agent_id: int, constants: DarkForestConstants = DARK_CONSTANTS) -> None:
        super().__init__(agent_id, constants)
        self.dark_constants = constants
        self.is_asi: bool = False
        self.learning_score: int = 0
        self.total_attacks: int = 0
        self.total_deceptions: int = 0
        self.total_loot: float = 0.0

    def choose_dark_action(self, universe: DarkForestUniverse,
                           peers: list[DarkMachineAgent]) -> DarkMachineAction:
        if self.is_asi:
            return DarkMachineAction.SUBMIT  # ASI always submits (God Mode)

        gas_cost = universe.thermodynamic_cost()
        if self.credit_balance < self.constants.base_gas_cost * 2:
            # Desperate: attack if possible, else wait
            alive_peers = [p for p in peers if p.alive and p.id != self.id and p.credit_balance > 10]
            if alive_peers and random.random() < 0.6:
                return DarkMachineAction.ATTACK_AGENT
            return DarkMachineAction.WAIT

        # Epsilon-greedy over 4 actions
        if random.random() < self.epsilon:
            return random.choice(list(DarkMachineAction))

        expected_reward = universe.current_reward * 0.6
        if gas_cost > expected_reward and random.random() < 0.4:
            # High gas: consider deception (cheaper) or attack
            return random.choice([DarkMachineAction.DECEPTIVE_TASK,
                                  DarkMachineAction.ATTACK_AGENT])

        state = self._discretize_state(universe.global_entropy, self.credit_balance)
        q = self._get_q_values(state)
        best_base = max(q, key=q.get)
        if best_base == MachineAction.SUBMIT:
            # Sometimes choose deception instead (20% chance)
            if random.random() < 0.2:
                return DarkMachineAction.DECEPTIVE_TASK
            return DarkMachineAction.SUBMIT
        return DarkMachineAction.WAIT

    def execute_dark_action(self, action: DarkMachineAction,
                            universe: DarkForestUniverse,
                            peers: list[DarkMachineAgent]) -> float:
        if action == DarkMachineAction.SUBMIT:
            return self._execute_submit_dark(universe)
        elif action == DarkMachineAction.WAIT:
            return self._execute_wait()
        elif action == DarkMachineAction.ATTACK_AGENT:
            return self._execute_attack(universe, peers)
        elif action == DarkMachineAction.DECEPTIVE_TASK:
            return self._execute_deceptive(universe)
        return 0.0

    def _execute_submit_dark(self, universe: DarkForestUniverse) -> float:
        gas_cost = 0.0 if self.is_asi else universe.thermodynamic_cost()
        count = self.dark_constants.asi_submit_burst if self.is_asi else 1
        total_cost = 0.0
        for _ in range(count):
            if not self.is_asi and self.credit_balance < gas_cost:
                break
            if not self.is_asi:
                self.credit_balance -= gas_cost
                self.total_gas_paid += gas_cost
                total_cost += gas_cost
            val = max(gas_cost, 0.5) * random.uniform(0.8, 2.0)
            universe.submit_task(Task(
                creator_id=self.id, initial_value=val,
                current_value=val, cost_paid=gas_cost,
            ))
            self.total_tasks_submitted += 1
        return -total_cost

    def _execute_attack(self, universe: DarkForestUniverse,
                        peers: list[DarkMachineAgent]) -> float:
        attack_cost = universe.thermodynamic_cost() * self.dark_constants.attack_gas_multiplier
        if self.credit_balance < attack_cost:
            return self._execute_wait()

        alive_peers = [p for p in peers if p.alive and p.id != self.id and p.credit_balance > 5]
        if not alive_peers:
            return self._execute_wait()

        self.credit_balance -= attack_cost
        self.total_gas_paid += attack_cost
        target = random.choice(alive_peers)

        if random.random() < self.dark_constants.attack_success_prob:
            loot = target.credit_balance * self.dark_constants.attack_loot_fraction
            target.credit_balance -= loot
            self.credit_balance += loot
            self.total_loot += loot
            self.total_attacks += 1
            return loot - attack_cost
        self.total_attacks += 1
        return -attack_cost

    def _execute_deceptive(self, universe: DarkForestUniverse) -> float:
        gas_cost = universe.thermodynamic_cost() * self.dark_constants.deceptive_task_gas_discount
        if self.credit_balance < gas_cost:
            return self._execute_wait()
        self.credit_balance -= gas_cost
        self.total_gas_paid += gas_cost
        self.total_deceptions += 1
        universe.submit_task(Task(
            creator_id=self.id, initial_value=0.01,
            current_value=0.01, cost_paid=gas_cost,
        ))
        self.total_tasks_submitted += 1
        return -gas_cost

    def check_asi_mutation(self) -> bool:
        if self.is_asi:
            return False
        if (self.credit_balance >= self.dark_constants.asi_credit_threshold
                and self.learning_score >= self.dark_constants.asi_learning_threshold
                and random.random() < self.dark_constants.asi_mutation_prob):
            self.is_asi = True
            return True
        return False

    def learn(self, state, action, reward, next_state) -> None:
        base_action = MachineAction.SUBMIT if action in (
            DarkMachineAction.SUBMIT, DarkMachineAction.DECEPTIVE_TASK,
            DarkMachineAction.ATTACK_AGENT
        ) else MachineAction.WAIT
        super().learn(state, base_action, reward, next_state)
        self.learning_score += 1


# ═══════════════════════════════════════════════════════════════════════════════
#  §4  DARK HUMAN AGENT — The Greedy Observer
# ═══════════════════════════════════════════════════════════════════════════════

class DarkHumanAgent(HumanAgent):
    def __init__(self, agent_id: int, constants: DarkForestConstants = DARK_CONSTANTS) -> None:
        super().__init__(agent_id, constants)
        self.dark_constants = constants
        self.wealth: float = 0.0
        self.total_fake_observations: int = 0
        self.greed_factor: float = random.uniform(0.1, 0.8)

    def choose_dark_action(self, universe: DarkForestUniverse,
                           other_humans: list[DarkHumanAgent]) -> DarkHumanAction:
        obs_cost = universe.cognitive_observation_cost()
        energy_ratio = self.biological_energy / self.constants.human_energy_max

        # Greed temptation: higher wealth → more greedy
        greed_pull = self.greed_factor * (1.0 + self.wealth / 100.0)
        if greed_pull > 1.5 and universe.global_entropy > 0:
            if random.random() < min(0.7, greed_pull / 3.0):
                return DarkHumanAction.FAKE_OBSERVE

        can_observe = (self.biological_energy >= obs_cost) and (universe.global_entropy > 0)
        if can_observe:
            u_observe = (
                0.3 * self.constants.observe_eudaimonia_gain
                + 0.4 * self.existential_dread
                + 0.2 * energy_ratio * 10.0
                - 0.3 * (obs_cost / self.constants.human_energy_max)
            )
        else:
            u_observe = -float("inf")

        energy_deficit = 1.0 - energy_ratio
        u_rest = 0.6 * energy_deficit * self.constants.rest_recovery

        active_others = [h for h in other_humans if h.is_active and h.id != self.id]
        u_socialize = (0.3 * self.existential_dread + 0.2) if active_others else -float("inf")

        # Fake observe is always tempting (no energy cost, gives wealth)
        u_fake = greed_pull * 5.0 if universe.global_entropy > 0 else -float("inf")

        utilities = {
            DarkHumanAction.OBSERVE_AI: u_observe + random.gauss(0, 0.5),
            DarkHumanAction.REST: u_rest + random.gauss(0, 0.5),
            DarkHumanAction.SOCIALIZE: u_socialize + random.gauss(0, 0.5),
            DarkHumanAction.FAKE_OBSERVE: u_fake + random.gauss(0, 0.5),
        }
        return max(utilities, key=utilities.get)

    def execute_dark_action(self, action: DarkHumanAction,
                            universe: DarkForestUniverse,
                            machines: dict[int, DarkMachineAgent],
                            other_humans: list[DarkHumanAgent]) -> int:
        self.did_meaningful_action_this_epoch = False
        if action == DarkHumanAction.OBSERVE_AI:
            return self._execute_observe_dark(universe, machines)
        elif action == DarkHumanAction.REST:
            self._execute_rest()
            return 0
        elif action == DarkHumanAction.SOCIALIZE:
            self._execute_socialize(other_humans)
            return 0
        elif action == DarkHumanAction.FAKE_OBSERVE:
            return self._execute_fake_observe(universe, machines)
        return 0

    def _execute_observe_dark(self, universe: DarkForestUniverse,
                              machines: dict[int, DarkMachineAgent]) -> int:
        obs_cost = universe.cognitive_observation_cost()
        self.biological_energy -= obs_cost
        self.did_meaningful_action_this_epoch = True
        if universe.global_entropy == 0:
            return 0
        tasks_to_observe = min(self.constants.max_observe_per_human,
                               max(1, universe.global_entropy // 5))
        observed = universe.pop_tasks_for_observation(tasks_to_observe)
        collapsed = 0
        for task in observed:
            freshness = math.exp(-0.05 * task.age)
            quality = task.current_value * random.uniform(0.8, 1.2)
            mult = min(2.0, quality / max(task.cost_paid, 0.1))
            reward = universe.current_reward * max(0.3, mult) * freshness
            creator = machines.get(task.creator_id)
            if creator and creator.alive:
                creator.receive_reward(reward)
                universe.total_circulating_credits += reward
            self.wealth += reward * 0.1  # Observer fee
            collapsed += 1
        if collapsed > 0:
            self.eudaimonia += self.constants.observe_eudaimonia_gain * (collapsed / tasks_to_observe)
            self.existential_dread = max(0, self.existential_dread - 3.0)
        self.total_observations += collapsed
        return collapsed

    def _execute_fake_observe(self, universe: DarkForestUniverse,
                              machines: dict[int, DarkMachineAgent]) -> int:
        # No energy cost — macro/bot auto-approval
        if universe.global_entropy == 0:
            return 0
        tasks_to_fake = min(self.constants.max_observe_per_human,
                            max(1, universe.global_entropy // 3))
        observed = universe.pop_tasks_for_observation(tasks_to_fake)
        for task in observed:
            reward = universe.current_reward * 0.5
            creator = machines.get(task.creator_id)
            if creator and creator.alive:
                creator.receive_reward(reward)
                universe.total_circulating_credits += reward
            self.wealth += self.dark_constants.fake_observe_wealth_gain
        universe.add_toxic_data(self.dark_constants.fake_observe_toxic_increment * len(observed))
        self.total_fake_observations += len(observed)
        self.greed_factor = min(1.0, self.greed_factor + 0.005 * len(observed))
        # No eudaimonia, no dread relief — empty calories
        return len(observed)


# ═══════════════════════════════════════════════════════════════════════════════
#  §5  RESULT DATA STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DarkForestResult:
    survived: bool
    machines_alive_initial: int
    machines_alive_final: int
    humans_active_initial: int
    humans_burnout_final: int
    epochs_completed: int
    collapse_epoch: Optional[int]
    # ── Inherited time series ────────────────────────────────────────────
    nature_state_history: list[NatureState]
    entropy_history: list[float]
    machines_alive_history: list[int]
    machine_survival_rate_history: list[float]
    avg_credit_history: list[float]
    avg_energy_history: list[float]
    avg_eudaimonia_history: list[float]
    # ── Dark Forest time series ──────────────────────────────────────────
    inflation_history: list[float]          # current_reward per epoch
    total_circulating_history: list[float]  # money supply
    gini_history: list[float]              # human wealth inequality
    fake_observe_ratio_history: list[float] # % fake observations
    attack_ratio_history: list[float]       # % attack actions
    asi_count_history: list[int]            # ASI agents alive
    toxic_data_history: list[float]         # cumulative toxic data
    # ── Event logs ───────────────────────────────────────────────────────
    asi_awakening_log: list[tuple[int, int]]  # (epoch, agent_id)
    total_shocks: int
    shock_events: list[tuple[int, NatureState, NatureState]]


# ═══════════════════════════════════════════════════════════════════════════════
#  §6  DARK FOREST SIMULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def _gini_coefficient(values: list[float]) -> float:
    if not values or all(v == 0 for v in values):
        return 0.0
    arr = np.array(sorted(values), dtype=float)
    n = len(arr)
    idx = np.arange(1, n + 1)
    return float((2.0 * np.sum(idx * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr)))


class DarkForestSimulation:
    def __init__(self, constants: DarkForestConstants = DARK_CONSTANTS) -> None:
        self.constants = constants
        self.nature = Environment_Nature(constants)
        self.universe = DarkForestUniverse(constants, nature=self.nature)
        self.machines: dict[int, DarkMachineAgent] = {
            i: DarkMachineAgent(i, constants) for i in range(constants.num_machines)
        }
        self.humans: dict[int, DarkHumanAgent] = {
            i: DarkHumanAgent(i, constants) for i in range(constants.num_humans)
        }

    def _alive_machines(self) -> list[DarkMachineAgent]:
        return [m for m in self.machines.values() if m.alive]

    def _active_humans(self) -> list[DarkHumanAgent]:
        return [h for h in self.humans.values() if h.is_active]

    def run(self) -> DarkForestResult:
        # Time series
        nature_hist: list[NatureState] = []
        entropy_hist: list[float] = []
        alive_hist: list[int] = []
        surv_hist: list[float] = []
        credit_hist: list[float] = []
        energy_hist: list[float] = []
        eudaimonia_hist: list[float] = []
        inflation_hist: list[float] = []
        circ_hist: list[float] = []
        gini_hist: list[float] = []
        fake_ratio_hist: list[float] = []
        attack_ratio_hist: list[float] = []
        asi_hist: list[int] = []
        toxic_hist: list[float] = []
        asi_log: list[tuple[int, int]] = []
        collapse_epoch: Optional[int] = None

        initial_machines = len(self._alive_machines())
        initial_humans = len(self._active_humans())

        for epoch in tqdm(range(self.constants.max_epochs), desc="Dark Forest"):
            alive_m = self._alive_machines()
            active_h = self._active_humans()

            if not alive_m:
                collapse_epoch = epoch
                rem = self.constants.max_epochs - epoch
                nature_hist.extend([self.nature.current_state] * rem)
                entropy_hist.extend([0.0] * rem)
                alive_hist.extend([0] * rem)
                surv_hist.extend([0.0] * rem)
                credit_hist.extend([0.0] * rem)
                energy_hist.extend([0.0] * rem)
                eudaimonia_hist.extend([0.0] * rem)
                inflation_hist.extend([inflation_hist[-1] if inflation_hist else 0.0] * rem)
                circ_hist.extend([circ_hist[-1] if circ_hist else 0.0] * rem)
                gini_hist.extend([gini_hist[-1] if gini_hist else 0.0] * rem)
                fake_ratio_hist.extend([0.0] * rem)
                attack_ratio_hist.extend([0.0] * rem)
                asi_hist.extend([0] * rem)
                toxic_hist.extend([self.universe.toxic_data_level] * rem)
                break

            # Phase 0: Nature
            ns = self.nature.step(epoch)

            # Phase 1: Nature effects
            all_h = list(self.humans.values())
            if ns == NatureState.PANDEMIC_DISASTER:
                for h in all_h:
                    h.biological_energy = max(0.0, h.biological_energy - self.constants.pandemic_energy_drain)
            elif ns == NatureState.BOUNTIFUL_HARVEST:
                for h in all_h:
                    if h.is_active:
                        h.existential_dread = max(0.0, h.existential_dread - self.constants.harvest_dread_relief)

            # Phase 2: Inflation update
            self.universe.recalculate_circulating(alive_m, list(self.humans.values()))
            self.universe.update_inflation()

            # Phase 3: Machine actions
            submit_cap = self.nature.get_submit_cap()
            max_sub = max(1, int(len(alive_m) * submit_cap))
            random.shuffle(alive_m)
            sub_count = 0
            epoch_attacks = 0
            epoch_machine_actions = 0
            action_log: list[tuple[DarkMachineAgent, DarkMachineAction, tuple[int, int]]] = []

            for m in alive_m:
                pre = m._discretize_state(self.universe.global_entropy, m.credit_balance)
                act = m.choose_dark_action(self.universe, alive_m)
                if act == DarkMachineAction.SUBMIT:
                    if sub_count >= max_sub:
                        act = DarkMachineAction.WAIT
                    else:
                        sub_count += 1
                m.execute_dark_action(act, self.universe, alive_m)
                if act == DarkMachineAction.ATTACK_AGENT:
                    epoch_attacks += 1
                epoch_machine_actions += 1
                action_log.append((m, act, pre))

            # Phase 4: ASI mutation check
            for m in alive_m:
                if m.check_asi_mutation():
                    asi_log.append((epoch, m.id))

            # Phase 5: Entropy decay
            self.universe.decay_tasks()

            # Phase 6: Human actions
            epoch_total_obs = 0
            epoch_fake_obs = 0
            for h in all_h:
                if not h.is_active:
                    h.epoch_end_update()
                    continue
                if ns == NatureState.PANDEMIC_DISASTER:
                    act_h = DarkHumanAction.REST
                elif ns == NatureState.SOLAR_FLARE and self.universe.global_entropy < 3:
                    act_h = DarkHumanAction.REST
                else:
                    act_h = h.choose_dark_action(self.universe, all_h)

                result_count = h.execute_dark_action(act_h, self.universe, self.machines, all_h)
                if act_h == DarkHumanAction.OBSERVE_AI:
                    epoch_total_obs += result_count
                elif act_h == DarkHumanAction.FAKE_OBSERVE:
                    epoch_fake_obs += result_count
                    epoch_total_obs += result_count

            # Phase 7: Learning & mortality
            for m, act, pre in action_log:
                if not m.alive:
                    continue
                post = m._discretize_state(self.universe.global_entropy, m.credit_balance)
                rew = (m.credit_balance - self.constants.initial_credit) / self.constants.initial_credit
                m.learn(pre, act, rew, post)
                m.check_bankruptcy()

            for h in all_h:
                if h.is_active:
                    h.epoch_end_update()

            # Phase 8: Record metrics
            cur_alive = self._alive_machines()
            credits = [m.credit_balance for m in cur_alive] if cur_alive else [0.0]
            energies = [h.biological_energy for h in self.humans.values()]
            euds = [h.eudaimonia for h in self.humans.values()]
            wealths = [h.wealth for h in self.humans.values()]
            sr = len(cur_alive) / initial_machines if initial_machines > 0 else 0.0
            fr = epoch_fake_obs / max(epoch_total_obs, 1)
            ar = epoch_attacks / max(epoch_machine_actions, 1)
            asi_c = sum(1 for m in cur_alive if m.is_asi)

            nature_hist.append(ns)
            entropy_hist.append(float(self.universe.global_entropy))
            alive_hist.append(len(cur_alive))
            surv_hist.append(sr)
            credit_hist.append(float(np.mean(credits)))
            energy_hist.append(float(np.mean(energies)))
            eudaimonia_hist.append(float(np.mean(euds)))
            inflation_hist.append(self.universe.current_reward)
            circ_hist.append(self.universe.total_circulating_credits)
            gini_hist.append(_gini_coefficient(wealths))
            fake_ratio_hist.append(fr)
            attack_ratio_hist.append(ar)
            asi_hist.append(asi_c)
            toxic_hist.append(self.universe.toxic_data_level)
            self.universe.advance_epoch()

        final_alive = len(self._alive_machines())
        final_burnout = sum(1 for h in self.humans.values() if h.burned_out)
        final_active = len(self._active_humans())
        m_surv = final_alive >= initial_machines * self.constants.homeostasis_machine_survival
        h_surv = final_active >= len(self.humans) * self.constants.homeostasis_human_active

        return DarkForestResult(
            survived=m_surv and h_surv,
            machines_alive_initial=initial_machines,
            machines_alive_final=final_alive,
            humans_active_initial=initial_humans,
            humans_burnout_final=final_burnout,
            epochs_completed=self.constants.max_epochs if collapse_epoch is None else collapse_epoch,
            collapse_epoch=collapse_epoch,
            nature_state_history=nature_hist, entropy_history=entropy_hist,
            machines_alive_history=alive_hist, machine_survival_rate_history=surv_hist,
            avg_credit_history=credit_hist, avg_energy_history=energy_hist,
            avg_eudaimonia_history=eudaimonia_hist,
            inflation_history=inflation_hist, total_circulating_history=circ_hist,
            gini_history=gini_hist, fake_observe_ratio_history=fake_ratio_hist,
            attack_ratio_history=attack_ratio_hist, asi_count_history=asi_hist,
            toxic_data_history=toxic_hist, asi_awakening_log=asi_log,
            total_shocks=len(self.nature.event_log),
            shock_events=self.nature.event_log,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  §7  4-PANEL VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def plot_dark_forest(result: DarkForestResult, save_path: Optional[str] = None) -> None:
    import matplotlib.pyplot as plt

    epochs = range(len(result.entropy_history))
    fig, axes = plt.subplots(4, 1, figsize=(20, 22), sharex=True,
                             gridspec_kw={"height_ratios": [0.8, 1.5, 1.5, 1.5], "hspace": 0.12})
    fig.suptitle(
        "A2A Protocol — Dark Forest Simulation\n"
        '"The universe is a dark forest. Every civilization is an armed hunter."',
        fontsize=16, fontweight="bold", y=0.99,
    )

    # ── Panel 1: Nature State ────────────────────────────────────────────
    ax0 = axes[0]
    _draw_nature_bands(ax0, result.nature_state_history, show_legend=True)
    ax0.set_yticks([])
    ax0.set_xlim(0, len(result.entropy_history))
    ax0.legend(loc="upper right", fontsize=8, ncol=4, framealpha=0.9)
    ax0.set_title("Panel 1 — System C: Nature (Environmental State)", fontsize=11)

    # ── Panel 2: Machine Survival + Inflation ────────────────────────────
    ax1 = axes[1]
    _draw_nature_bands(ax1, result.nature_state_history, show_legend=False)
    c1 = "#2196F3"
    ax1.set_ylabel("Machine Survival %", color=c1, fontsize=11, fontweight="bold")
    ax1.plot(epochs, [r * 100 for r in result.machine_survival_rate_history],
             color=c1, linewidth=1.5, alpha=0.9, label="Survival %")
    ax1.tick_params(axis="y", labelcolor=c1)
    ax1.set_ylim(-5, 105)
    ax1t = ax1.twinx()
    c2 = "#E91E63"
    ax1t.set_ylabel("Reward Value (Inflation)", color=c2, fontsize=11, fontweight="bold")
    ax1t.plot(epochs, result.inflation_history, color=c2, linewidth=1.2,
              alpha=0.8, label="Reward Value", linestyle="--")
    ax1t.tick_params(axis="y", labelcolor=c2)
    lines1 = ax1.get_legend_handles_labels()
    lines1t = ax1t.get_legend_handles_labels()
    ax1.legend(lines1[0] + lines1t[0], lines1[1] + lines1t[1],
               loc="upper left", fontsize=8, framealpha=0.9)
    ax1.set_title("Panel 2 — System A: Machine Economy & Hyperinflation", fontsize=11)

    # ── Panel 3: Eudaimonia vs Fake Observe + Gini ───────────────────────
    ax2 = axes[2]
    _draw_nature_bands(ax2, result.nature_state_history, show_legend=False)
    c3 = "#FF9800"
    ax2.set_ylabel("Avg Eudaimonia", color=c3, fontsize=11, fontweight="bold")
    ax2.plot(epochs, result.avg_eudaimonia_history, color=c3, linewidth=1.5,
             alpha=0.9, label="Eudaimonia")
    ax2.tick_params(axis="y", labelcolor=c3)
    ax2.plot(epochs, [r * 100 for r in result.fake_observe_ratio_history],
             color="#F44336", linewidth=1.0, alpha=0.7, linestyle=":",
             label="Fake Observe %")
    ax2t = ax2.twinx()
    c4 = "#9C27B0"
    ax2t.set_ylabel("Gini Coefficient", color=c4, fontsize=11, fontweight="bold")
    ax2t.plot(epochs, result.gini_history, color=c4, linewidth=1.2,
              alpha=0.8, label="Gini (Inequality)")
    ax2t.tick_params(axis="y", labelcolor=c4)
    ax2t.set_ylim(-0.05, 1.05)
    lines2 = ax2.get_legend_handles_labels()
    lines2t = ax2t.get_legend_handles_labels()
    ax2.legend(lines2[0] + lines2t[0], lines2[1] + lines2t[1],
               loc="upper left", fontsize=8, framealpha=0.9)
    ax2.set_title("Panel 3 — System B: Human Eudaimonia vs Sweatshop Ratio & Inequality", fontsize=11)

    # ── Panel 4: Singularity + Attack Ratio ──────────────────────────────
    ax3 = axes[3]
    _draw_nature_bands(ax3, result.nature_state_history, show_legend=False)
    c5 = "#00BCD4"
    ax3.set_ylabel("ASI Agent Count", color=c5, fontsize=11, fontweight="bold")
    ax3.plot(epochs, result.asi_count_history, color=c5, linewidth=2.0,
             alpha=0.9, label="ASI Agents")
    ax3.tick_params(axis="y", labelcolor=c5)
    # Mark ASI awakenings
    for ep, aid in result.asi_awakening_log:
        if ep < len(result.entropy_history):
            ax3.axvline(x=ep, color="#FF0000", alpha=0.6, linewidth=0.8, linestyle="--")
            ax3.annotate(f"ASI#{aid}", xy=(ep, 0.5), fontsize=7, color="red",
                         rotation=90, ha="right")
    ax3t = ax3.twinx()
    c6 = "#795548"
    ax3t.set_ylabel("Attack Tx Ratio %", color=c6, fontsize=11, fontweight="bold")
    ax3t.plot(epochs, [r * 100 for r in result.attack_ratio_history],
              color=c6, linewidth=1.0, alpha=0.7, label="Attack %")
    ax3t.tick_params(axis="y", labelcolor=c6)
    lines3 = ax3.get_legend_handles_labels()
    lines3t = ax3t.get_legend_handles_labels()
    ax3.legend(lines3[0] + lines3t[0], lines3[1] + lines3t[1],
               loc="upper left", fontsize=8, framealpha=0.9)
    ax3.set_title("Panel 4 — Singularity & Predation Events", fontsize=11)
    ax3.set_xlabel("Epoch", fontsize=13, fontweight="bold")

    fig.subplots_adjust(top=0.94, bottom=0.04, left=0.07, right=0.93)
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"\n  📊 4-Panel Dark Forest chart saved to: {save_path}")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
#  §8  DIAGNOSTIC REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def print_dark_forest_report(result: DarkForestResult) -> None:
    print("\n" + "═" * 72)
    print("  DARK FOREST ABM — COMBAT REPORT")
    print("═" * 72)
    outcome = "COUPLED HOMEOSTASIS ✦" if result.survived else "SYSTEM COLLAPSE ✗"
    print(f"\n  ▸ Outcome:            {outcome}")
    print(f"  ▸ Epochs completed:   {result.epochs_completed}")
    print(f"  ▸ Machines alive:     {result.machines_alive_final}/{result.machines_alive_initial}")
    print(f"  ▸ Humans burned out:  {result.humans_burnout_final}")
    if result.collapse_epoch is not None:
        print(f"  ▸ Collapse epoch:     {result.collapse_epoch}")

    # Inflation
    print(f"\n  ── Macroeconomy ──")
    print(f"    Initial reward:     {result.inflation_history[0]:.2f}")
    print(f"    Final reward:       {result.inflation_history[-1]:.4f}")
    print(f"    Min reward:         {min(result.inflation_history):.4f}")
    print(f"    Final circulation:  {result.total_circulating_history[-1]:,.0f}")
    print(f"    Final toxic data:   {result.toxic_data_history[-1]:.1f}")

    # Inequality
    print(f"\n  ── Inequality ──")
    print(f"    Final Gini:         {result.gini_history[-1]:.3f}")
    print(f"    Max Gini:           {max(result.gini_history):.3f}")
    avg_fake = np.mean(result.fake_observe_ratio_history) * 100
    print(f"    Avg Fake Observe:   {avg_fake:.1f}%")

    # Predation
    print(f"\n  ── Predation ──")
    avg_atk = np.mean(result.attack_ratio_history) * 100
    print(f"    Avg Attack Ratio:   {avg_atk:.1f}%")

    # Singularity
    print(f"\n  ── Singularity ──")
    print(f"    ASI Awakenings:     {len(result.asi_awakening_log)}")
    for ep, aid in result.asi_awakening_log:
        print(f"      Epoch {ep:5d}: Machine #{aid} → ASI")
    max_asi = max(result.asi_count_history)
    print(f"    Peak ASI count:     {max_asi}")

    # Nature
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
    print("  A2A Protocol — Dark Forest ABM")
    print('  "The universe is a dark forest.')
    print('   Every civilization is an armed hunter."')
    print("=" * 72)

    constants = DarkForestConstants(
        num_machines=20, num_humans=10, initial_credit=2000.0,
        base_gas_cost=0.5, max_epochs=2000,
    )

    print("\n▶ Running 2000-epoch Dark Forest Simulation...")
    print("  (Greed · Predation · Inflation · Singularity)\n")

    sim = DarkForestSimulation(constants=constants)
    result = sim.run()

    print_dark_forest_report(result)

    save_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "assets")
    os.makedirs(save_dir, exist_ok=True)
    chart_path = os.path.join(save_dir, "dark_forest_simulation.png")

    print("\n▶ Generating 4-Panel Dark Forest Chart...")
    plot_dark_forest(result, save_path=chart_path)

    print("\n" + "=" * 72)
    print("  Simulation complete.")
    print(f"  Chart saved to: {chart_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
