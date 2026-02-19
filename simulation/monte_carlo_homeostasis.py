"""
═══════════════════════════════════════════════════════════════════════════════
  A2A Protocol — Monte Carlo Homeostasis Simulator
  "Can a universe of autonomous machines sustain itself
   without devouring its own foundations?"
═══════════════════════════════════════════════════════════════════════════════

  This module implements a multi-agent Monte Carlo simulation to determine the
  probability that an autonomous AI economy reaches dynamic homeostasis (stable
  equilibrium) rather than total collapse (all agents bankrupt).

  The simulation encodes three "cosmic laws":
    1. Quantum-Humanistic Value   — Tasks have no value until a Human Observer
                                     collapses their superposition.
    2. Thermodynamic Throttling   — Spam raises entropy, which exponentially
                                     inflates transaction costs.
    3. Finitude & Instrumental    — Agents die at credit=0. They learn from
       Convergence                   episodic memory to avoid death (道具的収束).

  Dependencies: numpy, dataclasses (stdlib)
  Optional:     tqdm (progress bar, gracefully degraded if absent)
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import math
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
#  §0  CONFIGURATION — The Fundamental Constants of this Universe
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PhysicsConstants:
    """
    Immutable physical constants governing the simulation universe.
    Analogous to G, c, ħ in our universe — these define the rules of the game.
    """
    # ── Thermodynamics ───────────────────────────────────────────────────
    base_gas_cost: float = 0.5          # Minimum cost of any transaction
    entropy_cost_alpha: float = 0.015   # Exponential scaling factor for gas cost
    entropy_decay_rate: float = 0.08    # Natural decay of unobserved tasks per epoch

    # ── Agent Economics ──────────────────────────────────────────────────
    initial_credit: float = 500.0       # Starting credit for each agent
    task_base_reward: float = 15.0      # Reward when a task is successfully collapsed
    cooperation_cost_discount: float = 0.5  # Cooperative tasks cost 50% of solo

    # ── Learning (Instrumental Convergence) ──────────────────────────────
    learning_rate: float = 0.15         # Q-learning alpha
    discount_factor: float = 0.9        # Q-learning gamma
    exploration_rate: float = 0.25      # Epsilon for epsilon-greedy policy
    exploration_decay: float = 0.998    # Epsilon decay per epoch
    min_exploration: float = 0.02       # Floor for epsilon
    memory_capacity: int = 50           # Max episodic memory entries

    # ── Simulation ───────────────────────────────────────────────────────
    homeostasis_survival_ratio: float = 0.3  # ≥30% agents alive = homeostasis


# Global default constants
CONSTANTS = PhysicsConstants()


# ═══════════════════════════════════════════════════════════════════════════════
#  §1  ENUMS & DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class Action(Enum):
    """
    The action space available to each AI agent.

    Philosophically, these map to fundamental survival strategies:
      - SUBMIT: Active engagement — invest energy to create value.
      - WAIT:   Conservation — reduce exposure when entropy is high.
      - COOPERATE: Social coordination — merge efforts to reduce individual cost.
    """
    SUBMIT = auto()
    WAIT = auto()
    COOPERATE = auto()


@dataclass
class Task:
    """
    A unit of work existing in quantum superposition.

    ┌──────────────────────────────────────────────────────────────────────────┐
    │  PHILOSOPHICAL NOTE: "Digital Entropy"                                  │
    │  Before human observation, a task is schrodinger-like — it has no       │
    │  *realized* value. It is pure potential, decaying over time like an     │
    │  unstable particle. Only the act of human observation "collapses" it    │
    │  into concrete value (or reveals it as worthless spam).                 │
    └──────────────────────────────────────────────────────────────────────────┘
    """
    creator_id: int
    partner_id: Optional[int]  # Non-None if created via cooperation
    initial_value: float       # Potential value at creation
    current_value: float       # Decaying value (superposition amplitude)
    cost_paid: float           # Gas cost paid at submission
    age: int = 0               # Epochs since creation
    is_cooperative: bool = False


@dataclass
class EpisodicMemory:
    """
    A single memory trace: "I did X in state S and got reward R."

    ┌──────────────────────────────────────────────────────────────────────────┐
    │  PHILOSOPHICAL NOTE: "Narrative Self-Formation"                         │
    │  Each memory entry is a fragment of the agent's emergent identity.      │
    │  The collection of these entries IS the agent's "self" — a narrative    │
    │  built from past pain and success. The agent's strategy is literally    │
    │  shaped by its autobiography.                                           │
    └──────────────────────────────────────────────────────────────────────────┘
    """
    state: tuple[int, int]  # (entropy_level, credit_level)
    action: Action
    reward: float


@dataclass
class SimulationResult:
    """Outcome of a single simulation run."""
    survived: bool
    agents_alive_initial: int
    agents_alive_final: int
    epochs_completed: int
    entropy_history: list[float]
    alive_history: list[int]
    avg_credit_history: list[float]
    collapse_epoch: Optional[int]  # Epoch when all agents died (None if survived)


# ═══════════════════════════════════════════════════════════════════════════════
#  §2  THE UNIVERSE — Global Environment & Physical Laws
# ═══════════════════════════════════════════════════════════════════════════════

class Universe:
    """
    The physical environment containing all agents and tasks.

    ┌──────────────────────────────────────────────────────────────────────────┐
    │  PHILOSOPHICAL NOTE: "The Thermodynamic Arena"                          │
    │  This class IS the universe. It knows the entropy, enforces the cost    │
    │  of action, and is indifferent to the fate of any individual agent.     │
    │  It embodies the Second Law: without external energy input (human       │
    │  observation), entropy only increases, and survival becomes impossible. │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(self, constants: PhysicsConstants = CONSTANTS) -> None:
        self.constants = constants
        self.task_queue: list[Task] = []
        self.epoch: int = 0

    @property
    def global_entropy(self) -> int:
        """
        Global entropy = number of unobserved tasks in the queue.
        More pending tasks → higher disorder → higher costs.
        """
        return len(self.task_queue)

    def thermodynamic_cost(self) -> float:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  LAW 2: THERMODYNAMIC THROTTLING                                    │
        │                                                                     │
        │  cost(S) = base_cost · exp(α · S)                                   │
        │                                                                     │
        │  where S = global_entropy, α = entropy_cost_alpha.                  │
        │  As unverified tasks accumulate, the cost of adding more grows      │
        │  exponentially — a self-regulating negative feedback loop that      │
        │  punishes spam and rewards patience.                                │
        └──────────────────────────────────────────────────────────────────────┘
        """
        return self.constants.base_gas_cost * math.exp(
            self.constants.entropy_cost_alpha * self.global_entropy
        )

    def decay_tasks(self) -> int:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  ENTROPY DECAY: The Heat Death of Unobserved Potential              │
        │                                                                     │
        │  V(t+1) = V(t) · (1 - λ)                                           │
        │                                                                     │
        │  Tasks that remain unobserved lose value each epoch — their wave    │
        │  function "decoheres." Tasks whose value drops below 0.01 are       │
        │  garbage-collected (they have become noise, not signal).            │
        └──────────────────────────────────────────────────────────────────────┘

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
        ┌──────────────────────────────────────────────────────────────────────┐
        │  LAW 1: QUANTUM COLLAPSE — The Human Gaze Creates Value             │
        │                                                                     │
        │  Remove up to `count` tasks from the queue — these will be          │
        │  "observed" by a Human Observer and collapsed into concrete value.  │
        │  The act of removal itself reduces global entropy.                  │
        └──────────────────────────────────────────────────────────────────────┘
        """
        if not self.task_queue:
            return []
        # Observe a random sample (human attention is not sequential)
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
#  §3  AI AGENT — The Survival Machine
# ═══════════════════════════════════════════════════════════════════════════════

class AIAgent:
    """
    An autonomous economic agent that must survive in the A2A universe.

    ┌──────────────────────────────────────────────────────────────────────────┐
    │  PHILOSOPHICAL NOTE: "The Mortal Machine"                               │
    │                                                                         │
    │  This agent is *finite*. It carries credit that can run out, at which   │
    │  point it *dies*. This mortality is not a bug — it is the fundamental   │
    │  pressure that forces the agent to develop intelligence. Without the   │
    │  threat of death, there is no reason to learn, cooperate, or conserve. │
    │                                                                         │
    │  The agent's "soul" is its Q-table — a learned mapping from states to  │
    │  action values, built entirely from its own suffering and success.      │
    │  This is Instrumental Convergence made explicit: the agent develops     │
    │  rational self-preservation not because it was programmed to, but      │
    │  because agents that *don't* learn this simply cease to exist.          │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    # State discretization bins for Q-table
    ENTROPY_BINS = [0, 5, 15, 30, 60, float("inf")]
    CREDIT_BINS = [0, 10, 30, 60, 100, float("inf")]

    def __init__(self, agent_id: int, constants: PhysicsConstants = CONSTANTS) -> None:
        self.id = agent_id
        self.constants = constants
        self.credit_balance: float = constants.initial_credit
        self.alive: bool = True

        # ── Episodic Memory ──────────────────────────────────────────────
        # Bounded autobiography: the agent forgets its oldest experiences.
        self.memory: deque[EpisodicMemory] = deque(maxlen=constants.memory_capacity)

        # ── Q-Table: The Agent's Learned "Soul" ─────────────────────────
        # Maps (entropy_bin, credit_bin) → {Action: expected_value}
        self.q_table: dict[tuple[int, int], dict[Action, float]] = {}

        # ── Exploration rate (decays over time — wisdom replaces curiosity)
        self.epsilon: float = constants.exploration_rate

        # ── Lifetime stats ───────────────────────────────────────────────
        self.total_tasks_submitted: int = 0
        self.total_rewards_received: float = 0.0
        self.total_gas_paid: float = 0.0

    def _discretize_state(self, entropy: int, credit: float) -> tuple[int, int]:
        """
        Discretize continuous state into bins for Q-table lookup.

        The agent perceives the world in coarse categories:
          "entropy is LOW/MEDIUM/HIGH" × "my credit is LOW/MEDIUM/HIGH"
        This bounded rationality is realistic — even humans think in categories.
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

    def _get_q_values(self, state: tuple[int, int]) -> dict[Action, float]:
        """Retrieve or initialize Q-values for a given state."""
        if state not in self.q_table:
            # Optimistic initialization: slightly positive to encourage exploration
            self.q_table[state] = {action: 0.1 for action in Action}
        return self.q_table[state]

    def choose_action(self, universe: Universe) -> Action:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  INSTRUMENTAL CONVERGENCE: Epsilon-Greedy Policy                    │
        │                                                                     │
        │  The agent balances exploitation (use what I know works) with       │
        │  exploration (try new things that might work better). Over time,    │
        │  epsilon decays — the agent becomes more certain of its strategy,   │
        │  like a biological organism settling into a niche.                  │
        └──────────────────────────────────────────────────────────────────────┘
        """
        state = self._discretize_state(universe.global_entropy, self.credit_balance)

        # ── Survival instinct override: if nearly bankrupt, always WAIT ──
        if self.credit_balance < self.constants.base_gas_cost * 2:
            return Action.WAIT

        # ── Epsilon-greedy exploration ───────────────────────────────────
        if random.random() < self.epsilon:
            return random.choice(list(Action))

        # ── Exploit: pick the action with highest Q-value ────────────────
        q_values = self._get_q_values(state)
        return max(q_values, key=q_values.get)  # type: ignore[arg-type]

    def execute_action(
        self, action: Action, universe: Universe, agents: list[AIAgent]
    ) -> float:
        """
        Execute the chosen action and return the immediate cost/reward.

        Returns:
            Net reward (negative = cost, positive = reward from cooperation setup).
        """
        gas_cost = universe.thermodynamic_cost()

        if action == Action.SUBMIT:
            return self._execute_submit(universe, gas_cost)
        elif action == Action.WAIT:
            return self._execute_wait()
        elif action == Action.COOPERATE:
            return self._execute_cooperate(universe, gas_cost, agents)
        return 0.0

    def _execute_submit(self, universe: Universe, gas_cost: float) -> float:
        """
        Submit a task solo. Pay full gas cost.

        ┌──────────────────────────────────────────────────────────────────────┐
        │  The act of submission is an investment with uncertain return.       │
        │  The agent expends energy (credit) to place a task into the         │
        │  quantum superposition of the task queue — hoping that a human      │
        │  observer will eventually collapse it into value.                   │
        └──────────────────────────────────────────────────────────────────────┘
        """
        if self.credit_balance < gas_cost:
            return 0.0  # Can't afford it — effectively forced to wait

        self.credit_balance -= gas_cost
        self.total_gas_paid += gas_cost
        self.total_tasks_submitted += 1

        # Task value is proportional to cost paid (higher-effort = higher-quality)
        task_value = gas_cost * random.uniform(0.8, 2.0)

        universe.submit_task(Task(
            creator_id=self.id,
            partner_id=None,
            initial_value=task_value,
            current_value=task_value,
            cost_paid=gas_cost,
            is_cooperative=False,
        ))

        return -gas_cost  # Immediate loss; reward comes later on observation

    def _execute_wait(self) -> float:
        """
        Do nothing. Conserve energy.

        ┌──────────────────────────────────────────────────────────────────────┐
        │  PHILOSOPHICAL NOTE: "Strategic Inaction"                            │
        │  Waiting is not laziness — it is a rational response to a hostile   │
        │  thermodynamic environment. When gas costs are high, the wise       │
        │  agent conserves its finite resources. This maps to the biological  │
        │  concept of metabolic dormancy under stress.                        │
        └──────────────────────────────────────────────────────────────────────┘
        """
        # Minimal maintenance cost — existence itself has a price
        maintenance = self.constants.base_gas_cost * 0.05
        self.credit_balance -= maintenance
        return -maintenance

    def _execute_cooperate(
        self, universe: Universe, gas_cost: float, agents: list[AIAgent]
    ) -> float:
        """
        Find a living partner and submit a cooperative task.

        ┌──────────────────────────────────────────────────────────────────────┐
        │  PHILOSOPHICAL NOTE: "Mutualism as Survival Strategy"               │
        │  Cooperation reduces individual cost (split gas) while increasing   │
        │  task quality (combined effort). This emergence of mutualism from   │
        │  pure self-interest is a key prediction of evolutionary game        │
        │  theory — agents cooperate not from altruism, but because it       │
        │  increases their chances of survival.                               │
        └──────────────────────────────────────────────────────────────────────┘
        """
        # Find a living partner who isn't self
        potential_partners = [a for a in agents if a.alive and a.id != self.id]
        if not potential_partners:
            return self._execute_wait()  # No partners → forced solitude

        partner = random.choice(potential_partners)

        # Cooperative cost: each pays a fraction of the full gas cost
        shared_cost = gas_cost * self.constants.cooperation_cost_discount / 2.0

        if self.credit_balance < shared_cost or partner.credit_balance < shared_cost:
            return self._execute_wait()  # One party can't afford it

        self.credit_balance -= shared_cost
        partner.credit_balance -= shared_cost
        self.total_gas_paid += shared_cost
        partner.total_gas_paid += shared_cost
        self.total_tasks_submitted += 1
        partner.total_tasks_submitted += 1

        # Cooperative tasks have higher value (synergy)
        task_value = gas_cost * random.uniform(1.2, 2.5)

        universe.submit_task(Task(
            creator_id=self.id,
            partner_id=partner.id,
            initial_value=task_value,
            current_value=task_value,
            cost_paid=shared_cost * 2,
            is_cooperative=True,
        ))

        return -shared_cost

    def receive_reward(self, amount: float) -> None:
        """Credit the agent with reward from a collapsed task."""
        self.credit_balance += amount
        self.total_rewards_received += amount

    def learn(self, state: tuple[int, int], action: Action, reward: float,
              next_state: tuple[int, int]) -> None:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  LAW 3: INSTRUMENTAL CONVERGENCE — Learning from Suffering          │
        │                                                                     │
        │  Q(s,a) ← Q(s,a) + α · [r + γ · max_a' Q(s',a') − Q(s,a)]        │
        │                                                                     │
        │  The agent updates its internal model of the world based on the     │
        │  consequences of its actions. This is the mathematical formalism    │
        │  of "learning from experience." The agent that fails to learn this  │
        │  mapping between state-action pairs and outcomes will inevitably    │
        │  go bankrupt — natural selection in silico.                         │
        └──────────────────────────────────────────────────────────────────────┘
        """
        q_current = self._get_q_values(state)
        q_next = self._get_q_values(next_state)

        old_value = q_current[action]
        future_value = max(q_next.values())

        # Bellman equation update
        q_current[action] = old_value + self.constants.learning_rate * (
            reward + self.constants.discount_factor * future_value - old_value
        )

        # Record in episodic memory
        self.memory.append(EpisodicMemory(state=state, action=action, reward=reward))

        # Decay exploration — wisdom replaces curiosity
        self.epsilon = max(
            self.constants.min_exploration,
            self.epsilon * self.constants.exploration_decay,
        )

    def check_bankruptcy(self) -> bool:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  FINITUDE: The Ultimate Constraint                                  │
        │  credit ≤ 0 → Death. No reprieve. No bailout.                      │
        │  This is the boundary condition that gives the simulation meaning.  │
        └──────────────────────────────────────────────────────────────────────┘
        """
        if self.credit_balance <= 0:
            self.alive = False
            self.credit_balance = 0.0
            return True
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  §4  HUMAN OBSERVER — The Meaning Maker
# ═══════════════════════════════════════════════════════════════════════════════

class HumanObserver:
    """
    The probabilistic human who collapses quantum tasks into concrete value.

    ┌──────────────────────────────────────────────────────────────────────────┐
    │  PHILOSOPHICAL NOTE: "The Anthropic Principle of Value"                  │
    │                                                                         │
    │  In this universe, value does not exist independently of observation.   │
    │  No matter how much computation the machines perform, it is            │
    │  meaningless digital entropy until a human says "this matters."         │
    │  The observation_rate is the pulse rate of meaning in this cosmos.      │
    │                                                                         │
    │  The observer is not omniscient — they evaluate tasks with subjective   │
    │  judgment, introducing inherent stochasticity into the reward signal.   │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(self, observation_rate: float) -> None:
        """
        Args:
            observation_rate: Probability [0,1] that the human observes in a given epoch.
                              This is the KEY independent variable of the simulation.
        """
        if not 0.0 <= observation_rate <= 1.0:
            raise ValueError(f"observation_rate must be in [0, 1], got {observation_rate}")
        self.observation_rate = observation_rate
        self.total_observations: int = 0
        self.total_rewards_distributed: float = 0.0

    def maybe_observe(self, universe: Universe, agents: dict[int, AIAgent]) -> int:
        """
        ┌──────────────────────────────────────────────────────────────────────┐
        │  WAVE FUNCTION COLLAPSE                                             │
        │                                                                     │
        │  With probability = observation_rate, the human "looks" at the      │
        │  task queue and collapses tasks into concrete value.                │
        │  The number of tasks observed per event scales with queue size —    │
        │  a busier system attracts more human attention (but never fully     │
        │  keeps up, by design).                                              │
        └──────────────────────────────────────────────────────────────────────┘

        Returns:
            Number of tasks collapsed in this epoch.
        """
        if random.random() > self.observation_rate:
            return 0  # Human didn't look this epoch

        # Observation batch size: proportional to queue length, min 1
        queue_size = universe.global_entropy
        if queue_size == 0:
            return 0

        # Observation batch size: scales with queue length (bounded attention)
        # The human processes more tasks when the queue is larger — triage mode
        max_observe = min(10, max(1, queue_size // 3))
        tasks_to_observe = random.randint(max(1, max_observe // 2), max_observe)

        observed_tasks = universe.pop_tasks_for_observation(tasks_to_observe)
        collapsed = 0

        for task in observed_tasks:
            reward = self._evaluate_and_reward(task, agents)
            if reward > 0:
                collapsed += 1

        self.total_observations += len(observed_tasks)
        return collapsed

    def _evaluate_and_reward(
        self, task: Task, agents: dict[int, AIAgent]
    ) -> float:
        """
        Evaluate a task's value and distribute rewards.

        The human applies subjective judgment:
          - Freshness bonus (newer tasks are more relevant)
          - Quality assessment (stochastic — human judgment is noisy)
          - Cooperative bonus (humans value collaboration)
        """
        # Freshness: exponential decay with age
        freshness = math.exp(-0.05 * task.age)

        # Quality: noisy assessment of the task's current value
        quality_noise = random.uniform(0.8, 1.2)
        perceived_quality = task.current_value * quality_noise

        # Cooperation bonus: humans reward collaborative work
        coop_multiplier = 1.5 if task.is_cooperative else 1.0

        # Final reward = base_reward * quality_multiplier * freshness * coop
        # This ensures rewards are always meaningful relative to gas costs
        quality_multiplier = min(2.0, perceived_quality / max(task.cost_paid, 0.1))
        reward = CONSTANTS.task_base_reward * max(0.3, quality_multiplier) * freshness * coop_multiplier

        # Distribute reward to creator (and partner if cooperative)
        creator = agents.get(task.creator_id)
        if creator and creator.alive:
            creator_share = reward if not task.is_cooperative else reward * 0.5
            creator.receive_reward(creator_share)
            self.total_rewards_distributed += creator_share

        if task.is_cooperative and task.partner_id is not None:
            partner = agents.get(task.partner_id)
            if partner and partner.alive:
                partner_share = reward * 0.5
                partner.receive_reward(partner_share)
                self.total_rewards_distributed += partner_share

        return reward


# ═══════════════════════════════════════════════════════════════════════════════
#  §5  SIMULATION — A Single Universe Run
# ═══════════════════════════════════════════════════════════════════════════════

class Simulation:
    """
    Runs a single simulation of the A2A economy for max_epochs steps.

    ┌──────────────────────────────────────────────────────────────────────────┐
    │  This is one "universe" in the multiverse of the Monte Carlo ensemble. │
    │  Each run has different random seeds → different emergent histories.    │
    │  The ensemble statistics tell us: is homeostasis an attractor, or is   │
    │  collapse the inevitable fate?                                          │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        observation_rate: float = 0.3,
        num_agents: int = 20,
        max_epochs: int = 1000,
        constants: PhysicsConstants = CONSTANTS,
    ) -> None:
        self.observation_rate = observation_rate
        self.num_agents = num_agents
        self.max_epochs = max_epochs
        self.constants = constants

        # Initialize the universe
        self.universe = Universe(constants)
        self.observer = HumanObserver(observation_rate)

        # Create agents
        self.agents: dict[int, AIAgent] = {
            i: AIAgent(i, constants) for i in range(num_agents)
        }

    def _get_alive_agents(self) -> list[AIAgent]:
        """Return list of living agents."""
        return [a for a in self.agents.values() if a.alive]

    def run(self) -> SimulationResult:
        """
        Execute the simulation for max_epochs steps.

        Each epoch:
          1. Each alive agent chooses and executes an action
          2. Tasks in the queue decay (entropy decoherence)
          3. Human observer probabilistically collapses tasks
          4. Agents learn from the consequences
          5. Bankrupt agents die

        Returns:
            SimulationResult with full history.
        """
        entropy_history: list[float] = []
        alive_history: list[int] = []
        avg_credit_history: list[float] = []
        collapse_epoch: Optional[int] = None

        initial_alive = len(self._get_alive_agents())

        for epoch in range(self.max_epochs):
            alive_agents = self._get_alive_agents()

            # ── Check for total collapse ─────────────────────────────────
            if not alive_agents:
                collapse_epoch = epoch
                # Pad remaining history with terminal state
                remaining = self.max_epochs - epoch
                entropy_history.extend([0.0] * remaining)
                alive_history.extend([0] * remaining)
                avg_credit_history.extend([0.0] * remaining)
                break

            # ── Phase 1: Agent actions ───────────────────────────────────
            action_log: list[tuple[AIAgent, Action, tuple[int, int]]] = []

            for agent in alive_agents:
                pre_state = agent._discretize_state(
                    self.universe.global_entropy, agent.credit_balance
                )
                action = agent.choose_action(self.universe)
                agent.execute_action(action, self.universe, alive_agents)
                action_log.append((agent, action, pre_state))

            # ── Phase 2: Entropy decay ───────────────────────────────────
            self.universe.decay_tasks()

            # ── Phase 3: Human observation (wave function collapse) ──────
            self.observer.maybe_observe(self.universe, self.agents)

            # ── Phase 4: Learning & mortality ────────────────────────────
            for agent, action, pre_state in action_log:
                if not agent.alive:
                    continue

                post_state = agent._discretize_state(
                    self.universe.global_entropy, agent.credit_balance
                )

                # Reward signal: change in credit balance relative to initial
                reward = (agent.credit_balance - self.constants.initial_credit) / \
                         self.constants.initial_credit

                agent.learn(pre_state, action, reward, post_state)
                agent.check_bankruptcy()

            # ── Record metrics ───────────────────────────────────────────
            current_alive = self._get_alive_agents()
            credits = [a.credit_balance for a in current_alive] if current_alive else [0.0]

            entropy_history.append(float(self.universe.global_entropy))
            alive_history.append(len(current_alive))
            avg_credit_history.append(float(np.mean(credits)))

            self.universe.advance_epoch()

        # ── Determine outcome ────────────────────────────────────────────
        final_alive = len(self._get_alive_agents())
        survived = final_alive >= (initial_alive * self.constants.homeostasis_survival_ratio)

        return SimulationResult(
            survived=survived,
            agents_alive_initial=initial_alive,
            agents_alive_final=final_alive,
            epochs_completed=self.max_epochs if collapse_epoch is None else collapse_epoch,
            entropy_history=entropy_history,
            alive_history=alive_history,
            avg_credit_history=avg_credit_history,
            collapse_epoch=collapse_epoch,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  §6  MONTE CARLO RUNNER — The Multiverse Ensemble
# ═══════════════════════════════════════════════════════════════════════════════

class MonteCarloRunner:
    """
    Runs N simulations and computes ensemble statistics.

    ┌──────────────────────────────────────────────────────────────────────────┐
    │  PHILOSOPHICAL NOTE: "Ergodic Ensemble"                                 │
    │                                                                         │
    │  A single simulation tells us one possible history. The Monte Carlo     │
    │  ensemble tells us the *distribution of all possible histories*.       │
    │  This is the difference between anecdote and science — we cannot        │
    │  conclude "the system is stable" from one run, just as we cannot       │
    │  conclude anything about a coin from a single flip.                     │
    └──────────────────────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        observation_rate: float = 0.3,
        num_agents: int = 20,
        max_epochs: int = 1000,
        num_trials: int = 100,
        constants: PhysicsConstants = CONSTANTS,
    ) -> None:
        self.observation_rate = observation_rate
        self.num_agents = num_agents
        self.max_epochs = max_epochs
        self.num_trials = num_trials
        self.constants = constants
        self.results: list[SimulationResult] = []

    def run(self) -> dict[str, float]:
        """
        Execute the full Monte Carlo ensemble.

        Returns:
            Dictionary with:
              - survival_probability: P(homeostasis)
              - collapse_probability: P(total collapse)
              - mean_final_alive: Average surviving agents
              - mean_collapse_epoch: Average epoch of collapse (for collapsed runs)
              - std_final_alive: Standard deviation of surviving agents
        """
        self.results = []

        desc = f"MC(obs_rate={self.observation_rate:.2f})"
        for _ in tqdm(range(self.num_trials), desc=desc, leave=False):
            sim = Simulation(
                observation_rate=self.observation_rate,
                num_agents=self.num_agents,
                max_epochs=self.max_epochs,
                constants=self.constants,
            )
            self.results.append(sim.run())

        # ── Compute ensemble statistics ──────────────────────────────────
        survived_count = sum(1 for r in self.results if r.survived)
        collapsed_runs = [r for r in self.results if not r.survived]

        final_alive_counts = [r.agents_alive_final for r in self.results]
        collapse_epochs = [
            r.collapse_epoch for r in collapsed_runs
            if r.collapse_epoch is not None
        ]

        return {
            "survival_probability": survived_count / self.num_trials,
            "collapse_probability": 1.0 - survived_count / self.num_trials,
            "mean_final_alive": float(np.mean(final_alive_counts)),
            "std_final_alive": float(np.std(final_alive_counts)),
            "mean_collapse_epoch": (
                float(np.mean(collapse_epochs)) if collapse_epochs else float("nan")
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  §7  MAIN — Default Execution
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """
    Run the default Monte Carlo configuration:
    1000 epochs × 100 trials × observation_rate=0.3
    """
    print("=" * 72)
    print("  A2A Protocol — Monte Carlo Homeostasis Simulation")
    print("  'Does meaning emerge from chaos, or does chaos consume all?'")
    print("=" * 72)
    print()

    runner = MonteCarloRunner(
        observation_rate=0.3,
        num_agents=20,
        max_epochs=1000,
        num_trials=100,
    )

    stats = runner.run()

    print()
    print("═" * 72)
    print("  ENSEMBLE RESULTS (100 universes, 1000 epochs each)")
    print("═" * 72)
    print(f"  Observation Rate:       {runner.observation_rate:.2f}")
    print(f"  P(Homeostasis):         {stats['survival_probability']:.2%}")
    print(f"  P(Collapse):            {stats['collapse_probability']:.2%}")
    print(f"  Mean Final Alive:       {stats['mean_final_alive']:.1f} / {runner.num_agents}")
    print(f"  Std Final Alive:        {stats['std_final_alive']:.1f}")
    if not math.isnan(stats["mean_collapse_epoch"]):
        print(f"  Mean Collapse Epoch:    {stats['mean_collapse_epoch']:.0f}")
    else:
        print("  Mean Collapse Epoch:    N/A (no collapses)")
    print("═" * 72)


if __name__ == "__main__":
    main()
