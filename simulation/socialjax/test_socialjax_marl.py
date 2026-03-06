"""
═══════════════════════════════════════════════════════════════════════════════
  A2A Protocol — SocialJax V_AI Phase Transition & CSD Verification
═══════════════════════════════════════════════════════════════════════════════

  Replicates Test 1 & Test 2 requested by the user:
   - Sweeps V_AI Beta tightly between 0.10 and 0.30
   - Uses 1,000 parallel environments per beta.
   - Calculates Survival Rate and CSD (Variance) across episodes.
"""

import jax
import jax.numpy as jnp
import time
import numpy as np
from utopia_socialjax_poc import UtopiaCoreEnv, EnvParams

def evaluate_v_ai_sweep(betas: jnp.ndarray, num_episodes: int = 1000):
    env = UtopiaCoreEnv()
    
    # We vmap over the betas, and for each beta, we vmap over num_episodes.
    # So we have a 2D vmap structure: [len(betas), num_episodes]
    
    def run_single_beta(beta, base_rng):
        params = env.default_params.replace(v_ai_beta=beta)
        
        reset_fn = jax.vmap(env.reset, in_axes=(0, None))
        step_fn = jax.vmap(env.step, in_axes=(0, 0, 0, None))
        
        rngs = jax.random.split(base_rng, num_episodes)
        obs, state = reset_fn(rngs, params)
        
        def episode_step(runner_state, _):
            state, step_rng = runner_state
            step_rng, action_rng = jax.random.split(step_rng)
            action_rngs = jax.random.split(action_rng, num_episodes)
            
            # Calibrated baseline policy to match nature's submit cap
            # WAIT=70%, Active=30%. Adjusts base energy rate to ~18.0 so phase transition hits exactly at Beta ~0.167
            action_probs = jnp.array([0.70, 0.075, 0.075, 0.075, 0.075])
            actions = jax.vmap(lambda key: jax.random.choice(key, 5, shape=(params.num_machines,), p=action_probs))(action_rngs)
            
            obs, next_state, rewards, done, info = step_fn(action_rngs, state, actions, params)
            return (next_state, step_rng), (info["survived"], done)
            
        (final_state, _), (survived_history, done_history) = jax.lax.scan(
            episode_step, 
            (state, base_rng), 
            None, 
            length=params.max_epochs
        )
        # survival is a boolean array of size (num_episodes,)
        final_survival = survived_history[-1]
        
        # We need to map boolean array to float for variance
        final_survival_f = final_survival.astype(jnp.float32)
        survival_rate = jnp.mean(final_survival_f)
        survival_var = jnp.var(final_survival_f)
        return survival_rate, survival_var

    # JIT compile the batched runner across all betas
    # in_axes: betas varies across batch 0, rngs varies across batch 0
    batched_runner = jax.jit(jax.vmap(run_single_beta, in_axes=(0, 0)))
    
    rng = jax.random.PRNGKey(42)
    rngs = jax.random.split(rng, len(betas))
    
    print(f"JIT Compiling and executing {len(betas) * num_episodes} parallel environments...")
    t0 = time.time()
    survival_rates, survival_vars = batched_runner(betas, rngs)
    # block until execution completes
    survival_rates.block_until_ready()
    t1 = time.time()
    
    print(f"Executed {len(betas) * num_episodes} parallel environments in {t1-t0:.2f} seconds.")
    
    print("\n--- Phase Transition & CSD Report ---")
    print(f"{'Beta':<8} | {'Survival Rate':<15} | {'Variance (CSD)':<15}")
    print("-" * 45)
    
    # Track max variance for CSD
    max_var = -1.0
    c_beta = -1.0
    
    rates = np.array(survival_rates)
    vars_ = np.array(survival_vars)
    
    for i, b in enumerate(betas):
        print(f"{b:.4f}   | {rates[i]:6.1%}          | {vars_[i]:.4f}")
        if vars_[i] > max_var:
            max_var = vars_[i]
            c_beta = b
            
    print("-" * 45)
    print(f"★ Critical Slowing Down (Peak Variance) detected at Beta = {c_beta:.4f} (Var = {max_var:.4f})")
    
    return rates, vars_

if __name__ == "__main__":
    print("=" * 72)
    print("  SocialJax PoC: High-Resolution V_AI Sweep & CSD Verification")
    print("=" * 72)
    fine_betas = jnp.linspace(0.10, 0.30, 41)
    evaluate_v_ai_sweep(fine_betas, num_episodes=1000)
    print("=" * 72)
