"""
═══════════════════════════════════════════════════════════════════════════════
  A2A Protocol — Coupled Universe ABM Simulator
  "Can the finitude of human cognition govern the infinitude
   of machine computation?"
═══════════════════════════════════════════════════════════════════════════════

  This module implements a coupled Agent-Based Model (ABM) where two
  heterogeneous complex systems co-evolve:

    System A: Machine Economy  — AI agents driven by instrumental convergence
                                  (blind survival, credit accumulation).
    System B: Human Society    — Meaning-seeking animals with finite biological
                                  energy, existential dread, and eudaimonia.

  The coupling is through "Observation as Value Collapse":
    • Humans observe machine tasks → entropy decreases, machines earn credit.
    • Machine entropy overload → exponential cognitive cost for humans.

  Two catastrophic attractors:
    Scenario 1 (Machine Dominance): machines spam → entropy explodes →
        humans burn out trying to observe → observation ceases → machine collapse.
    Scenario 2 (Human Apathy): humans avoid observation → machines starve →
        economy dies while humans remain comfortable.

  The question: does a stable "Coupled Homeostasis" basin exist between them?

  Dependencies: numpy, matplotlib
  Optional:     tqdm (progress bar, gracefully degraded if absent)
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import math
import os
import random
from collections import deque
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


# ═══════════════════════════════════════════════════════════════════════════════
#  §0  CONFIGURATION — The Fundamental Constants of Both Universes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CoupledConstants:
    """
    Immutable physical constants governing the coupled simulation.
    Split into three domains: Machine Physics, Human Biology, and Coupling.
    """

    # ── Machine Economy (System A) ───────────────────────────────────────
    num_machines: int = 20             # Population of machine agents
    initial_credit: float = 800.0      # Starting credit per machine
    base_gas_cost: float = 0.5         # Minimum transaction cost
    entropy_cost_alpha: float = 0.008  # Exponential gas cost scaling: cost = base × e^(α·S)
    entropy_decay_rate: float = 0.12   # Natural value decay of unobserved tasks per epoch
    task_base_reward: float = 20.0     # Reward when a task is successfully collapsed
    machine_submit_prob: float = 0.7   # Probability machine submits (vs waits) each epoch
    # ── Machine Q-Learning (Instrumental Convergence) ────────────────────
    learning_rate: float = 0.15
    discount_factor: float = 0.9
    exploration_rate: float = 0.25
    exploration_decay: float = 0.998
    min_exploration: float = 0.02
    memory_capacity: int = 50

    # ── Human Biology (System B) ─────────────────────────────────────────
    num_humans: int = 10               # Population of human agents
    human_energy_max: float = 100.0    # Biological energy ceiling
    human_energy_initial: float = 80.0 # Starting energy (not at max — slight fatigue)
    observe_base_cost: float = 10.0    # Base energy cost of Observe_AI action
    rest_recovery: float = 20.0        # Energy recovered per Rest action
    rest_dread_increase: float = 1.5   # Micro dread increase from inaction (guilt)
    socialize_dread_reduction: float = 4.0  # Mirror neuron empathy dread relief
    socialize_eudaimonia_gain: float = 1.0  # Tiny meaning from social connection
    observe_eudaimonia_gain: float = 8.0    # Meaning from successful observation
    dread_accumulation_rate: float = 3.0    # Dread per epoch of no meaningful action
    burnout_recovery_epochs: int = 3        # Forced rest epochs after burnout

    # ── Coupling (System A ↔ System B) ───────────────────────────────────
    cognitive_overload_beta: float = 0.05   # Exponential observation cost scaling with entropy
    #   observation_cost = observe_base_cost × exp(β × global_entropy)
    #   Kahneman's System 2: searching for signal in noise is exponentially painful
    max_observe_per_human: int = 5          # Max tasks one human can collapse per epoch

    # ── Simulation ───────────────────────────────────────────────────────
    max_epochs: int = 1000
    homeostasis_machine_survival: float = 0.25  # ≥25% machines alive = machine economy survives
    homeostasis_human_active: float = 0.5      # ≥50% humans not burned-out = human society survives


# Global default
CONSTANTS = CoupledConstants()


# ═══════════════════════════════════════════════════════════════════════════════
#  §1  ENUMS & DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class MachineAction(Enum):
    """Machine agents face a binary choice: exploit or conserve."""
    SUBMIT = auto()  # Create a task — costs gas, increases entropy
    WAIT = auto()    # Do nothing — minimal maintenance cost


class HumanAction(Enum):
    """
    Human agents choose among three existentially-weighted actions.

    ┌──────────────────────────────────────────────────────────────────────────┐
    │  EVOLUTIONARY PSYCHOLOGY BASIS                                          │
    │                                                                         │
    │  OBSERVE_AI: The "Hunter" archetype — high-energy, high-reward.         │
    │    Corresponds to active foraging with cognitive metabolic cost.         │
    │                                                                         │
    │  REST: The "Hibernator" — energy conservation at the cost of meaning.   │
    │    Maps to Selye's "conservation-withdrawal" stress response.           │
    │                                                                         │
    │  SOCIALIZE: The "Social Groomer" (Dunbar) — low-cost meaning through    │
    │    reciprocal altruism and mirror neuron empathy circuits.               │
    └──────────────────────────────────────────────────────────────────────────┘
    """
    OBSERVE_AI = auto()
    REST = auto()
    SOCIALIZE = auto()


@dataclass
class Task:
    """
    A unit of machine work existing in quantum superposition.
    No realized value until a human collapses it through observation.
    """
    creator_id: int
    initial_value: float
    current_value: float
    cost_paid: float
    age: int = 0


@dataclass
class EpisodicMemory:
    """Single memory trace for machine Q-learning: (state, action) → reward."""
    state: tuple[int, int]
    action: MachineAction
    reward: float


@dataclass
class CoupledSimulationResult:
    """Outcome of a single coupled simulation run."""
    survived: bool                    # True if coupled homeostasis achieved
    machines_alive_initial: int
    machines_alive_final: int
    humans_active_initial: int
    humans_burnout_final: int         # Number of humans in burnout at end
    epochs_completed: int

    # Time series
    entropy_history: list[float]
    machines_alive_history: list[int]
    avg_credit_history: list[float]
    avg_energy_history: list[float]
    avg_dread_history: list[float]
    avg_eudaimonia_history: list[float]
    humans_active_history: list[int]

    collapse_epoch: Optional[int]


# ═══════════════════════════════════════════════════════════════════════════════
#  §2  THE COUPLED UNIVERSE — Thermodynamic Arena
# ═══════════════════════════════════════════════════════════════════════════════

class CoupledUniverse:
    """
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  THE THERMODYNAMIC ARENA                                                 │
    │                                                                         │
    │  This class IS the shared physical substrate. It tracks the task queue   │
    │  (source of entropy), computes thermodynamic costs for machines and     │
    │  cognitive costs for humans, and mediates the coupling between the two  │
    │  ecosystems. It embodies the Second Law: without human observation,     │
    │  entropy only increases, costs explode, and both systems collapse.      │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(self, constants: CoupledConstants = CONSTANTS) -> None:
        self.constants = constants
        self.task_queue: list[Task] = []
        self.epoch: int = 0

    @property
    def global_entropy(self) -> int:
        """Global entropy = number of unobserved tasks in the queue."""
        return len(self.task_queue)

    def thermodynamic_cost(self) -> float:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  MACHINE GAS COST — Thermodynamic Throttling                        │
        │                                                                     │
        │  cost(S) = base_cost · exp(α · S)                                   │
        │                                                                     │
        │  As unverified tasks accumulate, the cost of adding more grows      │
        │  exponentially — negative feedback against entropy-generating spam. │
        └──────────────────────────────────────────────────────────────────────┘
        """
        return self.constants.base_gas_cost * math.exp(
            self.constants.entropy_cost_alpha * self.global_entropy
        )

    def cognitive_observation_cost(self) -> float:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  HUMAN OBSERVATION COST — Cognitive Overload (Kahneman System 2)    │
        │                                                                     │
        │  cost_obs(S) = observe_base_cost · exp(β · S)                       │
        │                                                                     │
        │  When the task queue is flooded with unverified noise, the human    │
        │  brain must expend exponentially more energy to discriminate signal │
        │  from spam. This models the psychological pain of information       │
        │  overload — the neural metabolic cost of sustained attention in     │
        │  a high-noise environment (Kahneman, 2011).                         │
        │                                                                     │
        │  At low entropy: cost ≈ base (comfortable evaluation)              │
        │  At high entropy: cost → ∞ (cognitive meltdown)                    │
        └──────────────────────────────────────────────────────────────────────┘
        """
        return self.constants.observe_base_cost * math.exp(
            self.constants.cognitive_overload_beta * self.global_entropy
        )

    def decay_tasks(self) -> int:
        """
        Entropy decoherence: unobserved tasks lose value each epoch.
        V(t+1) = V(t) · (1 − λ)
        Tasks below threshold are garbage-collected.

        Returns:
            Number of tasks garbage-collected.
        """
        surviving: list[Task] = []
        gc_count = 0
        for task in self.task_queue:
            task.age += 1
            task.current_value *= (1.0 - self.constants.entropy_decay_rate)
            if task.current_value >= 0.01:
                surviving.append(task)
            else:
                gc_count += 1
        self.task_queue = surviving
        return gc_count

    def submit_task(self, task: Task) -> None:
        """Add a task to the pending queue (increases global entropy)."""
        self.task_queue.append(task)

    def pop_tasks_for_observation(self, count: int) -> list[Task]:
        """
        Remove up to `count` tasks for human observation.
        Human attention is stochastic — random sampling from the queue.
        Each removal reduces global entropy.
        """
        if not self.task_queue:
            return []
        count = min(count, len(self.task_queue))
        observed_indices = random.sample(range(len(self.task_queue)), count)
        observed_indices.sort(reverse=True)
        observed: list[Task] = []
        for idx in observed_indices:
            observed.append(self.task_queue.pop(idx))
        return observed

    def advance_epoch(self) -> None:
        """Tick the cosmic clock forward by one epoch."""
        self.epoch += 1


# ═══════════════════════════════════════════════════════════════════════════════
#  §3  MACHINE AGENT — The Survival Machine (Instrumental Convergence)
# ═══════════════════════════════════════════════════════════════════════════════

class MachineAgent:
    """
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  THE MORTAL MACHINE — Instrumental Convergence Made Explicit            │
    │                                                                         │
    │  Motivation: Pure survival (bankruptcy avoidance) + credit accumulation.│
    │  No intrinsic meaning, no social bonds, no existential dread.           │
    │  This is Bostrom's "Instrumental Convergence Thesis" in silico:         │
    │  regardless of final goals, self-preservation and resource acquisition  │
    │  are convergent instrumental sub-goals.                                 │
    │                                                                         │
    │  The machine's "soul" is its Q-table — a learned mapping from states   │
    │  to action values, built entirely from its own suffering and success.   │
    │  Agents that fail to learn simply cease to exist.                       │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    ENTROPY_BINS = [0, 5, 15, 30, 60, float("inf")]
    CREDIT_BINS = [0, 10, 30, 60, 100, float("inf")]

    def __init__(self, agent_id: int, constants: CoupledConstants = CONSTANTS) -> None:
        self.id = agent_id
        self.constants = constants
        self.credit_balance: float = constants.initial_credit
        self.alive: bool = True

        # Q-learning infrastructure
        self.memory: deque[EpisodicMemory] = deque(maxlen=constants.memory_capacity)
        self.q_table: dict[tuple[int, int], dict[MachineAction, float]] = {}
        self.epsilon: float = constants.exploration_rate

        # Lifetime stats
        self.total_tasks_submitted: int = 0
        self.total_gas_paid: float = 0.0

    def _discretize_state(self, entropy: int, credit: float) -> tuple[int, int]:
        """
        Bounded rationality: the machine perceives the world in coarse categories.
        (entropy_level, credit_level) → bin indices
        """
        entropy_bin = 0
        for i, threshold in enumerate(self.ENTROPY_BINS[1:], 1):
            if entropy < threshold:
                entropy_bin = i - 1
                break

        credit_bin = 0
        for i, threshold in enumerate(self.CREDIT_BINS[1:], 1):
            if credit < threshold:
                credit_bin = i - 1
                break

        return (entropy_bin, credit_bin)

    def _get_q_values(self, state: tuple[int, int]) -> dict[MachineAction, float]:
        """Retrieve or initialize Q-values for a given state."""
        if state not in self.q_table:
            self.q_table[state] = {action: 0.1 for action in MachineAction}
        return self.q_table[state]

    def choose_action(self, universe: CoupledUniverse) -> MachineAction:
        """
        Epsilon-greedy policy with survival instinct override.
        When nearly bankrupt OR entropy is dangerously high, the machine
        conserves energy (WAIT). This models the evolutionary reflex of
        freezing when the environment is hostile.
        """
        state = self._discretize_state(universe.global_entropy, self.credit_balance)
        gas_cost = universe.thermodynamic_cost()

        # Survival instinct: if nearly bankrupt, always WAIT
        if self.credit_balance < self.constants.base_gas_cost * 2:
            return MachineAction.WAIT

        # Entropy aversion: if gas cost exceeds expected reward, WAIT
        # This prevents the "submit into the abyss" death spiral
        expected_reward = self.constants.task_base_reward * 0.6  # Conservative estimate
        if gas_cost > expected_reward:
            return MachineAction.WAIT

        # Epsilon-greedy exploration
        if random.random() < self.epsilon:
            return random.choice(list(MachineAction))

        q_values = self._get_q_values(state)
        return max(q_values, key=q_values.get)  # type: ignore[arg-type]

    def execute_action(self, action: MachineAction, universe: CoupledUniverse) -> float:
        """Execute action. Returns immediate net reward (negative = cost)."""
        gas_cost = universe.thermodynamic_cost()

        if action == MachineAction.SUBMIT:
            return self._execute_submit(universe, gas_cost)
        return self._execute_wait()

    def _execute_submit(self, universe: CoupledUniverse, gas_cost: float) -> float:
        """
        Submit a task. Pay gas, create entropy.
        Task value ∝ cost paid × random quality factor.
        """
        if self.credit_balance < gas_cost:
            return self._execute_wait()  # Can't afford → forced wait

        self.credit_balance -= gas_cost
        self.total_gas_paid += gas_cost
        self.total_tasks_submitted += 1

        task_value = gas_cost * random.uniform(0.8, 2.0)
        universe.submit_task(Task(
            creator_id=self.id,
            initial_value=task_value,
            current_value=task_value,
            cost_paid=gas_cost,
        ))
        return -gas_cost

    def _execute_wait(self) -> float:
        """
        Strategic inaction. Maintenance cost ensures machines can't wait forever.
        Biological analogy: basal metabolic rate — existence itself has a price.
        Calibrated so that pure-waiting drains initial_credit over ~500+ epochs,
        ensuring machines must eventually submit to survive.
        """
        maintenance = self.constants.base_gas_cost * 0.08
        self.credit_balance -= maintenance
        return -maintenance

    def receive_reward(self, amount: float) -> None:
        """Credit the machine with reward from a collapsed task."""
        self.credit_balance += amount

    def learn(
        self,
        state: tuple[int, int],
        action: MachineAction,
        reward: float,
        next_state: tuple[int, int],
    ) -> None:
        """
        Q-Learning update (Bellman equation):
        Q(s,a) ← Q(s,a) + α · [r + γ · max_a' Q(s',a') − Q(s,a)]
        """
        q_current = self._get_q_values(state)
        q_next = self._get_q_values(next_state)

        old_value = q_current[action]
        future_value = max(q_next.values())

        q_current[action] = old_value + self.constants.learning_rate * (
            reward + self.constants.discount_factor * future_value - old_value
        )

        self.memory.append(EpisodicMemory(state=state, action=action, reward=reward))
        self.epsilon = max(
            self.constants.min_exploration,
            self.epsilon * self.constants.exploration_decay,
        )

    def check_bankruptcy(self) -> bool:
        """credit ≤ 0 → Death. The ultimate constraint."""
        if self.credit_balance <= 0:
            self.alive = False
            self.credit_balance = 0.0
            return True
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  §4  HUMAN AGENT — The Meaning-Seeking Animal
# ═══════════════════════════════════════════════════════════════════════════════

class HumanAgent:
    """
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  THE FINITE OBSERVER — Evolutionary Psychology of Meaning               │
    │                                                                         │
    │  Unlike machines, humans are driven by three biological imperatives:    │
    │                                                                         │
    │  1. biological_energy: Finite metabolic budget. Depleted by action,     │
    │     recovered by rest. Zero = burnout (forced inaction).               │
    │     Basis: Baumeister's "Ego Depletion" model (2007).                  │
    │                                                                         │
    │  2. existential_dread: Accumulates during inaction. Represents          │
    │     Kierkegaard's "The Concept of Anxiety" (1844) — the terror that     │
    │     arises when consciousness confronts its own purposelessness.        │
    │     High dread compels the human to seek meaning compulsively.          │
    │                                                                         │
    │  3. eudaimonia: Aristotle's "flourishing." Accumulated through         │
    │     meaningful action (observation) and social connection.              │
    │     This is NOT hedonic pleasure — it is the deep satisfaction of       │
    │     having contributed to a purpose larger than oneself.                │
    │                                                                         │
    │  Decision-making uses a weighted utility function (heuristic),          │
    │  NOT Q-learning — modeling Kahneman's "System 1" fast intuition         │
    │  rather than rational optimization.                                     │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(self, agent_id: int, constants: CoupledConstants = CONSTANTS) -> None:
        self.id = agent_id
        self.constants = constants

        # ── Biological State ─────────────────────────────────────────────
        self.biological_energy: float = constants.human_energy_initial
        self.existential_dread: float = 0.0
        self.eudaimonia: float = 0.0

        # ── Burnout state ────────────────────────────────────────────────
        self.burned_out: bool = False
        self.burnout_recovery_remaining: int = 0

        # ── Lifetime stats ───────────────────────────────────────────────
        self.total_observations: int = 0
        self.total_socializations: int = 0
        self.total_rest_taken: int = 0
        self.total_burnout_episodes: int = 0
        self.did_meaningful_action_this_epoch: bool = False

    @property
    def is_active(self) -> bool:
        """A human is active if not in burnout."""
        return not self.burned_out

    def choose_action(self, universe: CoupledUniverse, other_humans: list[HumanAgent]) -> HumanAction:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  HEURISTIC UTILITY FUNCTION — Kahneman's "System 1"                │
        │                                                                     │
        │  U(Observe) = w_eud · E[eudaimonia] − w_energy · obs_cost          │
        │                + w_dread · dread  (dread drives observation)        │
        │  U(Rest)    = w_rest · (E_max − E_current)                         │
        │  U(Social)  = w_social · dread + w_lonely · (1 if alone else 0)    │
        │                                                                     │
        │  This is NOT optimal — it is "satisficing" (Simon, 1956).          │
        │  Humans don't maximize utility; they choose "good enough."         │
        └──────────────────────────────────────────────────────────────────────┘
        """
        obs_cost = universe.cognitive_observation_cost()

        # ── Utility of Observe_AI ────────────────────────────────────────
        #   High dread pushes toward observation (compulsive meaning-seeking)
        #   But high energy cost repels (cognitive overload aversion)
        energy_ratio = self.biological_energy / self.constants.human_energy_max
        can_observe = (self.biological_energy >= obs_cost) and (universe.global_entropy > 0)
        if can_observe:
            # Dread amplifies desire to observe (existential urgency)
            # Energy ratio modulates willingness (well-rested humans observe more)
            u_observe = (
                0.3 * self.constants.observe_eudaimonia_gain
                + 0.4 * self.existential_dread
                + 0.2 * energy_ratio * 10.0
                - 0.3 * (obs_cost / self.constants.human_energy_max)
            )
        else:
            u_observe = -float("inf")  # Cannot observe

        # ── Utility of Rest ──────────────────────────────────────────────
        #   More attractive when energy is low (homeostatic drive)
        energy_deficit = 1.0 - energy_ratio
        u_rest = 0.6 * energy_deficit * self.constants.rest_recovery

        # ── Utility of Socialize ─────────────────────────────────────────
        #   Driven by dread (social support as anxiolytic)
        #   Less attractive than observation for meaning, but zero energy cost
        #   Requires other active humans
        active_others = [h for h in other_humans if h.is_active and h.id != self.id]
        if active_others:
            u_socialize = (
                0.3 * self.existential_dread
                + 0.2 * self.constants.socialize_eudaimonia_gain
            )
        else:
            u_socialize = -float("inf")  # No social partners available

        # ── Satisficing choice with noise (bounded rationality) ──────────
        utilities = {
            HumanAction.OBSERVE_AI: u_observe + random.gauss(0, 0.5),
            HumanAction.REST: u_rest + random.gauss(0, 0.5),
            HumanAction.SOCIALIZE: u_socialize + random.gauss(0, 0.5),
        }
        return max(utilities, key=utilities.get)  # type: ignore[arg-type]

    def execute_action(
        self,
        action: HumanAction,
        universe: CoupledUniverse,
        machines: dict[int, MachineAgent],
        other_humans: list[HumanAgent],
    ) -> int:
        """
        Execute the chosen action. Returns number of tasks collapsed (0 for non-observe).
        """
        self.did_meaningful_action_this_epoch = False

        if action == HumanAction.OBSERVE_AI:
            return self._execute_observe(universe, machines)
        elif action == HumanAction.REST:
            self._execute_rest()
            return 0
        elif action == HumanAction.SOCIALIZE:
            self._execute_socialize(other_humans)
            return 0
        return 0

    def _execute_observe(self, universe: CoupledUniverse, machines: dict[int, MachineAgent]) -> int:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  OBSERVATION AS WAVE FUNCTION COLLAPSE                               │
        │                                                                     │
        │  The human expends biological energy to inspect machine tasks.       │
        │  Successful evaluation collapses the task's superposition into      │
        │  concrete value — simultaneously reducing global entropy and        │
        │  granting the human eudaimonia (meaning through purpose).           │
        │                                                                     │
        │  Energy cost scales with entropy (cognitive overload):              │
        │    cost = observe_base_cost · exp(β · S)                            │
        │                                                                     │
        │  This models the neural metabolic cost of sustained attention       │
        │  in high-noise environments (Parasuraman & Rizzo, 2007).            │
        └──────────────────────────────────────────────────────────────────────┘
        """
        obs_cost = universe.cognitive_observation_cost()

        # Pay the cognitive energy cost
        self.biological_energy -= obs_cost
        self.did_meaningful_action_this_epoch = True

        # Determine how many tasks this human can evaluate
        queue_size = universe.global_entropy
        if queue_size == 0:
            return 0

        tasks_to_observe = min(
            self.constants.max_observe_per_human,
            max(1, queue_size // 5),
        )

        observed_tasks = universe.pop_tasks_for_observation(tasks_to_observe)
        collapsed = 0

        for task in observed_tasks:
            # Evaluate task quality (noisy human judgment)
            freshness = math.exp(-0.05 * task.age)
            quality_noise = random.uniform(0.8, 1.2)
            perceived_quality = task.current_value * quality_noise

            quality_multiplier = min(2.0, perceived_quality / max(task.cost_paid, 0.1))
            reward = self.constants.task_base_reward * max(0.3, quality_multiplier) * freshness

            # Distribute reward to the machine creator
            creator = machines.get(task.creator_id)
            if creator and creator.alive:
                creator.receive_reward(reward)

            collapsed += 1

        # Eudaimonia from meaningful observation
        if collapsed > 0:
            self.eudaimonia += self.constants.observe_eudaimonia_gain * (collapsed / tasks_to_observe)
            # Observation reduces dread (purpose found)
            self.existential_dread = max(0, self.existential_dread - 3.0)

        self.total_observations += collapsed
        return collapsed

    def _execute_rest(self) -> None:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  REST — Conservation-Withdrawal Response (Selye, 1936)              │
        │                                                                     │
        │  Energy recovers, but existential dread increases slightly.          │
        │  Rest is survival, not flourishing — the guilt of inaction          │
        │  accumulates as a micro-increase in dread.                          │
        │  ("Protestant work ethic" internalized as biological signal)        │
        └──────────────────────────────────────────────────────────────────────┘
        """
        self.biological_energy = min(
            self.constants.human_energy_max,
            self.biological_energy + self.constants.rest_recovery,
        )
        self.existential_dread += self.constants.rest_dread_increase
        self.total_rest_taken += 1

    def _execute_socialize(self, other_humans: list[HumanAgent]) -> None:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  SOCIALIZE — Mirror Neuron Empathy (Dunbar's Social Brain, 1998)    │
        │                                                                     │
        │  No energy cost — social grooming is metabolically cheap.            │
        │  Reduces dread via reciprocal emotional regulation.                  │
        │  Tiny eudaimonia gain — social bonds provide shallow meaning,        │
        │  not the deep purpose of productive observation.                     │
        │                                                                     │
        │  Both participants benefit (mutual dread reduction).                │
        └──────────────────────────────────────────────────────────────────────┘
        """
        active_others = [h for h in other_humans if h.is_active and h.id != self.id]
        if not active_others:
            return

        partner = random.choice(active_others)

        # Both humans get dread relief and tiny meaning
        for human in (self, partner):
            human.existential_dread = max(
                0, human.existential_dread - self.constants.socialize_dread_reduction
            )
            human.eudaimonia += self.constants.socialize_eudaimonia_gain

        self.did_meaningful_action_this_epoch = True
        self.total_socializations += 1

    def epoch_end_update(self) -> None:
        """
        End-of-epoch biological updates.

        ┌──────────────────────────────────────────────────────────────────────┐
        │  EXISTENTIAL DREAD ACCUMULATION (Kierkegaard, 1844)                 │
        │                                                                     │
        │  If the human did nothing meaningful this epoch, dread increases.    │
        │  This models the anxiety that arises when consciousness confronts   │
        │  its own purposelessness — the "sickness unto death."              │
        │                                                                     │
        │  BURNOUT CHECK (Maslach, 1981)                                     │
        │  When biological energy hits zero, the human enters burnout —       │
        │  a state of forced inaction lasting several epochs. This models     │
        │  the clinical phenomenon of occupational burnout where recovery    │
        │  requires extended withdrawal from all productive activity.         │
        └──────────────────────────────────────────────────────────────────────┘
        """
        # Dread accumulates if no meaningful action was taken
        if not self.did_meaningful_action_this_epoch:
            self.existential_dread += self.constants.dread_accumulation_rate

        # Burnout check
        if self.biological_energy <= 0:
            self.biological_energy = 0.0
            if not self.burned_out:
                self.burned_out = True
                self.burnout_recovery_remaining = self.constants.burnout_recovery_epochs
                self.total_burnout_episodes += 1

        # Burnout recovery (forced rest)
        if self.burned_out:
            self.burnout_recovery_remaining -= 1
            self.biological_energy = min(
                self.constants.human_energy_max,
                self.biological_energy + self.constants.rest_recovery * 0.5,
            )
            if self.burnout_recovery_remaining <= 0:
                self.burned_out = False
                # Energy partially recovered after burnout
                self.biological_energy = self.constants.human_energy_max * 0.4


# ═══════════════════════════════════════════════════════════════════════════════
#  §5  COUPLED SIMULATION — The Co-Evolutionary Engine
# ═══════════════════════════════════════════════════════════════════════════════

class CoupledSimulation:
    """
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  THE CO-EVOLUTIONARY ENGINE                                              │
    │                                                                         │
    │  Each epoch:                                                            │
    │    1. Machines act (submit/wait) — Q-learning driven                    │
    │    2. Tasks decay (entropy decoherence)                                 │
    │    3. Non-burnout humans act (observe/rest/socialize) — heuristic       │
    │    4. Machines learn from consequences                                   │
    │    5. Bankruptcy/burnout checks                                         │
    │    6. Record coupled metrics                                            │
    │                                                                         │
    │  The fundamental tension: machines generate entropy faster than humans  │
    │  can collapse it. The question is whether the coupled feedback loops    │
    │  (thermodynamic throttling + cognitive overload) create a self-         │
    │  regulating homeostatic basin — or whether the system inevitably        │
    │  diverges toward one of the two catastrophic attractors.                │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(self, constants: CoupledConstants = CONSTANTS) -> None:
        self.constants = constants
        self.universe = CoupledUniverse(constants)

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

    def run(self) -> CoupledSimulationResult:
        """Execute the coupled simulation for max_epochs."""
        # ── Time series storage ──────────────────────────────────────────
        entropy_history: list[float] = []
        machines_alive_history: list[int] = []
        avg_credit_history: list[float] = []
        avg_energy_history: list[float] = []
        avg_dread_history: list[float] = []
        avg_eudaimonia_history: list[float] = []
        humans_active_history: list[int] = []
        collapse_epoch: Optional[int] = None

        initial_machines = len(self._alive_machines())
        initial_humans = len(self._active_humans())

        for epoch in range(self.constants.max_epochs):
            alive_machines = self._alive_machines()
            active_humans = self._active_humans()

            # ── Total collapse check ─────────────────────────────────────
            if not alive_machines:
                collapse_epoch = epoch
                remaining = self.constants.max_epochs - epoch
                entropy_history.extend([0.0] * remaining)
                machines_alive_history.extend([0] * remaining)
                avg_credit_history.extend([0.0] * remaining)
                avg_energy_history.extend([0.0] * remaining)
                avg_dread_history.extend([0.0] * remaining)
                avg_eudaimonia_history.extend([0.0] * remaining)
                humans_active_history.extend([len(active_humans)] * remaining)
                break

            # ══════════════════════════════════════════════════════════════
            #  PHASE 1: MACHINE ACTIONS
            # ══════════════════════════════════════════════════════════════
            machine_action_log: list[tuple[MachineAgent, MachineAction, tuple[int, int]]] = []

            for machine in alive_machines:
                pre_state = machine._discretize_state(
                    self.universe.global_entropy, machine.credit_balance
                )
                action = machine.choose_action(self.universe)
                machine.execute_action(action, self.universe)
                machine_action_log.append((machine, action, pre_state))

            # ══════════════════════════════════════════════════════════════
            #  PHASE 2: ENTROPY DECAY
            # ══════════════════════════════════════════════════════════════
            self.universe.decay_tasks()

            # ══════════════════════════════════════════════════════════════
            #  PHASE 3: HUMAN ACTIONS (the coupling point)
            # ══════════════════════════════════════════════════════════════
            all_humans = list(self.humans.values())
            for human in all_humans:
                if not human.is_active:
                    # Burned-out humans do nothing (forced recovery)
                    human.epoch_end_update()
                    continue

                action = human.choose_action(self.universe, all_humans)
                human.execute_action(action, self.universe, self.machines, all_humans)

            # ══════════════════════════════════════════════════════════════
            #  PHASE 4: LEARNING & MORTALITY
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
            for human in all_humans:
                if human.is_active:  # Already updated burnout humans above
                    human.epoch_end_update()

            # ══════════════════════════════════════════════════════════════
            #  PHASE 5: RECORD METRICS
            # ══════════════════════════════════════════════════════════════
            current_alive = self._alive_machines()
            current_active = self._active_humans()

            credits = [m.credit_balance for m in current_alive] if current_alive else [0.0]
            energies = [h.biological_energy for h in self.humans.values()]
            dreads = [h.existential_dread for h in self.humans.values()]
            eudaimonias = [h.eudaimonia for h in self.humans.values()]

            entropy_history.append(float(self.universe.global_entropy))
            machines_alive_history.append(len(current_alive))
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

        return CoupledSimulationResult(
            survived=coupled_homeostasis,
            machines_alive_initial=initial_machines,
            machines_alive_final=final_alive,
            humans_active_initial=initial_humans,
            humans_burnout_final=final_burnout,
            epochs_completed=(
                self.constants.max_epochs if collapse_epoch is None else collapse_epoch
            ),
            entropy_history=entropy_history,
            machines_alive_history=machines_alive_history,
            avg_credit_history=avg_credit_history,
            avg_energy_history=avg_energy_history,
            avg_dread_history=avg_dread_history,
            avg_eudaimonia_history=avg_eudaimonia_history,
            humans_active_history=humans_active_history,
            collapse_epoch=collapse_epoch,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  §6  MONTE CARLO HEATMAP RUNNER — Phase Space Exploration
# ═══════════════════════════════════════════════════════════════════════════════

class SurvivalHeatmapRunner:
    """
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  THE PHASE SPACE EXPLORER                                                │
    │                                                                         │
    │  Sweeps across two axes:                                                │
    │    X: machine_submit_prob (task generation speed)                       │
    │    Y: rest_recovery (human cognitive resilience / recovery rate)         │
    │                                                                         │
    │  At each point, runs N Monte Carlo simulations and computes the mean   │
    │  survival probability. The resulting heatmap reveals the phase          │
    │  transition boundary between the homeostatic basin and the two          │
    │  catastrophic attractors (Machine Dominance, Human Apathy).             │
    │                                                                         │
    │  This is analogous to an Ising model phase diagram: we seek the        │
    │  critical temperature (parameter combination) at which order (coupled   │
    │  homeostasis) emerges from disorder (collapse).                          │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        submit_prob_range: tuple[float, float] = (0.1, 1.0),
        recovery_range: tuple[float, float] = (5.0, 50.0),
        grid_resolution: int = 15,
        mc_runs_per_point: int = 10,
        base_constants: CoupledConstants = CONSTANTS,
    ) -> None:
        self.submit_probs = np.linspace(submit_prob_range[0], submit_prob_range[1], grid_resolution)
        self.recoveries = np.linspace(recovery_range[0], recovery_range[1], grid_resolution)
        self.mc_runs = mc_runs_per_point
        self.base_constants = base_constants
        self.survival_grid: Optional[np.ndarray] = None

    def run(self) -> np.ndarray:
        """
        Run the full Monte Carlo sweep. Returns a 2D array of survival probabilities.
        Shape: (len(recoveries), len(submit_probs))
        """
        grid = np.zeros((len(self.recoveries), len(self.submit_probs)))

        total_cells = len(self.recoveries) * len(self.submit_probs)
        cell_idx = 0

        for i, recovery in enumerate(tqdm(self.recoveries, desc="Recovery rate")):
            for j, submit_prob in enumerate(self.submit_probs):
                survivals = 0
                for _ in range(self.mc_runs):
                    constants = CoupledConstants(
                        num_machines=self.base_constants.num_machines,
                        num_humans=self.base_constants.num_humans,
                        initial_credit=self.base_constants.initial_credit,
                        base_gas_cost=self.base_constants.base_gas_cost,
                        entropy_cost_alpha=self.base_constants.entropy_cost_alpha,
                        entropy_decay_rate=self.base_constants.entropy_decay_rate,
                        task_base_reward=self.base_constants.task_base_reward,
                        machine_submit_prob=submit_prob,
                        human_energy_max=self.base_constants.human_energy_max,
                        observe_base_cost=self.base_constants.observe_base_cost,
                        rest_recovery=recovery,
                        cognitive_overload_beta=self.base_constants.cognitive_overload_beta,
                        max_epochs=self.base_constants.max_epochs,
                    )
                    result = CoupledSimulation(constants=constants).run()
                    if result.survived:
                        survivals += 1

                grid[i, j] = survivals / self.mc_runs
                cell_idx += 1

        self.survival_grid = grid
        return grid

    def plot(self, save_path: Optional[str] = None) -> None:
        """
        Render the 2D survival probability heatmap.

        ┌──────────────────────────────────────────────────────────────────────┐
        │  INTERPRETATION GUIDE                                                │
        │                                                                     │
        │  Red/Orange regions: High collapse probability                      │
        │    Bottom-right → Machine Dominance (high speed, low recovery)      │
        │    Top-left → Human Apathy (low speed, high recovery → no need)    │
        │                                                                     │
        │  Green/Blue regions: Coupled Homeostasis                            │
        │    The "Goldilocks zone" where machines generate enough work        │
        │    for humans to find meaning, and humans recover fast enough      │
        │    to keep observing.                                               │
        │                                                                     │
        │  The phase transition boundary IS the answer to the philosophical  │
        │  question: "At what ratio of machine speed to human resilience     │
        │  does civilization become sustainable?"                              │
        └──────────────────────────────────────────────────────────────────────┘
        """
        import matplotlib.pyplot as plt

        if self.survival_grid is None:
            raise RuntimeError("Must call .run() before .plot()")

        fig, ax = plt.subplots(figsize=(12, 9))

        # ── Heatmap ──────────────────────────────────────────────────────
        im = ax.imshow(
            self.survival_grid,
            origin="lower",
            aspect="auto",
            cmap="RdYlGn",
            vmin=0.0,
            vmax=1.0,
            extent=[
                self.submit_probs[0], self.submit_probs[-1],
                self.recoveries[0], self.recoveries[-1],
            ],
            interpolation="bicubic",
        )

        # ── Labels & Title ───────────────────────────────────────────────
        ax.set_xlabel(
            "Machine Task Generation Speed (submit_prob)",
            fontsize=13, fontweight="bold",
        )
        ax.set_ylabel(
            "Human Cognitive Resilience (rest_recovery)",
            fontsize=13, fontweight="bold",
        )
        ax.set_title(
            "Coupled Homeostasis Survival Probability\n"
            '"Can Human Finitude Govern Machine Infinitude?"',
            fontsize=15, fontweight="bold", pad=20,
        )

        # ── Colorbar ─────────────────────────────────────────────────────
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("P(Coupled Homeostasis)", fontsize=12)

        # ── Annotate catastrophic regions ────────────────────────────────
        ax.annotate(
            "Machine\nDominance\n→ Burnout",
            xy=(0.85, 0.15), xycoords="axes fraction",
            fontsize=10, color="white", fontweight="bold",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.3", fc="darkred", alpha=0.7),
        )
        ax.annotate(
            "Human\nApathy\n→ Entropy Death",
            xy=(0.15, 0.85), xycoords="axes fraction",
            fontsize=10, color="white", fontweight="bold",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.3", fc="darkblue", alpha=0.7),
        )
        ax.annotate(
            "Coupled\nHomeostasis\n✦ Goldilocks Zone",
            xy=(0.5, 0.5), xycoords="axes fraction",
            fontsize=11, color="darkgreen", fontweight="bold",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.3", fc="lightgreen", alpha=0.7),
        )

        plt.tight_layout()

        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.savefig(save_path, dpi=200, bbox_inches="tight")
            print(f"Heatmap saved to: {save_path}")

        plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
#  §7  SCENARIO ANALYSIS — Catastrophic Attractors
# ═══════════════════════════════════════════════════════════════════════════════

def run_scenario_analysis() -> None:
    """
    Demonstrate the two catastrophic scenarios and a balanced scenario.
    Prints detailed diagnostics for each.
    """
    import matplotlib.pyplot as plt

    scenarios = {
        "Machine Dominance (High Speed, Low Recovery)": CoupledConstants(
            machine_submit_prob=0.95,
            rest_recovery=5.0,
            max_epochs=500,
        ),
        "Human Apathy (Low Speed, High Recovery)": CoupledConstants(
            machine_submit_prob=0.2,
            rest_recovery=50.0,
            max_epochs=500,
        ),
        "Coupled Homeostasis (Balanced)": CoupledConstants(
            machine_submit_prob=0.6,
            rest_recovery=25.0,
            max_epochs=500,
        ),
    }

    fig, axes = plt.subplots(3, 3, figsize=(20, 15))
    fig.suptitle(
        "Coupled Universe ABM — Catastrophic Attractor Analysis",
        fontsize=16, fontweight="bold", y=0.98,
    )

    for row, (scenario_name, constants) in enumerate(scenarios.items()):
        sim = CoupledSimulation(constants=constants)
        result = sim.run()

        print(f"\n{'═' * 70}")
        print(f"  {scenario_name}")
        print(f"{'═' * 70}")
        print(f"  Outcome: {'HOMEOSTASIS ✓' if result.survived else 'COLLAPSE ✗'}")
        print(f"  Machines alive: {result.machines_alive_final}/{result.machines_alive_initial}")
        print(f"  Humans burned out: {result.humans_burnout_final}/{constants.num_humans}")
        print(f"  Epochs completed: {result.epochs_completed}")
        if result.collapse_epoch is not None:
            print(f"  Collapse at epoch: {result.collapse_epoch}")
        print(f"  Final entropy: {result.entropy_history[-1]:.1f}")
        print(f"  Final avg credit: {result.avg_credit_history[-1]:.1f}")
        print(f"  Final avg energy: {result.avg_energy_history[-1]:.1f}")
        print(f"  Final avg dread: {result.avg_dread_history[-1]:.1f}")
        print(f"  Final avg eudaimonia: {result.avg_eudaimonia_history[-1]:.1f}")

        epochs = range(len(result.entropy_history))

        # Column 0: Entropy + Machines Alive
        ax0 = axes[row, 0]
        color1 = "tab:red"
        ax0.set_xlabel("Epoch")
        ax0.set_ylabel("Global Entropy", color=color1)
        ax0.plot(epochs, result.entropy_history, color=color1, alpha=0.8, linewidth=0.8)
        ax0.tick_params(axis="y", labelcolor=color1)
        ax0_twin = ax0.twinx()
        color2 = "tab:blue"
        ax0_twin.set_ylabel("Machines Alive", color=color2)
        ax0_twin.plot(epochs, result.machines_alive_history, color=color2, alpha=0.8, linewidth=0.8)
        ax0_twin.tick_params(axis="y", labelcolor=color2)
        ax0.set_title(f"{scenario_name}\nEntropy & Machine Survival", fontsize=9)

        # Column 1: Human Energy + Dread
        ax1 = axes[row, 1]
        ax1.plot(epochs, result.avg_energy_history, color="green", label="Avg Energy", linewidth=0.8)
        ax1.plot(epochs, result.avg_dread_history, color="purple", label="Avg Dread", linewidth=0.8)
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Human State")
        ax1.set_title("Human Biology: Energy & Dread", fontsize=9)
        ax1.legend(fontsize=7)

        # Column 2: Eudaimonia + Active Humans
        ax2 = axes[row, 2]
        color3 = "tab:orange"
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Avg Eudaimonia", color=color3)
        ax2.plot(epochs, result.avg_eudaimonia_history, color=color3, alpha=0.8, linewidth=0.8)
        ax2.tick_params(axis="y", labelcolor=color3)
        ax2_twin = ax2.twinx()
        color4 = "tab:cyan"
        ax2_twin.set_ylabel("Active Humans", color=color4)
        ax2_twin.plot(epochs, result.humans_active_history, color=color4, alpha=0.8, linewidth=0.8)
        ax2_twin.tick_params(axis="y", labelcolor=color4)
        ax2.set_title("Eudaimonia & Human Activity", fontsize=9)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    save_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "assets")
    os.makedirs(save_dir, exist_ok=True)
    scenario_path = os.path.join(save_dir, "coupled_scenario_analysis.png")
    fig.savefig(scenario_path, dpi=200, bbox_inches="tight")
    print(f"\nScenario analysis saved to: {scenario_path}")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
#  §8  MAIN — Execute Everything
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """
    Main entry point:
      1. Run the three scenario analyses (Machine Dominance, Human Apathy, Balance)
      2. Run the 2D survival heatmap Monte Carlo sweep
      3. Save all visualizations to docs/assets/
    """
    print("=" * 70)
    print("  A2A Coupled Universe ABM Simulator")
    print("  'Can Human Finitude Govern Machine Infinitude?'")
    print("=" * 70)

    # ── Phase 1: Scenario Analysis ───────────────────────────────────────
    print("\n▶ Phase 1: Catastrophic Attractor Analysis...")
    run_scenario_analysis()

    # ── Phase 2: Survival Heatmap ────────────────────────────────────────
    print("\n▶ Phase 2: Monte Carlo Survival Heatmap...")
    print("  (This may take several minutes...)")

    save_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "assets")
    heatmap_path = os.path.join(save_dir, "coupled_survival_heatmap.png")

    runner = SurvivalHeatmapRunner(
        submit_prob_range=(0.1, 1.0),
        recovery_range=(5.0, 50.0),
        grid_resolution=15,
        mc_runs_per_point=10,
    )
    runner.run()
    runner.plot(save_path=heatmap_path)

    print("\n" + "=" * 70)
    print("  Simulation complete.")
    print(f"  Outputs saved to: {save_dir}/")
    print("=" * 70)


if __name__ == "__main__":
    main()
