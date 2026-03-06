"""
═══════════════════════════════════════════════════════════════════════════════
  A2A Protocol — Sim 23: Heterogeneous Population (Freeriders vs Cooperators)
═══════════════════════════════════════════════════════════════════════════════

  This test replicates Sim 23 to mathematically verify that the ecosystem
  depends on the *collective average* beta, not individual compliance.
  We test multiple freerider ratios (beta=0.0) mixed with cooperators
  to see if the homogeneous collective average threshold (~0.13-0.16) holds.
"""

import jax
import jax.numpy as jnp
import time
import numpy as np
from utopia_socialjax_poc import UtopiaCoreEnv, EnvParams

def evaluate_heterogeneous():
    env = UtopiaCoreEnv()
    params = env.default_params
    
    freerider_ratios = [0.50, 0.60, 0.70, 0.75, 0.80, 0.90]
    cooperator_betas = jnp.linspace(0.10, 0.90, 17)
    num_episodes = 1000
    
    print(f"{'Freerider%':<11} | {'Cooperator_Beta':<15} | {'Collective_Avg_Beta':<19} | {'Survival_Rate':<13} | {'Variance'}")
    print("-" * 80)
    
    # We compile the inner loop function which takes beta_array directly.
    # beta_array is fixed shape (num_machines,) so JIT works across calls.
    def run_single_combination(base_rng, beta_array):
        # We vmap over the environment episodes
        reset_fn = jax.vmap(env.reset, in_axes=(0, None, None))
        step_fn = jax.vmap(env.step, in_axes=(0, 0, 0, None))
        
        rngs = jax.random.split(base_rng, num_episodes)
        obs, state = reset_fn(rngs, params, beta_array)
        
        def episode_step(runner_state, _):
            state, step_rng = runner_state
            step_rng, action_rng = jax.random.split(step_rng)
            action_rngs = jax.random.split(action_rng, num_episodes)
            
            # Calibrated baseline policy to match nature's submit cap
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
        
        final_survival_f = survived_history[-1].astype(jnp.float32)
        return jnp.mean(final_survival_f), jnp.var(final_survival_f)

    # JIT the runner so it is compiled once and executes rapidly for each combination
    compiled_runner = jax.jit(run_single_combination)
    
    results_summary = []
    
    idx = 0
    t0 = time.time()
    for fr in freerider_ratios:
        num_freeriders = int(fr * params.num_machines)
        
        min_avg_beta_for_100 = 1.0
        
        for cb in cooperator_betas:
            # Construct beta array
            beta_array = jnp.concatenate([
                jnp.zeros(num_freeriders),
                jnp.full(params.num_machines - num_freeriders, cb)
            ])
            
            collective_avg_beta = jnp.mean(beta_array)
            
            # Seed reproducible per combination
            base_rng = jax.random.PRNGKey(42 + idx)
            idx += 1
            
            survival_rate, survival_var = compiled_runner(base_rng, beta_array)
            # Fetch arrays from device
            surv_r = np.array(survival_rate)
            surv_v = np.array(survival_var)
            
            marker = ""
            if fr == 0.75 and abs(collective_avg_beta - 0.198) <= 0.02:
                marker = "  ★ ORIGINAL FINDING"
                
            print(f"{fr * 100:>9.1f}% | {cb:15.3f} | {collective_avg_beta:19.4f} | {surv_r:12.1%} | {surv_v:.4f}{marker}")
            
            if surv_r == 1.0 and collective_avg_beta < min_avg_beta_for_100:
                min_avg_beta_for_100 = collective_avg_beta
                
        results_summary.append((fr, min_avg_beta_for_100))
        print("-" * 80)
        
    t1 = time.time()
    print(f"\nExecution time: {t1 - t0:.2f} seconds.")
    print("\n★ Minimum collective avg beta for 100% survival per freerider ratio")
    for fr, min_b in results_summary:
        print(f"  Freerider {fr * 100:.1f}% -> Min Avg Beta: {min_b:.4f}")

if __name__ == "__main__":
    print("=" * 80)
    print("  SocialJax PoC: Sim 23 - Heterogeneous Population (Freeriders)")
    print("=" * 80)
    evaluate_heterogeneous()
