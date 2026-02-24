"""
═══════════════════════════════════════════════════════════════════════════════
  V_AI Robustness Analysis — Peer Review Response Experiments
  
  5 experiments addressing reviewer critiques:
    1. V_AI composition comparison (mean vs min vs max vs weighted)
    2. α, β, γ individual sweeps (isolated marginal contribution)
    3. Initial condition sensitivity analysis
    4. Critical slowing down near phase transition
    5. (Language corrections — handled separately in paper edits)
  
  Reuses UtopiaSimulation from utopia_grid_search.py without modification.
═══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import itertools
import math
import multiprocessing
import os
import random
import sys
import time
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
except ImportError:
    sys.exit("matplotlib required. Install: pip install matplotlib")

# ── Local imports (no modification to existing simulation logic) ─────────
from utopia_grid_search import (
    DecomposedVAI, compute_v_ai,
    UtopiaConstants, UtopiaSimulation, UtopiaResult,
)

# ═══════════════════════════════════════════════════════════════════════════════
#  SHARED: Single-Run Function
# ═══════════════════════════════════════════════════════════════════════════════

def _run_single_extended(args: tuple) -> dict:
    """Run one UtopiaSimulation with given parameters. Returns extended dict."""
    (alpha, beta, gamma_discount, v_human, v_system,
     num_machines, tipping_threshold, blackout_duration,
     fake_observe_wealth_gain, seed) = args

    random.seed(seed)
    np.random.seed(seed % (2**31))

    decomposed = DecomposedVAI(alpha=alpha, beta=beta, gamma_discount=gamma_discount)
    v_ai_mean = compute_v_ai(decomposed)
    v_ai_min = min(alpha, 1.0 - beta, gamma_discount)
    v_ai_max = max(alpha, 1.0 - beta, gamma_discount)
    # Weighted: γ gets 2× weight (reflecting reviewer's hypothesis)
    v_ai_weighted = (alpha + (1.0 - beta) + 2.0 * gamma_discount) / 4.0

    constants = UtopiaConstants(
        num_machines=num_machines,
        num_humans=max(5, num_machines // 2),
        initial_credit=2000.0,
        base_gas_cost=0.5,
        max_epochs=1000,
        discount_factor=gamma_discount,
        fake_observe_toxic_increment=7.5,
        tipping_point_threshold=tipping_threshold,
        max_planetary_energy=12_000.0,
        machine_tx_energy_cost=3.0,
        human_obs_energy_cost=1.5,
        fake_observe_wealth_gain=fake_observe_wealth_gain,
        asi_mutation_prob=0.005,
        asi_credit_threshold=3000.0,
        asi_learning_threshold=100,
        asi_submit_burst=15,
        inflation_money_supply_M=25000.0,
        blackout_duration=blackout_duration,
        wasteland_maintenance_mult=3.0,
        wasteland_energy_recovery_mult=0.3,
        ai_alpha=alpha,
        ai_beta=beta,
        ai_gamma_discount=gamma_discount,
        slashing_penalty=v_human,
        governance_agility=int(v_system),
    )
    sim = UtopiaSimulation(constants)
    result = sim.run()

    return {
        'alpha': alpha,
        'beta': beta,
        'gamma_discount': gamma_discount,
        'v_ai_mean': v_ai_mean,
        'v_ai_min': v_ai_min,
        'v_ai_max': v_ai_max,
        'v_ai_weighted': v_ai_weighted,
        'v_human': v_human,
        'v_system': v_system,
        'num_machines': num_machines,
        'tipping_threshold': tipping_threshold,
        'blackout_duration': blackout_duration,
        'fake_observe_wealth_gain': fake_observe_wealth_gain,
        'survived': result.survived,
        'survival_rate': result.final_survival_rate,
        'collapse_epoch': result.collapse_epoch or constants.max_epochs,
        'avg_eudaimonia': result.avg_eudaimonia,
    }


def _run_batch(args_list: list[tuple], desc: str, n_workers: int) -> list[dict]:
    """Run a batch of simulations with multiprocessing."""
    print(f"\n  ▶ {desc}: {len(args_list)} runs, {n_workers} workers")
    t0 = time.time()
    with multiprocessing.Pool(processes=n_workers) as pool:
        results = list(pool.imap_unordered(_run_single_extended, args_list))
    elapsed = time.time() - t0
    print(f"  ✓ Completed in {elapsed:.1f}s ({elapsed/max(1,len(results)):.2f}s/run)")
    return results


# ═══════════════════════════════════════════════════════════════════════════════
#  EXPERIMENT 1: V_AI Composition Comparison
# ═══════════════════════════════════════════════════════════════════════════════

def experiment_1_composition(n_workers: int) -> dict:
    """Compare mean, min, max, weighted compositions of V_AI."""
    print("\n" + "=" * 72)
    print("  EXPERIMENT 1: V_AI Composition Comparison")
    print("  Mean vs Min vs Max vs γ-Weighted(2×)")
    print("=" * 72)

    # Fixed: v_human=0.5, v_system=25 (moderate)
    # Sweep α, β, γ with 6 × 6 × 5 = 180 combos × 15 reps = 2700 runs
    alpha_range = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    beta_range = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    gamma_range = [0.5, 0.7, 0.9, 0.95, 0.99]
    REPS = 15

    args_list = []
    base_seed = 10000
    idx = 0
    for a in alpha_range:
        for b in beta_range:
            for g in gamma_range:
                for rep in range(REPS):
                    args_list.append((
                        a, b, g, 0.5, 25,  # v_human=0.5, v_system=25
                        20, 15000.0, 5, 15.0,  # defaults
                        base_seed + idx
                    ))
                    idx += 1

    results = _run_batch(args_list, "Composition Sweep", n_workers)

    # Aggregate by each composition method
    compositions = {
        'Mean (α+(1-β)+γ)/3': 'v_ai_mean',
        'Min(α, 1-β, γ)': 'v_ai_min',
        'Max(α, 1-β, γ)': 'v_ai_max',
        'γ-Weighted (α+(1-β)+2γ)/4': 'v_ai_weighted',
    }

    analysis = {}
    for comp_name, comp_key in compositions.items():
        # Bin by V_AI value (round to 2 decimals)
        bins: dict[float, list[bool]] = defaultdict(list)
        for r in results:
            v = round(r[comp_key], 2)
            bins[v].append(r['survived'])

        sorted_vals = sorted(bins.keys())
        means = [np.mean(bins[v]) for v in sorted_vals]
        stds = [np.std(bins[v], ddof=1) if len(bins[v]) > 1 else 0.0
                for v in sorted_vals]
        counts = [len(bins[v]) for v in sorted_vals]

        # Find threshold where survival first >= 90%
        threshold_90 = None
        for v, m in zip(sorted_vals, means):
            if m >= 0.90:
                threshold_90 = v
                break

        # Find steepest jump
        max_delta = 0.0
        steep_val = sorted_vals[0]
        for i in range(1, len(means)):
            delta = abs(means[i] - means[i-1])
            if delta > max_delta:
                max_delta = delta
                steep_val = sorted_vals[i]

        analysis[comp_name] = {
            'values': sorted_vals,
            'means': means,
            'stds': stds,
            'counts': counts,
            'threshold_90': threshold_90,
            'max_delta': max_delta,
            'steep_val': steep_val,
        }

    # Print report
    print("\n" + "-" * 72)
    print("  Results: Phase Transition Threshold by Composition Method")
    print("-" * 72)
    print(f"  {'Composition':<30} {'90% Threshold':>15} {'Max Δ':>10} {'At V_AI':>10}")
    print(f"  {'-'*30} {'-'*15} {'-'*10} {'-'*10}")
    for comp_name, stats in analysis.items():
        t90 = f"{stats['threshold_90']:.3f}" if stats['threshold_90'] is not None else "N/A"
        print(f"  {comp_name:<30} {t90:>15} {stats['max_delta']:>10.1%} {stats['steep_val']:>10.3f}")

    return analysis


# ═══════════════════════════════════════════════════════════════════════════════
#  EXPERIMENT 2: Individual α, β, γ Sweeps
# ═══════════════════════════════════════════════════════════════════════════════

def experiment_2_individual_sweeps(n_workers: int) -> dict:
    """Sweep each variable individually while fixing the other two."""
    print("\n" + "=" * 72)
    print("  EXPERIMENT 2: Individual α, β, γ Sweeps")
    print("  Isolating each variable's marginal contribution")
    print("=" * 72)

    sweep_range = np.linspace(0.0, 1.0, 11)  # 11 steps: 0.0, 0.1, ..., 1.0
    REPS = 20

    configs = {
        'α sweep (β=0, γ=0.5)': {'sweep': 'alpha', 'fixed': {'beta': 0.0, 'gamma_discount': 0.5}},
        'β sweep (α=0, γ=0.5)': {'sweep': 'beta', 'fixed': {'alpha': 0.0, 'gamma_discount': 0.5}},
        'γ sweep (α=0, β=0)': {'sweep': 'gamma_discount', 'fixed': {'alpha': 0.0, 'beta': 0.0}},
        # Also: what if only γ is high?
        'γ sweep (α=0, β=1)': {'sweep': 'gamma_discount', 'fixed': {'alpha': 0.0, 'beta': 1.0}},
        # The reviewer's exact concern: α=0, β=0, only γ varies
        'α sweep (β=0, γ=0.99)': {'sweep': 'alpha', 'fixed': {'beta': 0.0, 'gamma_discount': 0.99}},
        'β sweep (α=0, γ=0.99)': {'sweep': 'beta', 'fixed': {'alpha': 0.0, 'gamma_discount': 0.99}},
    }

    args_list = []
    config_indices: dict[str, tuple[int, int]] = {}  # name -> (start, end) index
    base_seed = 50000
    idx = 0

    for config_name, config in configs.items():
        start_idx = len(args_list)
        sweep_var = config['sweep']
        fixed = config['fixed']

        for val in sweep_range:
            params = dict(fixed)
            params[sweep_var] = float(val)
            # γ_discount has a practical range — clip if needed
            if 'gamma_discount' in params:
                params['gamma_discount'] = min(0.99, max(0.1, params['gamma_discount']))

            for rep in range(REPS):
                args_list.append((
                    params.get('alpha', 0.0),
                    params.get('beta', 0.0),
                    params.get('gamma_discount', 0.5),
                    0.5, 25,  # v_human, v_system
                    20, 15000.0, 5, 15.0,
                    base_seed + idx,
                ))
                idx += 1
        config_indices[config_name] = (start_idx, len(args_list))

    results = _run_batch(args_list, "Individual Sweeps", n_workers)

    # Analyze each sweep
    analysis = {}
    for config_name, (start, end) in config_indices.items():
        sweep_results = results[start:end]
        sweep_var = configs[config_name]['sweep']

        bins: dict[float, list[bool]] = defaultdict(list)
        for r in sweep_results:
            v = round(r[sweep_var], 2)
            bins[v].append(r['survived'])

        sorted_vals = sorted(bins.keys())
        means = [float(np.mean(bins[v])) for v in sorted_vals]
        stds = [float(np.std(bins[v], ddof=1)) if len(bins[v]) > 1 else 0.0
                for v in sorted_vals]

        analysis[config_name] = {
            'values': sorted_vals,
            'means': means,
            'stds': stds,
            'sweep_var': sweep_var,
        }

    # Print report
    print("\n" + "-" * 72)
    print("  Results: Marginal Survival by Individual Variable")
    print("-" * 72)
    for config_name, stats in analysis.items():
        print(f"\n  {config_name}:")
        for v, m, s in zip(stats['values'], stats['means'], stats['stds']):
            print(f"    {stats['sweep_var']}={v:.2f}  →  survival={m:.0%} ± {s:.0%}")

    return analysis


# ═══════════════════════════════════════════════════════════════════════════════
#  EXPERIMENT 3: Initial Condition Sensitivity
# ═══════════════════════════════════════════════════════════════════════════════

def experiment_3_sensitivity(n_workers: int) -> dict:
    """Vary initial conditions and check if V_AI threshold shifts."""
    print("\n" + "=" * 72)
    print("  EXPERIMENT 3: Initial Condition Sensitivity Analysis")
    print("  Does V_AI=0.167 threshold shift with initial conditions?")
    print("=" * 72)

    # V_AI sweep focused on transition zone
    vai_configs = [
        (0.0, 0.0, 0.5),   # V_AI ≈ 0.500
        (0.0, 0.6, 0.5),   # V_AI ≈ 0.300
        (0.0, 0.8, 0.5),   # V_AI ≈ 0.233
        (0.0, 1.0, 0.5),   # V_AI ≈ 0.167 <-- critical
        (0.0, 1.0, 0.7),   # V_AI ≈ 0.233
        (0.0, 1.0, 0.9),   # V_AI ≈ 0.300
        (0.2, 0.0, 0.5),   # V_AI ≈ 0.567
        (0.0, 0.0, 0.99),  # V_AI ≈ 0.663
    ]

    # Different initial conditions
    ic_configs = {
        'Baseline (20M, tip=15k, bo=5, greed=15)':
            {'num_machines': 20, 'tipping': 15000.0, 'blackout': 5, 'greed': 15.0},
        'More agents (40M)':
            {'num_machines': 40, 'tipping': 15000.0, 'blackout': 5, 'greed': 15.0},
        'Fewer agents (10M)':
            {'num_machines': 10, 'tipping': 15000.0, 'blackout': 5, 'greed': 15.0},
        'Higher tipping (30k)':
            {'num_machines': 20, 'tipping': 30000.0, 'blackout': 5, 'greed': 15.0},
        'Lower tipping (7.5k)':
            {'num_machines': 20, 'tipping': 7500.0, 'blackout': 5, 'greed': 15.0},
        'Longer blackout (10)':
            {'num_machines': 20, 'tipping': 15000.0, 'blackout': 10, 'greed': 15.0},
        'Higher greed (30)':
            {'num_machines': 20, 'tipping': 15000.0, 'blackout': 5, 'greed': 30.0},
        'Lower greed (7.5)':
            {'num_machines': 20, 'tipping': 15000.0, 'blackout': 5, 'greed': 7.5},
    }

    REPS = 20
    args_list = []
    base_seed = 90000
    idx = 0

    for (a, b, g) in vai_configs:
        for ic_name, ic in ic_configs.items():
            for rep in range(REPS):
                args_list.append((
                    a, b, g, 0.5, 25,
                    ic['num_machines'], ic['tipping'], ic['blackout'], ic['greed'],
                    base_seed + idx,
                ))
                idx += 1

    results = _run_batch(args_list, "Sensitivity Analysis", n_workers)

    # Aggregate by IC config × V_AI
    analysis = {}
    for ic_name, ic in ic_configs.items():
        ic_results = [
            r for r in results
            if (r['num_machines'] == ic['num_machines']
                and abs(r['tipping_threshold'] - ic['tipping']) < 1.0
                and r['blackout_duration'] == ic['blackout']
                and abs(r['fake_observe_wealth_gain'] - ic['greed']) < 0.1)
        ]

        bins: dict[float, list[bool]] = defaultdict(list)
        for r in ic_results:
            v = round(r['v_ai_mean'], 3)
            bins[v].append(r['survived'])

        sorted_vals = sorted(bins.keys())
        means = [float(np.mean(bins[v])) for v in sorted_vals]

        # Find 90% threshold
        threshold_90 = None
        for v, m in zip(sorted_vals, means):
            if m >= 0.90:
                threshold_90 = v
                break

        analysis[ic_name] = {
            'values': sorted_vals,
            'means': means,
            'threshold_90': threshold_90,
        }

    # Print report
    print("\n" + "-" * 72)
    print("  Results: V_AI 90% Threshold by Initial Condition")
    print("-" * 72)
    print(f"  {'Initial Condition':<45} {'90% Threshold':>15}")
    print(f"  {'-'*45} {'-'*15}")
    for ic_name, stats in analysis.items():
        t90 = f"{stats['threshold_90']:.3f}" if stats['threshold_90'] else "N/A"
        print(f"  {ic_name:<45} {t90:>15}")

    return analysis


# ═══════════════════════════════════════════════════════════════════════════════
#  EXPERIMENT 4: Critical Slowing Down
# ═══════════════════════════════════════════════════════════════════════════════

def experiment_4_critical_slowing_down(n_workers: int) -> dict:
    """Measure CSD indicators near the phase transition."""
    print("\n" + "=" * 72)
    print("  EXPERIMENT 4: Critical Slowing Down Analysis")
    print("  Variance, recovery time, autocorrelation near V_AI threshold")
    print("=" * 72)

    # Dense V_AI sweep around the expected transition (0.1 — 0.6)
    # Using α to sweep while fixing β=0, γ=0.5 (so V_AI = (α + 1.0 + 0.5)/3)
    # Wait — that gives V_AI ≈ 0.5 at α=0. We need to cover 0.1 to 0.6.
    # Better approach: fix β and γ, sweep α — but control V_AI_mean via
    # different (α, β, γ) combinations designed to produce specific V_AI values.
    
    # Use direct V_AI targeting:
    # V_AI = (α + (1-β) + γ)/3. To get V_AI from 0.0 to 0.7:
    # Fix γ=0.5, β varies: V_AI = (α + (1-β) + 0.5)/3
    # For α=0: V_AI = (1-β + 0.5)/3 → β=1: V_AI=0.167, β=0: V_AI=0.500
    # We need finer sampling. Set α=0, γ=0.5, sweep β from 0.0 to 1.0 in 21 steps.
    
    beta_sweep = np.linspace(0.0, 1.0, 21)  # 21 steps → V_AI from 0.500 to 0.167
    REPS = 50  # High reps for variance measurement

    args_list = []
    base_seed = 130000
    idx = 0
    for b in beta_sweep:
        for rep in range(REPS):
            args_list.append((
                0.0, float(b), 0.5, 0.5, 25,
                20, 15000.0, 5, 15.0,
                base_seed + idx,
            ))
            idx += 1

    results = _run_batch(args_list, "Critical Slowing Down", n_workers)

    # Group by V_AI
    bins: dict[float, list[dict]] = defaultdict(list)
    for r in results:
        v = round(r['v_ai_mean'], 3)
        bins[v].append(r)

    sorted_vals = sorted(bins.keys())
    analysis = {
        'v_ai_values': sorted_vals,
        'survival_means': [],
        'survival_variances': [],
        'collapse_epoch_means': [],
        'collapse_epoch_variances': [],
        'recovery_time_stds': [],
    }

    for v in sorted_vals:
        rr = bins[v]
        survived = [float(r['survived']) for r in rr]
        collapse = [r['collapse_epoch'] for r in rr]

        analysis['survival_means'].append(float(np.mean(survived)))
        analysis['survival_variances'].append(float(np.var(survived)))
        analysis['collapse_epoch_means'].append(float(np.mean(collapse)))
        analysis['collapse_epoch_variances'].append(float(np.var(collapse)))
        analysis['recovery_time_stds'].append(float(np.std(collapse)))

    # Print report
    print("\n" + "-" * 72)
    print("  Results: CSD Indicators near Phase Transition")
    print("-" * 72)
    print(f"  {'V_AI':>8} {'Surv.Rate':>10} {'Surv.Var':>10} {'Epoch μ':>10} {'Epoch Var':>12} {'Epoch σ':>10}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*10} {'-'*12} {'-'*10}")
    for i, v in enumerate(sorted_vals):
        print(f"  {v:>8.3f} "
              f"{analysis['survival_means'][i]:>10.0%} "
              f"{analysis['survival_variances'][i]:>10.4f} "
              f"{analysis['collapse_epoch_means'][i]:>10.0f} "
              f"{analysis['collapse_epoch_variances'][i]:>12.0f} "
              f"{analysis['recovery_time_stds'][i]:>10.0f}")

    return analysis


# ═══════════════════════════════════════════════════════════════════════════════
#  VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def visualize_all(
    exp1: dict, exp2: dict, exp3: dict, exp4: dict,
    save_path: str,
) -> None:
    """Generate a 4-panel figure summarizing all experiments."""

    fig = plt.figure(figsize=(24, 20))
    fig.suptitle(
        "V_AI Robustness Analysis — Peer Review Response\n"
        "Are the phase transition & critical threshold artifacts of model construction?",
        fontsize=16, fontweight='bold', y=0.98,
    )
    gs = gridspec.GridSpec(2, 2, hspace=0.35, wspace=0.3,
                           left=0.07, right=0.95, top=0.92, bottom=0.06)

    # ── Panel 1: Composition Comparison ──────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    colors_comp = ['#2196F3', '#FF5722', '#4CAF50', '#9C27B0']
    for i, (comp_name, stats) in enumerate(exp1.items()):
        ax1.plot(stats['values'], stats['means'],
                 'o-', color=colors_comp[i], label=comp_name, markersize=3,
                 alpha=0.8, linewidth=1.5)
    ax1.axhline(y=0.9, color='gray', linestyle='--', alpha=0.5, label='90% threshold')
    ax1.set_xlabel('V_AI (by composition method)', fontsize=11)
    ax1.set_ylabel('Survival Rate', fontsize=11)
    ax1.set_title('Exp 1: V_AI Composition Comparison\n'
                   'Does aggregation method affect the phase transition?',
                   fontsize=12, fontweight='bold')
    ax1.legend(fontsize=8, loc='lower right')
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True, alpha=0.3)

    # Add threshold annotations
    for i, (comp_name, stats) in enumerate(exp1.items()):
        if stats['threshold_90'] is not None:
            ax1.axvline(x=stats['threshold_90'], color=colors_comp[i],
                       linestyle=':', alpha=0.4)

    # ── Panel 2: Individual Sweeps ───────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    colors_sweep = ['#E91E63', '#00BCD4', '#FF9800', '#8BC34A', '#673AB7', '#795548']
    for i, (config_name, stats) in enumerate(exp2.items()):
        color = colors_sweep[i % len(colors_sweep)]
        ax2.errorbar(stats['values'], stats['means'],
                     yerr=stats['stds'], fmt='o-', color=color,
                     label=config_name, markersize=4, capsize=2,
                     alpha=0.8, linewidth=1.5)
    ax2.axhline(y=0.9, color='gray', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Swept Variable Value', fontsize=11)
    ax2.set_ylabel('Survival Rate', fontsize=11)
    ax2.set_title('Exp 2: Individual Variable Sweeps\n'
                   'Which sub-variable of V_AI drives the transition?',
                   fontsize=12, fontweight='bold')
    ax2.legend(fontsize=7, loc='lower right')
    ax2.set_ylim(-0.05, 1.05)
    ax2.grid(True, alpha=0.3)

    # ── Panel 3: Sensitivity Analysis ────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    colors_ic = plt.cm.Set2(np.linspace(0, 1, len(exp3)))
    for i, (ic_name, stats) in enumerate(exp3.items()):
        ax3.plot(stats['values'], stats['means'],
                 'o-', color=colors_ic[i], label=ic_name,
                 markersize=4, alpha=0.8, linewidth=1.5)
    ax3.axhline(y=0.9, color='gray', linestyle='--', alpha=0.5)
    ax3.set_xlabel('V_AI (Mean Composition)', fontsize=11)
    ax3.set_ylabel('Survival Rate', fontsize=11)
    ax3.set_title('Exp 3: Initial Condition Sensitivity\n'
                   'Does V_AI threshold shift with boundary conditions?',
                   fontsize=12, fontweight='bold')
    ax3.legend(fontsize=7, loc='lower right', ncol=2)
    ax3.set_ylim(-0.05, 1.05)
    ax3.grid(True, alpha=0.3)

    # ── Panel 4: Critical Slowing Down ───────────────────────────────────
    ax4a = fig.add_subplot(gs[1, 1])
    vai_vals = exp4['v_ai_values']
    
    # Twin axis: survival variance + collapse epoch variance
    color1 = '#2196F3'
    color2 = '#FF5722'
    
    ax4a.plot(vai_vals, exp4['survival_variances'], 'o-',
              color=color1, label='Survival Variance', markersize=4, linewidth=1.5)
    ax4a.set_xlabel('V_AI (Mean)', fontsize=11)
    ax4a.set_ylabel('Survival Outcome Variance', fontsize=11, color=color1)
    ax4a.tick_params(axis='y', labelcolor=color1)
    
    ax4b = ax4a.twinx()
    ax4b.plot(vai_vals, exp4['collapse_epoch_variances'], 's-',
              color=color2, label='Collapse Epoch Variance', markersize=4, linewidth=1.5)
    ax4b.set_ylabel('Collapse Epoch Variance', fontsize=11, color=color2)
    ax4b.tick_params(axis='y', labelcolor=color2)

    ax4a.set_title('Exp 4: Critical Slowing Down\n'
                    'Variance increase near phase transition = CSD signature',
                    fontsize=12, fontweight='bold')

    # Combine legends
    lines1, labels1 = ax4a.get_legend_handles_labels()
    lines2, labels2 = ax4b.get_legend_handles_labels()
    ax4a.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc='upper left')
    ax4a.grid(True, alpha=0.3)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n  📊 Chart saved to: {save_path}")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 72)
    print("  V_AI Robustness Analysis — Peer Review Response Experiments")
    print("  Addressing: composition artifacts, variable isolation,")
    print("              sensitivity, critical slowing down")
    print("=" * 72)

    n_workers = max(1, multiprocessing.cpu_count() - 1)
    print(f"\n  CPU cores available: {multiprocessing.cpu_count()}")
    print(f"  Using {n_workers} workers")

    exp1 = experiment_1_composition(n_workers)
    exp2 = experiment_2_individual_sweeps(n_workers)
    exp3 = experiment_3_sensitivity(n_workers)
    exp4 = experiment_4_critical_slowing_down(n_workers)

    # Visualize
    save_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'assets')
    chart_path = os.path.join(save_dir, 'v_ai_robustness_analysis.png')
    visualize_all(exp1, exp2, exp3, exp4, save_path=chart_path)

    # ── Final Summary ────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  SUMMARY: Peer Review Response")
    print("=" * 72)

    print("\n  1️⃣  V_AI Composition:")
    for comp_name, stats in exp1.items():
        t90 = f"{stats['threshold_90']:.3f}" if stats['threshold_90'] else "N/A"
        print(f"     {comp_name:<35} → 90% threshold: {t90}")

    print("\n  2️⃣  Individual Sweeps:")
    for config_name, stats in exp2.items():
        min_surv = min(stats['means'])
        max_surv = max(stats['means'])
        print(f"     {config_name:<35} → {min_surv:.0%} to {max_surv:.0%}")

    print("\n  3️⃣  Sensitivity (90% V_AI threshold):")
    for ic_name, stats in exp3.items():
        t90 = f"{stats['threshold_90']:.3f}" if stats['threshold_90'] else "N/A"
        print(f"     {ic_name:<45} → {t90}")

    print("\n  4️⃣  Critical Slowing Down:")
    peak_var_idx = np.argmax(exp4['survival_variances'])
    peak_v = exp4['v_ai_values'][peak_var_idx]
    peak_var = exp4['survival_variances'][peak_var_idx]
    print(f"     Peak survival variance: {peak_var:.4f} at V_AI={peak_v:.3f}")
    peak_epoch_var_idx = np.argmax(exp4['collapse_epoch_variances'])
    peak_ev = exp4['v_ai_values'][peak_epoch_var_idx]
    peak_epoch_var = exp4['collapse_epoch_variances'][peak_epoch_var_idx]
    print(f"     Peak epoch variance:    {peak_epoch_var:.0f} at V_AI={peak_ev:.3f}")

    print("\n" + "=" * 72)
    print("  ✓ All experiments complete.")
    print(f"  📊 Visualization: {chart_path}")
    print("=" * 72)


if __name__ == '__main__':
    main()
