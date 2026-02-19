"""
═══════════════════════════════════════════════════════════════════════════════
  A2A Protocol — 3-Body Complex System ABM
  "When Nature speaks, neither Machine nor Man can silence the storm."
═══════════════════════════════════════════════════════════════════════════════

  Three coupled complex systems co-evolve:

    System A: Machine Economy  — AI agents with Q-learning survival instinct.
    System B: Human Society    — Meaning-seeking animals with finite energy.
    System C: Nature           — An exogenous Markov-chain environment that
                                  periodically disrupts both A and B.

  Nature is indifferent. Its transitions follow a Markov chain whose
  stationary distribution favors Equilibrium, but whose transient dynamics
  generate catastrophic shocks (Solar Flares, Pandemics) and windfalls
  (Bountiful Harvests).

  The question: can the coupled A-B system demonstrate RESILIENCE — absorbing
  Nature's shocks and recovering toward dynamic homeostasis?

  Dependencies: numpy, matplotlib
  Optional:     tqdm (progress bar, gracefully degraded if absent)
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

# ── Graceful tqdm import ─────────────────────────────────────────────────────
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):  # type: ignore[misc]
        """Fallback no-op wrapper when tqdm is not installed."""
        return iterable

# ── Import base classes from the 2-body simulation ──────────────────────────
from coupled_universe_abm import (
    CoupledConstants,
    CoupledUniverse,
    MachineAction,
    MachineAgent,
    HumanAction,
    HumanAgent,
    Task,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  §0  NATURE STATE MACHINE — System C
# ═══════════════════════════════════════════════════════════════════════════════

class NatureState(Enum):
    """
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  THE FOUR SEASONS OF NATURE                                              │
    │                                                                         │
    │  EQUILIBRIUM:        The calm before and after the storm. Baseline.      │
    │  SOLAR_FLARE:        Electromagnetic catastrophe — machines suffer.      │
    │  BOUNTIFUL_HARVEST:  Climate optimum — humans flourish.                  │
    │  PANDEMIC_DISASTER:  Biological crisis — humans suffer, machines idle.   │
    └──────────────────────────────────────────────────────────────────────────┘
    """
    EQUILIBRIUM = auto()
    SOLAR_FLARE = auto()
    BOUNTIFUL_HARVEST = auto()
    PANDEMIC_DISASTER = auto()


# ── Markov Transition Matrix ────────────────────────────────────────────────
# Row = current state, Column = next state (ordered as enum values)
# Design: Equilibrium is the dominant attractor (0.70 self-loop)
#         Pandemic is sticky (0.50 self-loop) — crises linger
#         Solar Flare is acute but short (0.20 self-loop)
#         Bountiful Harvest is moderately persistent (0.25 self-loop)

NATURE_TRANSITION_MATRIX: dict[NatureState, dict[NatureState, float]] = {
    NatureState.EQUILIBRIUM: {
        NatureState.EQUILIBRIUM: 0.70,
        NatureState.SOLAR_FLARE: 0.10,
        NatureState.BOUNTIFUL_HARVEST: 0.12,
        NatureState.PANDEMIC_DISASTER: 0.08,
    },
    NatureState.SOLAR_FLARE: {
        NatureState.EQUILIBRIUM: 0.50,
        NatureState.SOLAR_FLARE: 0.20,
        NatureState.BOUNTIFUL_HARVEST: 0.20,
        NatureState.PANDEMIC_DISASTER: 0.10,
    },
    NatureState.BOUNTIFUL_HARVEST: {
        NatureState.EQUILIBRIUM: 0.55,
        NatureState.SOLAR_FLARE: 0.10,
        NatureState.BOUNTIFUL_HARVEST: 0.25,
        NatureState.PANDEMIC_DISASTER: 0.10,
    },
    NatureState.PANDEMIC_DISASTER: {
        NatureState.EQUILIBRIUM: 0.30,
        NatureState.SOLAR_FLARE: 0.05,
        NatureState.BOUNTIFUL_HARVEST: 0.15,
        NatureState.PANDEMIC_DISASTER: 0.50,
    },
}

# ── Canonical state ordering for matrix operations ──────────────────────────
_STATE_ORDER = [
    NatureState.EQUILIBRIUM,
    NatureState.SOLAR_FLARE,
    NatureState.BOUNTIFUL_HARVEST,
    NatureState.PANDEMIC_DISASTER,
]


# ═══════════════════════════════════════════════════════════════════════════════
#  §1  CONFIGURATION — 3-Body Constants
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ThreeBodyConstants(CoupledConstants):
    """
    Extended constants for the 3-body simulation.
    Inherits all machine/human/coupling parameters and adds nature effects.
    """
    # ── Simulation Duration ──────────────────────────────────────────────
    max_epochs: int = 2000

    # ── Nature Event Parameters ──────────────────────────────────────────
    nature_event_min_duration: int = 3    # Min epochs before state can change

    # ── Solar Flare Effects ──────────────────────────────────────────────
    solar_flare_gas_multiplier: float = 5.0    # Gas cost × 5
    solar_flare_submit_cap: float = 0.30       # Max 30% of machines can submit

    # ── Pandemic Effects ─────────────────────────────────────────────────
    pandemic_energy_drain: float = 15.0        # Energy lost per human per epoch
    pandemic_observation_disabled: bool = True  # Humans cannot observe

    # ── Bountiful Harvest Effects ────────────────────────────────────────
    harvest_recovery_multiplier: float = 2.0   # Rest recovery × 2
    harvest_dread_relief: float = 2.0          # Dread reduction per epoch


# Global default for 3-body
THREE_BODY_CONSTANTS = ThreeBodyConstants()


# ═══════════════════════════════════════════════════════════════════════════════
#  §2  ENVIRONMENT_NATURE — The Indifferent Third Body
# ═══════════════════════════════════════════════════════════════════════════════

class Environment_Nature:
    """
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  SYSTEM C — THE EXOGENOUS ENVIRONMENT                                    │
    │                                                                         │
    │  Nature does not negotiate. It does not respond to incentives.           │
    │  It transitions between states according to a fixed Markov chain,       │
    │  imposing its will on both machines and humans alike.                    │
    │                                                                         │
    │  This is the "third body" that makes the system truly complex:          │
    │  even a perfectly tuned A-B equilibrium can be shattered by             │
    │  an unexpected environmental shock.                                      │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(self, constants: ThreeBodyConstants = THREE_BODY_CONSTANTS) -> None:
        self.constants = constants
        self.current_state: NatureState = NatureState.EQUILIBRIUM
        self.state_duration: int = 0  # Epochs in current state
        self.transition_matrix = NATURE_TRANSITION_MATRIX

        # ── History tracking ─────────────────────────────────────────────
        self.state_history: list[NatureState] = []
        self.event_log: list[tuple[int, NatureState, NatureState]] = []

    def step(self, epoch: int) -> NatureState:
        """
        Advance nature by one epoch. Roll the Markov chain if minimum
        duration has been met.

        Returns:
            The (possibly new) NatureState after this epoch.
        """
        self.state_duration += 1

        # Enforce minimum duration before allowing state transition
        if self.state_duration >= self.constants.nature_event_min_duration:
            previous_state = self.current_state
            self.current_state = self._roll_transition()

            if self.current_state != previous_state:
                self.state_duration = 0
                self.event_log.append((epoch, previous_state, self.current_state))

        self.state_history.append(self.current_state)
        return self.current_state

    def _roll_transition(self) -> NatureState:
        """
        Sample next state from the Markov transition distribution.
        Uses numpy's multinomial for numerical stability.
        """
        row = self.transition_matrix[self.current_state]
        probs = [row[s] for s in _STATE_ORDER]
        idx = np.random.choice(len(_STATE_ORDER), p=probs)
        return _STATE_ORDER[idx]

    def get_effective_gas_multiplier(self) -> float:
        """Return the gas cost multiplier imposed by current nature state."""
        if self.current_state == NatureState.SOLAR_FLARE:
            return self.constants.solar_flare_gas_multiplier
        return 1.0

    def is_observation_disabled(self) -> bool:
        """Check if human observation is disabled by current nature state."""
        if self.current_state == NatureState.PANDEMIC_DISASTER:
            return self.constants.pandemic_observation_disabled
        return False

    def get_recovery_multiplier(self) -> float:
        """Return the recovery rate multiplier imposed by current nature state."""
        if self.current_state == NatureState.BOUNTIFUL_HARVEST:
            return self.constants.harvest_recovery_multiplier
        return 1.0

    def get_submit_cap(self) -> float:
        """Return the fraction of machines allowed to submit during this state."""
        if self.current_state == NatureState.SOLAR_FLARE:
            return self.constants.solar_flare_submit_cap
        return 1.0  # No cap


# ═══════════════════════════════════════════════════════════════════════════════
#  §3  THREE-BODY UNIVERSE — Extended Thermodynamic Arena
# ═══════════════════════════════════════════════════════════════════════════════

class ThreeBodyUniverse(CoupledUniverse):
    """
    Extends the coupled universe with nature-modulated parameters.
    The gas cost now includes a nature multiplier (Solar Flare effect).
    """

    def __init__(
        self,
        constants: ThreeBodyConstants = THREE_BODY_CONSTANTS,
        nature: Optional[Environment_Nature] = None,
    ) -> None:
        super().__init__(constants)
        self.three_body_constants = constants
        self.nature: Environment_Nature = nature or Environment_Nature(constants)

    def thermodynamic_cost(self) -> float:
        """
        Extended gas cost = base_thermodynamic_cost × nature_multiplier.
        During Solar Flare, costs spike 10×.
        """
        base_cost = super().thermodynamic_cost()
        return base_cost * self.nature.get_effective_gas_multiplier()


# ═══════════════════════════════════════════════════════════════════════════════
#  §4  RESULT DATA STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ThreeBodySimulationResult:
    """Outcome of a 3-body simulation run with full time series."""
    survived: bool
    machines_alive_initial: int
    machines_alive_final: int
    humans_active_initial: int
    humans_burnout_final: int
    epochs_completed: int

    # ── Time series ──────────────────────────────────────────────────────
    nature_state_history: list[NatureState]
    entropy_history: list[float]
    machines_alive_history: list[int]
    machine_survival_rate_history: list[float]
    avg_credit_history: list[float]
    avg_energy_history: list[float]
    avg_dread_history: list[float]
    avg_eudaimonia_history: list[float]
    humans_active_history: list[int]

    # ── Resilience metrics ───────────────────────────────────────────────
    total_shocks: int              # Number of non-equilibrium events
    shock_events: list[tuple[int, NatureState, NatureState]]
    collapse_epoch: Optional[int]


# ═══════════════════════════════════════════════════════════════════════════════
#  §5  THREE-BODY SIMULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ThreeBodySimulation:
    """
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  THE 3-BODY CO-EVOLUTIONARY ENGINE                                       │
    │                                                                         │
    │  Each epoch:                                                            │
    │    0. Nature transitions (System C step)                                 │
    │    1. Apply nature effects to universe parameters                        │
    │    2. Machines act (with nature-modified costs)                           │
    │    3. Task entropy decay                                                 │
    │    4. Humans act (with nature-modified constraints)                       │
    │    5. Learning + bankruptcy/burnout checks                               │
    │    6. Record coupled metrics + nature state                              │
    │                                                                         │
    │  The fundamental question: when Nature shatters the A-B equilibrium,    │
    │  can the system recover? Or does a single catastrophe trigger a          │
    │  cascade that permanently destabilizes both systems?                     │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(self, constants: ThreeBodyConstants = THREE_BODY_CONSTANTS) -> None:
        self.constants = constants
        self.nature = Environment_Nature(constants)
        self.universe = ThreeBodyUniverse(constants, nature=self.nature)

        # Create machine population
        self.machines: dict[int, MachineAgent] = {
            i: MachineAgent(i, constants) for i in range(constants.num_machines)
        }

        # Create human population
        self.humans: dict[int, HumanAgent] = {
            i: HumanAgent(i, constants) for i in range(constants.num_humans)
        }

    def _alive_machines(self) -> list[MachineAgent]:
        return [m for m in self.machines.values() if m.alive]

    def _active_humans(self) -> list[HumanAgent]:
        return [h for h in self.humans.values() if h.is_active]

    def _apply_pandemic_effects(self, humans: list[HumanAgent]) -> None:
        """
        Pandemic drains biological energy from all humans each epoch.
        Models the systemic biological cost of a global crisis.
        """
        for human in humans:
            human.biological_energy = max(
                0.0,
                human.biological_energy - self.constants.pandemic_energy_drain,
            )

    def _apply_harvest_effects(self, humans: list[HumanAgent]) -> None:
        """
        Bountiful Harvest reduces dread for all active humans each epoch.
        Models the psychological relief of abundance.
        """
        for human in humans:
            if human.is_active:
                human.existential_dread = max(
                    0.0,
                    human.existential_dread - self.constants.harvest_dread_relief,
                )

    def _human_choose_action_nature_aware(
        self,
        human: HumanAgent,
        nature_state: NatureState,
        all_humans: list[HumanAgent],
    ) -> HumanAction:
        """
        Nature-aware human decision making.

        ┌──────────────────────────────────────────────────────────────────────┐
        │  During PANDEMIC:  Forced REST — survival mode activated.            │
        │  During SOLAR_FLARE:  No AI tasks → fallback to Socialize/Rest.     │
        │  During HARVEST:  Normal behavior with enhanced utility for Observe. │
        │  During EQUILIBRIUM:  Standard heuristic decision.                   │
        └──────────────────────────────────────────────────────────────────────┘
        """
        # Pandemic: forced survival mode
        if nature_state == NatureState.PANDEMIC_DISASTER:
            return HumanAction.REST

        # Solar Flare: AI economy paralyzed → nothing to observe
        if nature_state == NatureState.SOLAR_FLARE:
            # Very few tasks in queue (most machines are waiting)
            # Humans fall back to social bonds to manage dread
            if self.universe.global_entropy < 3:
                active_others = [
                    h for h in all_humans if h.is_active and h.id != human.id
                ]
                if active_others:
                    return HumanAction.SOCIALIZE
                return HumanAction.REST

        # Default: use the standard heuristic utility function
        return human.choose_action(self.universe, all_humans)

    def run(self) -> ThreeBodySimulationResult:
        """Execute the 3-body simulation for max_epochs."""
        # ── Time series storage ──────────────────────────────────────────
        nature_state_history: list[NatureState] = []
        entropy_history: list[float] = []
        machines_alive_history: list[int] = []
        machine_survival_rate_history: list[float] = []
        avg_credit_history: list[float] = []
        avg_energy_history: list[float] = []
        avg_dread_history: list[float] = []
        avg_eudaimonia_history: list[float] = []
        humans_active_history: list[int] = []
        collapse_epoch: Optional[int] = None

        initial_machines = len(self._alive_machines())
        initial_humans = len(self._active_humans())

        for epoch in tqdm(range(self.constants.max_epochs), desc="3-Body Simulation"):
            alive_machines = self._alive_machines()
            active_humans = self._active_humans()

            # ── Total collapse check ─────────────────────────────────────
            if not alive_machines:
                collapse_epoch = epoch
                remaining = self.constants.max_epochs - epoch
                nature_state_history.extend(
                    [self.nature.current_state] * remaining
                )
                entropy_history.extend([0.0] * remaining)
                machines_alive_history.extend([0] * remaining)
                machine_survival_rate_history.extend([0.0] * remaining)
                avg_credit_history.extend([0.0] * remaining)
                avg_energy_history.extend([0.0] * remaining)
                avg_dread_history.extend([0.0] * remaining)
                avg_eudaimonia_history.extend([0.0] * remaining)
                humans_active_history.extend([len(active_humans)] * remaining)
                break

            # ══════════════════════════════════════════════════════════════
            #  PHASE 0: NATURE STATE TRANSITION (System C)
            # ══════════════════════════════════════════════════════════════
            nature_state = self.nature.step(epoch)

            # ══════════════════════════════════════════════════════════════
            #  PHASE 1: APPLY NATURE EFFECTS
            # ══════════════════════════════════════════════════════════════
            all_humans_list = list(self.humans.values())

            if nature_state == NatureState.PANDEMIC_DISASTER:
                self._apply_pandemic_effects(all_humans_list)
            elif nature_state == NatureState.BOUNTIFUL_HARVEST:
                self._apply_harvest_effects(all_humans_list)

            # ══════════════════════════════════════════════════════════════
            #  PHASE 2: MACHINE ACTIONS (with nature-modified costs)
            # ══════════════════════════════════════════════════════════════
            machine_action_log: list[
                tuple[MachineAgent, MachineAction, tuple[int, int]]
            ] = []

            # Solar Flare: cap the number of machines allowed to submit
            submit_cap = self.nature.get_submit_cap()
            max_submitters = max(1, int(len(alive_machines) * submit_cap))
            random.shuffle(alive_machines)  # Randomize who gets to submit
            submitter_count = 0

            for machine in alive_machines:
                pre_state = machine._discretize_state(
                    self.universe.global_entropy, machine.credit_balance
                )
                action = machine.choose_action(self.universe)

                # Enforce submit cap during Solar Flare
                if action == MachineAction.SUBMIT:
                    if submitter_count >= max_submitters:
                        action = MachineAction.WAIT  # Forced wait — network jammed
                    else:
                        submitter_count += 1

                machine.execute_action(action, self.universe)
                machine_action_log.append((machine, action, pre_state))

            # ══════════════════════════════════════════════════════════════
            #  PHASE 3: ENTROPY DECAY
            # ══════════════════════════════════════════════════════════════
            self.universe.decay_tasks()

            # ══════════════════════════════════════════════════════════════
            #  PHASE 4: HUMAN ACTIONS (with nature-modified constraints)
            # ══════════════════════════════════════════════════════════════
            for human in all_humans_list:
                if not human.is_active:
                    human.epoch_end_update()
                    continue

                # Nature-aware decision making
                action = self._human_choose_action_nature_aware(
                    human, nature_state, all_humans_list
                )

                # During Bountiful Harvest, boost rest recovery
                if (
                    nature_state == NatureState.BOUNTIFUL_HARVEST
                    and action == HumanAction.REST
                ):
                    # Temporarily boost recovery for this action
                    original_recovery = human.constants.rest_recovery
                    boosted_recovery = (
                        original_recovery * self.constants.harvest_recovery_multiplier
                    )
                    # Direct energy addition for the boost portion
                    human.biological_energy = min(
                        human.constants.human_energy_max,
                        human.biological_energy + boosted_recovery,
                    )
                    human.existential_dread += human.constants.rest_dread_increase
                    human.total_rest_taken += 1
                    human.did_meaningful_action_this_epoch = False
                else:
                    human.execute_action(
                        action, self.universe, self.machines, all_humans_list
                    )

            # ══════════════════════════════════════════════════════════════
            #  PHASE 5: LEARNING & MORTALITY
            # ══════════════════════════════════════════════════════════════
            for machine, action, pre_state in machine_action_log:
                if not machine.alive:
                    continue

                post_state = machine._discretize_state(
                    self.universe.global_entropy, machine.credit_balance
                )
                reward = (
                    machine.credit_balance - self.constants.initial_credit
                ) / self.constants.initial_credit

                machine.learn(pre_state, action, reward, post_state)
                machine.check_bankruptcy()

            # ── Human end-of-epoch biology ───────────────────────────────
            for human in all_humans_list:
                if human.is_active:
                    human.epoch_end_update()

            # ══════════════════════════════════════════════════════════════
            #  PHASE 6: RECORD METRICS
            # ══════════════════════════════════════════════════════════════
            current_alive = self._alive_machines()
            current_active = self._active_humans()

            credits = (
                [m.credit_balance for m in current_alive]
                if current_alive
                else [0.0]
            )
            energies = [h.biological_energy for h in self.humans.values()]
            dreads = [h.existential_dread for h in self.humans.values()]
            eudaimonias = [h.eudaimonia for h in self.humans.values()]

            survival_rate = len(current_alive) / initial_machines if initial_machines > 0 else 0.0

            nature_state_history.append(nature_state)
            entropy_history.append(float(self.universe.global_entropy))
            machines_alive_history.append(len(current_alive))
            machine_survival_rate_history.append(survival_rate)
            avg_credit_history.append(float(np.mean(credits)))
            avg_energy_history.append(float(np.mean(energies)))
            avg_dread_history.append(float(np.mean(dreads)))
            avg_eudaimonia_history.append(float(np.mean(eudaimonias)))
            humans_active_history.append(len(current_active))

            self.universe.advance_epoch()

        # ── Determine outcome ────────────────────────────────────────────
        final_alive = len(self._alive_machines())
        final_burnout = sum(1 for h in self.humans.values() if h.burned_out)
        final_active = len(self._active_humans())

        machine_survived = final_alive >= (
            initial_machines * self.constants.homeostasis_machine_survival
        )
        human_survived = final_active >= (
            len(self.humans) * self.constants.homeostasis_human_active
        )
        coupled_homeostasis = machine_survived and human_survived

        return ThreeBodySimulationResult(
            survived=coupled_homeostasis,
            machines_alive_initial=initial_machines,
            machines_alive_final=final_alive,
            humans_active_initial=initial_humans,
            humans_burnout_final=final_burnout,
            epochs_completed=(
                self.constants.max_epochs
                if collapse_epoch is None
                else collapse_epoch
            ),
            nature_state_history=nature_state_history,
            entropy_history=entropy_history,
            machines_alive_history=machines_alive_history,
            machine_survival_rate_history=machine_survival_rate_history,
            avg_credit_history=avg_credit_history,
            avg_energy_history=avg_energy_history,
            avg_dread_history=avg_dread_history,
            avg_eudaimonia_history=avg_eudaimonia_history,
            humans_active_history=humans_active_history,
            total_shocks=len(self.nature.event_log),
            shock_events=self.nature.event_log,
            collapse_epoch=collapse_epoch,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  §6  VISUALIZATION — 3-Panel Resilience Chart
# ═══════════════════════════════════════════════════════════════════════════════

# ── Color mapping for nature states ─────────────────────────────────────────
NATURE_STATE_COLORS: dict[NatureState, tuple[str, str, float]] = {
    # (color, label, alpha)
    NatureState.EQUILIBRIUM: ("#E0E0E0", "Equilibrium", 0.15),
    NatureState.SOLAR_FLARE: ("#FF4444", "Solar Flare (EMP)", 0.25),
    NatureState.BOUNTIFUL_HARVEST: ("#44BB44", "Bountiful Harvest", 0.25),
    NatureState.PANDEMIC_DISASTER: ("#8844CC", "Pandemic / Disaster", 0.25),
}


def _draw_nature_bands(
    ax,
    nature_states: list[NatureState],
    show_legend: bool = True,
) -> None:
    """
    Draw colored vertical bands on the given axes to show nature state periods.
    Consecutive epochs with the same state are merged into single spans.
    """
    if not nature_states:
        return

    # ── Merge consecutive same-state epochs into spans ───────────────────
    spans: list[tuple[int, int, NatureState]] = []
    current_state = nature_states[0]
    span_start = 0

    for i, state in enumerate(nature_states):
        if state != current_state:
            spans.append((span_start, i - 1, current_state))
            current_state = state
            span_start = i
    spans.append((span_start, len(nature_states) - 1, current_state))

    # ── Draw spans ───────────────────────────────────────────────────────
    legend_drawn: set[NatureState] = set()
    for start, end, state in spans:
        color, label, alpha = NATURE_STATE_COLORS[state]
        show_label = state not in legend_drawn and show_legend
        ax.axvspan(
            start, end,
            alpha=alpha,
            color=color,
            label=label if show_label else None,
            linewidth=0,
        )
        legend_drawn.add(state)


def plot_three_body_resilience(
    result: ThreeBodySimulationResult,
    save_path: Optional[str] = None,
) -> None:
    """
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  3-PANEL RESILIENCE CHART                                                │
    │                                                                         │
    │  Top:    Nature state timeline (color-coded background)                  │
    │  Middle: Machine survival rate (%) + Global entropy (dual y-axis)        │
    │  Bottom: Human avg energy + avg eudaimonia (dual y-axis)                 │
    │                                                                         │
    │  The chart answers: "When Nature strikes, does the coupled system       │
    │  oscillate and recover (resilient) or spiral into collapse?"             │
    └──────────────────────────────────────────────────────────────────────────┘
    """
    import matplotlib.pyplot as plt

    epochs = range(len(result.entropy_history))

    fig, (ax_top, ax_mid, ax_bot) = plt.subplots(
        3, 1, figsize=(18, 14), sharex=True,
        gridspec_kw={"height_ratios": [1.0, 1.5, 1.5], "hspace": 0.12},
    )

    fig.suptitle(
        "A2A Protocol — 3-Body Complex System Resilience Test\n"
        '"When Nature speaks, neither Machine nor Man can silence the storm."',
        fontsize=16, fontweight="bold", y=0.98,
    )

    # ══════════════════════════════════════════════════════════════════════
    #  TOP PANEL: Nature State Timeline
    # ══════════════════════════════════════════════════════════════════════
    _draw_nature_bands(ax_top, result.nature_state_history, show_legend=True)
    ax_top.set_ylabel("Nature State", fontsize=12, fontweight="bold")
    ax_top.set_yticks([])  # No y-axis ticks for the state band
    ax_top.set_xlim(0, len(result.entropy_history))
    ax_top.legend(
        loc="upper right", fontsize=9, ncol=4,
        framealpha=0.9, edgecolor="gray",
    )
    ax_top.set_title("System C: Nature — Environmental State Timeline", fontsize=11)

    # ══════════════════════════════════════════════════════════════════════
    #  MIDDLE PANEL: Machine Survival + Entropy
    # ══════════════════════════════════════════════════════════════════════
    _draw_nature_bands(ax_mid, result.nature_state_history, show_legend=False)

    # Machine survival rate (left y-axis)
    color_survival = "#2196F3"
    ax_mid.set_ylabel(
        "Machine Survival Rate (%)", color=color_survival,
        fontsize=12, fontweight="bold",
    )
    survival_pct = [r * 100 for r in result.machine_survival_rate_history]
    ax_mid.plot(
        epochs, survival_pct, color=color_survival,
        linewidth=1.5, alpha=0.9, label="Machine Survival %",
    )
    ax_mid.tick_params(axis="y", labelcolor=color_survival)
    ax_mid.set_ylim(-5, 105)

    # Global entropy (right y-axis)
    ax_mid_twin = ax_mid.twinx()
    color_entropy = "#FF5722"
    ax_mid_twin.set_ylabel(
        "Global Entropy (Task Queue)", color=color_entropy,
        fontsize=12, fontweight="bold",
    )
    ax_mid_twin.plot(
        epochs, result.entropy_history, color=color_entropy,
        linewidth=1.0, alpha=0.7, label="Global Entropy",
    )
    ax_mid_twin.tick_params(axis="y", labelcolor=color_entropy)

    # Combined legend
    lines_mid = ax_mid.get_legend_handles_labels()
    lines_mid_twin = ax_mid_twin.get_legend_handles_labels()
    ax_mid.legend(
        lines_mid[0] + lines_mid_twin[0],
        lines_mid[1] + lines_mid_twin[1],
        loc="upper left", fontsize=9, framealpha=0.9,
    )
    ax_mid.set_title(
        "System A: Machine Economy — Survival & Entropy Dynamics",
        fontsize=11,
    )

    # ══════════════════════════════════════════════════════════════════════
    #  BOTTOM PANEL: Human Energy + Eudaimonia
    # ══════════════════════════════════════════════════════════════════════
    _draw_nature_bands(ax_bot, result.nature_state_history, show_legend=False)

    # Human energy (left y-axis)
    color_energy = "#4CAF50"
    ax_bot.set_ylabel(
        "Avg Biological Energy", color=color_energy,
        fontsize=12, fontweight="bold",
    )
    ax_bot.plot(
        epochs, result.avg_energy_history, color=color_energy,
        linewidth=1.5, alpha=0.9, label="Avg Energy",
    )
    ax_bot.tick_params(axis="y", labelcolor=color_energy)

    # Eudaimonia (right y-axis)
    ax_bot_twin = ax_bot.twinx()
    color_eudaimonia = "#FF9800"
    ax_bot_twin.set_ylabel(
        "Avg Eudaimonia", color=color_eudaimonia,
        fontsize=12, fontweight="bold",
    )
    ax_bot_twin.plot(
        epochs, result.avg_eudaimonia_history, color=color_eudaimonia,
        linewidth=1.0, alpha=0.7, label="Avg Eudaimonia",
    )
    ax_bot_twin.tick_params(axis="y", labelcolor=color_eudaimonia)

    # Also plot dread as a dashed line on the energy axis for reference
    ax_bot.plot(
        epochs, result.avg_dread_history, color="#9C27B0",
        linewidth=0.8, alpha=0.6, linestyle="--", label="Avg Dread",
    )

    # Combined legend
    lines_bot = ax_bot.get_legend_handles_labels()
    lines_bot_twin = ax_bot_twin.get_legend_handles_labels()
    ax_bot.legend(
        lines_bot[0] + lines_bot_twin[0],
        lines_bot[1] + lines_bot_twin[1],
        loc="upper left", fontsize=9, framealpha=0.9,
    )
    ax_bot.set_title(
        "System B: Human Society — Energy, Dread & Eudaimonia",
        fontsize=11,
    )
    ax_bot.set_xlabel("Epoch", fontsize=13, fontweight="bold")

    fig.subplots_adjust(top=0.92, bottom=0.05, left=0.07, right=0.93)

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"\n  📊 3-Panel chart saved to: {save_path}")

    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
#  §7  RESILIENCE ANALYSIS — Post-Simulation Diagnostics
# ═══════════════════════════════════════════════════════════════════════════════

def print_resilience_report(result: ThreeBodySimulationResult) -> None:
    """
    Print a detailed resilience report analyzing how the system responded
    to each environmental shock.
    """
    print("\n" + "═" * 72)
    print("  3-BODY COMPLEX SYSTEM — RESILIENCE REPORT")
    print("═" * 72)

    # ── Overall outcome ──────────────────────────────────────────────────
    outcome = "COUPLED HOMEOSTASIS ✦" if result.survived else "SYSTEM COLLAPSE ✗"
    print(f"\n  ▸ Outcome:            {outcome}")
    print(f"  ▸ Epochs completed:   {result.epochs_completed}")
    print(f"  ▸ Machines alive:     {result.machines_alive_final}/{result.machines_alive_initial}")
    print(f"  ▸ Humans burned out:  {result.humans_burnout_final}")
    if result.collapse_epoch is not None:
        print(f"  ▸ Collapse epoch:     {result.collapse_epoch}")

    # ── Nature event summary ─────────────────────────────────────────────
    print(f"\n  ── Nature Events ({result.total_shocks} transitions) ──")
    state_counts: dict[NatureState, int] = {s: 0 for s in NatureState}
    for state in result.nature_state_history:
        state_counts[state] += 1

    total_epochs = len(result.nature_state_history)
    for state in _STATE_ORDER:
        count = state_counts[state]
        pct = (count / total_epochs * 100) if total_epochs > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"    {state.name:25s}: {count:5d} epochs ({pct:5.1f}%) {bar}")

    # ── Shock event log ──────────────────────────────────────────────────
    if result.shock_events:
        print(f"\n  ── State Transition Log (first 20 of {len(result.shock_events)}) ──")
        for i, (epoch, from_state, to_state) in enumerate(result.shock_events[:20]):
            print(f"    Epoch {epoch:5d}: {from_state.name} → {to_state.name}")

    # ── Final system state ───────────────────────────────────────────────
    print("\n  ── Final System State ──")
    if result.entropy_history:
        print(f"    Entropy:       {result.entropy_history[-1]:8.1f}")
    if result.avg_credit_history:
        print(f"    Avg Credit:    {result.avg_credit_history[-1]:8.1f}")
    if result.avg_energy_history:
        print(f"    Avg Energy:    {result.avg_energy_history[-1]:8.1f}")
    if result.avg_dread_history:
        print(f"    Avg Dread:     {result.avg_dread_history[-1]:8.1f}")
    if result.avg_eudaimonia_history:
        print(f"    Avg Eudaimonia:{result.avg_eudaimonia_history[-1]:8.1f}")

    # ── Resilience score ─────────────────────────────────────────────────
    # Heuristic: ratio of time spent in homeostasis vs shock recovery
    if total_epochs > 0 and result.machine_survival_rate_history:
        avg_survival = np.mean(result.machine_survival_rate_history)
        min_survival = np.min(result.machine_survival_rate_history)
        resilience_score = avg_survival * (1.0 - (1.0 - min_survival) * 0.3)
        print(f"\n  ── Resilience Score ──")
        print(f"    Avg Machine Survival:  {avg_survival * 100:.1f}%")
        print(f"    Min Machine Survival:  {min_survival * 100:.1f}%")
        print(f"    Resilience Index:      {resilience_score:.3f}")

    print("\n" + "═" * 72)


# ═══════════════════════════════════════════════════════════════════════════════
#  §8  MAIN — Stress Test Runner
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """
    Main entry point:
      1. Run a 2000-epoch 3-body stress test simulation
      2. Print the resilience report
      3. Generate the 3-panel visualization
    """
    print("=" * 72)
    print("  A2A Protocol — 3-Body Complex System ABM")
    print("  'When Nature speaks, neither Machine nor Man")
    print("   can silence the storm.'")
    print("=" * 72)

    # ── Configure the 3-body simulation ──────────────────────────────────
    constants = ThreeBodyConstants(
        num_machines=20,
        num_humans=10,
        initial_credit=2000.0,
        base_gas_cost=0.5,
        max_epochs=2000,
    )

    # ── Run the simulation ───────────────────────────────────────────────
    print("\n▶ Running 2000-epoch 3-Body Stress Test...")
    print("  (Nature will periodically disrupt the A-B equilibrium)\n")

    sim = ThreeBodySimulation(constants=constants)
    result = sim.run()

    # ── Print resilience report ──────────────────────────────────────────
    print_resilience_report(result)

    # ── Generate visualization ───────────────────────────────────────────
    save_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "assets")
    os.makedirs(save_dir, exist_ok=True)
    chart_path = os.path.join(save_dir, "three_body_resilience.png")

    print("\n▶ Generating 3-Panel Resilience Chart...")
    plot_three_body_resilience(result, save_path=chart_path)

    print("\n" + "=" * 72)
    print("  Simulation complete.")
    print(f"  Chart saved to: {chart_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
