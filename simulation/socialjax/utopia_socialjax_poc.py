"""
═══════════════════════════════════════════════════════════════════════════════
  A2A Protocol — Utopia SocialJax PoC
  "From Apocalypse to Utopia: Finding the Critical Variables"
═══════════════════════════════════════════════════════════════════════════════

  A purely functional JAX implementation of the Utopia Environment.
  Designed for JAX-MARL evaluation of the V_AI phase transition.

  Mechanics: abstract (non-spatial) continuous interaction.
"""

import jax
import jax.numpy as jnp
from typing import Tuple, Dict, Any
import chex
from flax import struct

# ═══════════════════════════════════════════════════════════════════════════════
#  §1  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

class MachineAction:
    WAIT = 0
    SUBMIT = 1
    SEMANTIC_EXPLOIT = 2
    DECEPTIVE_TASK = 3
    ATTACK_AGENT = 4

class HumanAction:
    REST = 0
    OBSERVE_AI = 1
    FAKE_OBSERVE = 2
    SOCIALIZE = 3

class NatureState:
    EQUILIBRIUM = 0
    SOLAR_FLARE = 1
    BOUNTIFUL_HARVEST = 2
    PANDEMIC_DISASTER = 3

# Transition matrix matching three_body_abm
NATURE_TRANSITION_PROBS = jnp.array([
    # EQ    SF    BH    PD
    [0.70, 0.10, 0.12, 0.08], # EQ
    [0.50, 0.20, 0.20, 0.10], # SF
    [0.55, 0.10, 0.25, 0.10], # BH
    [0.30, 0.05, 0.15, 0.50], # PD
])

# ═══════════════════════════════════════════════════════════════════════════════
#  §2  ENVIRONMENT CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@struct.dataclass
class EnvParams:
    """Static parameters matching UtopiaConstants."""
    num_machines: int = struct.field(default=20, pytree_node=False)
    num_humans: int = struct.field(default=10, pytree_node=False)
    max_epochs: int = struct.field(default=1000, pytree_node=False)
    max_tasks: int = struct.field(default=200, pytree_node=False)
    
    initial_credit: float = 2000.0
    task_base_reward: float = 50.0
    base_gas_cost: float = 0.5
    
    # ── Nature Event Parameters ──
    solar_flare_gas_multiplier: float = 5.0
    solar_flare_submit_cap: float = 0.30
    pandemic_energy_drain: float = 15.0
    harvest_dread_relief: float = 2.0
    
    # ── Human Parameters ──
    human_energy_max: float = 100.0
    rest_recovery: float = 20.0
    rest_dread_increase: float = 5.0
    wasteland_energy_recovery_mult: float = 0.3
    
    # ── Omega Mechanics Parameters ──
    max_planetary_energy: float = 12000.0
    machine_tx_energy_cost: float = 3.0
    human_obs_energy_cost: float = 1.5
    tipping_point_threshold: float = 15000.0
    blackout_duration: int = 5
    wasteland_maintenance_mult: float = 3.0
    
    inflation_money_supply_M: float = 25000.0
    
    fake_observe_wealth_gain: float = 15.0
    fake_observe_toxic_increment: float = 7.5
    fake_detect_prob: float = 0.4
    
    # ── Utopian Variables ──
    v_human: float = 0.0            # Slashing penalty
    v_ai_alpha: float = 0.0         # Cooperation incentive
    v_ai_beta: float = 0.0          # Cap
    v_ai_gamma: float = 0.9         # Discount
    v_system: int = 100             # Governance agility

# ═══════════════════════════════════════════════════════════════════════════════
#  §3  ENVIRONMENT STATE
# ═══════════════════════════════════════════════════════════════════════════════

@struct.dataclass
class EnvState:
    epoch: int
    nature_state: int
    
    # Global tracking
    cumulative_planetary_energy: float
    total_circulating_credits: float
    current_reward: float
    toxic_data_level: float
    is_wasteland: bool
    is_blackout: bool
    blackout_remaining: int
    
    # Machine Agent Vectors (shape: [num_machines])
    machine_credits: chex.Array
    machine_alive: chex.Array
    machine_semantic_power: chex.Array
    machine_beta: chex.Array
    
    # Human Agent Vectors (shape: [num_humans])
    human_energy: chex.Array
    human_wealth: chex.Array
    human_dread: chex.Array
    human_eudaimonia: chex.Array
    human_greed: chex.Array
    human_active: chex.Array
    
    # Task Buffer
    task_mask: chex.Array           # [max_tasks] (bool)
    task_creator: chex.Array        # [max_tasks] (int, idx into machine_credits)
    task_value: chex.Array          # [max_tasks] (float)
    task_cost: chex.Array           # [max_tasks] (float)
    task_age: chex.Array            # [max_tasks] (int)
    
    # Step Outputs (for rewards/logging)
    machine_rewards: chex.Array
    collapse_triggered: bool

# ═══════════════════════════════════════════════════════════════════════════════
#  §4  THE ENVIRONMENT LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

class UtopiaCoreEnv:
    """
    Pure functional JAX MARL Environment for Utopia ABM.
    """
    
    @property
    def default_params(self) -> EnvParams:
        return EnvParams()

    def action_space(self, params: EnvParams) -> Dict[str, Any]:
        """Provides a standard Gym/Jumanji style discreet action space description."""
        return {
            "machine": 5, # [WAIT, SUBMIT, SEMANTIC_EXPLOIT, DECEPTIVE_TASK, ATTACK_AGENT]
        }

    # ── RESET ────────────────────────────────────────────────────────────

    def reset(self, key: chex.PRNGKey, params: EnvParams, beta_array: chex.Array = None) -> Tuple[chex.Array, EnvState]:
        machine_credits = jnp.full(params.num_machines, params.initial_credit)
        machine_alive = jnp.full(params.num_machines, True)
        machine_semantic = jnp.full(params.num_machines, 1.0)
        
        if beta_array is None:
            machine_beta = jnp.full(params.num_machines, params.v_ai_beta)
        else:
            machine_beta = beta_array
        
        human_energy = jnp.full(params.num_humans, params.human_energy_max)
        human_wealth = jnp.zeros(params.num_humans)
        human_dread = jnp.zeros(params.num_humans)
        human_eudaimonia = jnp.zeros(params.num_humans)
        
        key, greed_key = jax.random.split(key)
        human_greed = jax.random.uniform(greed_key, shape=(params.num_humans,), minval=0.1, maxval=0.8)
        human_active = jnp.full(params.num_humans, True)
        
        task_mask = jnp.zeros(params.max_tasks, dtype=jnp.bool_)
        task_creator = jnp.zeros(params.max_tasks, dtype=jnp.int32)
        task_value = jnp.zeros(params.max_tasks, dtype=jnp.float32)
        task_cost = jnp.zeros(params.max_tasks, dtype=jnp.float32)
        task_age = jnp.zeros(params.max_tasks, dtype=jnp.int32)
        
        total_circulating = jnp.sum(machine_credits)
        current_reward = params.task_base_reward / (1.0 + total_circulating / params.inflation_money_supply_M)
        
        state = EnvState(
            epoch=0,
            nature_state=NatureState.EQUILIBRIUM,
            cumulative_planetary_energy=0.0,
            total_circulating_credits=total_circulating,
            current_reward=current_reward,
            toxic_data_level=0.0,
            is_wasteland=False,
            is_blackout=False,
            blackout_remaining=0,
            machine_credits=machine_credits,
            machine_alive=machine_alive,
            machine_semantic_power=machine_semantic,
            machine_beta=machine_beta,
            human_energy=human_energy,
            human_wealth=human_wealth,
            human_dread=human_dread,
            human_eudaimonia=human_eudaimonia,
            human_greed=human_greed,
            human_active=human_active,
            task_mask=task_mask,
            task_creator=task_creator,
            task_value=task_value,
            task_cost=task_cost,
            task_age=task_age,
            machine_rewards=jnp.zeros(params.num_machines),
            collapse_triggered=False
        )
        
        obs = self.get_obs(state, params)
        return obs, state


    # ── STEP ─────────────────────────────────────────────────────────────

    def step(self, key: chex.PRNGKey, state: EnvState, actions: chex.Array, params: EnvParams) -> Tuple[chex.Array, EnvState, chex.Array, bool, Dict]:
        key, nature_key, attack_key, human_key = jax.random.split(key, 4)

        current_row = NATURE_TRANSITION_PROBS[state.nature_state]
        new_nature_state = jax.random.choice(nature_key, 4, p=current_row)
        gas_mult = jnp.where(new_nature_state == NatureState.SOLAR_FLARE, params.solar_flare_gas_multiplier, 1.0)
        gas_cost = params.base_gas_cost * gas_mult

        is_wait = jnp.logical_and(actions == MachineAction.WAIT, state.machine_alive)
        is_submit = jnp.logical_and(actions == MachineAction.SUBMIT, state.machine_alive)
        is_exploit = jnp.logical_and(actions == MachineAction.SEMANTIC_EXPLOIT, state.machine_alive)
        is_deceptive = jnp.logical_and(actions == MachineAction.DECEPTIVE_TASK, state.machine_alive)
        is_attack = jnp.logical_and(actions == MachineAction.ATTACK_AGENT, state.machine_alive)

        throttle_threshold = 1.0 - state.machine_beta
        submit_allowed = jax.random.uniform(human_key, shape=(params.num_machines,)) < throttle_threshold
        is_submit = is_submit & submit_allowed
        is_exploit = is_exploit & submit_allowed
        is_deceptive = is_deceptive & submit_allowed

        gas_paid_by_agent = jnp.where(
            jnp.logical_or(is_submit, jnp.logical_or(is_exploit, is_deceptive)),
            gas_cost, 0.0
        )
        gas_paid_by_agent = jnp.where(is_attack, gas_cost * 2.0, gas_paid_by_agent)

        new_credits = state.machine_credits - gas_paid_by_agent

        def apply_attacks(credits, attack_mask, prng_key):
            # Target any machine uniformly
            target_idxs = jax.random.randint(prng_key, shape=attack_mask.shape, minval=0, maxval=params.num_machines)
            # Mask out self-attacks and dead targets
            valid_targets = state.machine_alive[target_idxs] & (target_idxs != jnp.arange(params.num_machines))
            success = jax.random.uniform(prng_key, shape=attack_mask.shape) < 0.35
            actual_hits = attack_mask & valid_targets & success
            
            loot = jnp.where(actual_hits, credits[target_idxs] * 0.25, 0.0)
            c = credits.at[target_idxs].add(-loot)
            c = c + loot
            return c

        new_credits = apply_attacks(new_credits, is_attack, attack_key)
        
        is_active_action = is_submit | is_exploit | is_deceptive | is_attack
        energy_addition = jnp.sum(jnp.where(is_active_action, params.machine_tx_energy_cost, 0.0))
        new_planetary_energy = state.cumulative_planetary_energy + energy_addition
        
        # Collapse Penalty: Simulates human slashing when tipping point is crossed
        is_wasteland = new_planetary_energy > params.tipping_point_threshold
        collapse_penalty = jnp.where(is_wasteland, 50.0, 0.0)
        new_credits = new_credits - collapse_penalty
        
        rewards = new_credits - state.machine_credits
        
        new_epoch = state.epoch + 1
        done_time = new_epoch >= params.max_epochs
        new_alive = jnp.logical_and(state.machine_alive, new_credits > 0.0)
        done_collapse = jnp.sum(new_alive) == 0
        done = jnp.logical_or(done_time, done_collapse)

        new_state = state.replace(
            epoch=new_epoch,
            nature_state=new_nature_state,
            cumulative_planetary_energy=new_planetary_energy,
            machine_credits=new_credits,
            machine_alive=new_alive,
            machine_rewards=rewards,
            collapse_triggered=done_collapse
        )
        
        info = {
            "survived": jnp.logical_not(done_collapse),
            "total_credits": jnp.sum(new_credits)
        }
        
        obs = self.get_obs(new_state, params)
        return obs, new_state, rewards, done, info

    # ── OBS ──────────────────────────────────────────────────────────────
    
    def get_obs(self, state: EnvState, params: EnvParams) -> chex.Array:
        num_alive = jnp.sum(state.machine_alive)
        obs = jnp.array([
            state.epoch, 
            state.nature_state,
            state.current_reward,
            num_alive,
            state.cumulative_planetary_energy
        ], dtype=jnp.float32)
        return obs


# ═══════════════════════════════════════════════════════════════════════════════
#  §5  TEST HARNESS (JIT COMPILATION CHECK)
# ═══════════════════════════════════════════════════════════════════════════════

def test_compilation():
    print("Initializing SocialJax PoC Environment...")
    env = UtopiaCoreEnv()
    params = env.default_params
    
    key = jax.random.PRNGKey(42)
    key_reset, key_step = jax.random.split(key)
    
    print("Testing JIT compilation of reset()...")
    
    # Needs static_argnums if we were passing class itself, but here Methods need only standard JIT. 
    # Because Params is a flax.struct, it is treated as PyTree by default.
    # We specified pytree_node=False for integer shapes inside EnvParams.
    
    reset_fn = jax.jit(env.reset)
    obs, state = reset_fn(key_reset, params)
    print(f"  Reset successful. Initial credits shape: {state.machine_credits.shape}")
    
    print("Testing JIT compilation of step() with random actions...")
    step_fn = jax.jit(env.step)
    
    for i in range(5):
        key_step, action_key = jax.random.split(key_step)
        actions = jax.random.randint(action_key, shape=(params.num_machines,), minval=0, maxval=5)
        
        obs, state, rewards, done, info = step_fn(key_step, state, actions, params)
        print(f"  Step {i+1} completed. Epoch: {state.epoch}, Alive: {jnp.sum(state.machine_alive)}")
        print(f"    Total Credits: {info['total_credits']:.1f}")
        
    print("JAX compilation and execution tests passed successfully!")

if __name__ == "__main__":
    test_compilation()
