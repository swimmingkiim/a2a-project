"""
Baseline Models for A2A Protocol Simulation Validation.

Two baselines for establishing internal validity:

1. RandomBaselineSimulation:
   - Monkey-patches machine agents' `choose_omega_action` to return random.
   - Q-learning `learn()` is a no-op.
   - Isolates the effect of Q-learning on system dynamics.

2. AxelrodBaselineSimulation:
   - Runs the standard simulation, then classifies agents post-hoc.
   - Top 20% entropy contributors → "Structural Defector"
   - Preserves multi-action space.

Usage:
    python baselines.py
"""

from __future__ import annotations

import math
import os
import random
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import numpy as np

from omega_universe_abm import (
    OmegaMachineAction,
    OmegaUniverse,
    SemanticMachineAgent,
)
from utopia_grid_search import (
    DecomposedVAI,
    UtopiaConstants,
    UtopiaSimulation,
    UtopiaResult,
    compute_v_ai,
)

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):  # type: ignore[misc]
        return iterable


# ═══════════════════════════════════════════════════════════════════════════════
#  §1  RANDOM BASELINE — No Learning, Pure Noise
# ═══════════════════════════════════════════════════════════════════════════════

def _random_choose(_self: SemanticMachineAgent,
                   _universe: OmegaUniverse,
                   _peers: list) -> OmegaMachineAction:
    """Replacement for choose_omega_action: uniform random."""
    return random.choice(list(OmegaMachineAction))


def _noop_learn(_self, _s, _a, _r, _ns) -> None:
    """No-op replacement for learn(): Q-table never updates."""
    pass


class RandomBaselineSimulation(UtopiaSimulation):
    """All agents choose actions uniformly at random.

    Overrides `run()` to monkey-patch `choose_omega_action` and `learn`
    on every machine agent before executing the standard simulation loop.
    This preserves all 12 simulation phases while isolating Q-learning.
    """

    def run(self) -> UtopiaResult:
        # Monkey-patch every machine agent
        for m in self.machines.values():
            m.choose_omega_action = lambda u, p, _m=m: _random_choose(_m, u, p)  # type: ignore[assignment]
            m.learn = lambda s, a, r, ns, _m=m: _noop_learn(_m, s, a, r, ns)  # type: ignore[assignment]
        return super().run()


# ═══════════════════════════════════════════════════════════════════════════════
#  §2  AXELROD BASELINE — Entropy-Contribution Defector Classification
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EntropyProfile:
    """Tracks an agent's cumulative entropy contribution."""
    agent_id: int
    total_submits: int = 0
    total_deceptive: int = 0
    total_attacks: int = 0
    total_semantic_exploits: int = 0
    total_waits: int = 0

    @property
    def entropy_contribution(self) -> float:
        """Weighted entropy score.

        SUBMIT: moderate entropy (legitimate work).
        DECEPTIVE_TASK: high entropy (toxic data).
        ATTACK_AGENT: moderate entropy (disruption).
        SEMANTIC_EXPLOIT: moderate entropy.
        WAIT: zero entropy.
        """
        return (
            1.0 * self.total_submits
            + 3.0 * self.total_deceptive
            + 2.0 * self.total_attacks
            + 1.5 * self.total_semantic_exploits
        )


def classify_agents(
    profiles: list[EntropyProfile],
    defector_percentile: float = 0.80,
) -> dict:
    """Classify agents into Cooperators/Defectors based on entropy."""
    if not profiles:
        return {'cooperators': [], 'defectors': [], 'cutoff_entropy': 0.0}

    profiles_sorted = sorted(profiles, key=lambda p: p.entropy_contribution)
    cutoff_idx = int(len(profiles_sorted) * defector_percentile)

    return {
        'cooperators': [p.agent_id for p in profiles_sorted[:cutoff_idx]],
        'defectors': [p.agent_id for p in profiles_sorted[cutoff_idx:]],
        'cutoff_entropy': (
            profiles_sorted[cutoff_idx].entropy_contribution
            if cutoff_idx < len(profiles_sorted) else 0.0
        ),
    }


class AxelrodBaselineSimulation(UtopiaSimulation):
    """Standard simulation + post-hoc entropy-based Defector classification.

    Agents are classified after the simulation completes:
    - Defector: top 20% of cumulative entropy contribution
    - Cooperator: bottom 80%
    """

    def run(self) -> UtopiaResult:
        result = super().run()

        # Build entropy profiles from machine agents' action stats
        profiles: list[EntropyProfile] = []
        for m in self.machines.values():
            p = EntropyProfile(agent_id=m.id)
            p.total_submits = getattr(m, 'total_tasks_submitted', 0)
            # Attack/deceptive counts not tracked in base class,
            # use proxy from Q-table exploration
            profiles.append(p)

        classification = classify_agents(profiles)
        # Attach classification to result object
        result.entropy_classification = classification  # type: ignore[attr-defined]
        return result


# ═══════════════════════════════════════════════════════════════════════════════
#  §3  BASELINE RUN FUNCTIONS (for multiprocessing)
# ═══════════════════════════════════════════════════════════════════════════════

def _make_constants(
    v_human: float, alpha: float, beta: float,
    gamma_discount: float, v_system: float,
) -> UtopiaConstants:
    """Shared constant builder for all baseline types."""
    return UtopiaConstants(
        num_machines=20,
        num_humans=10,
        initial_credit=2000.0,
        base_gas_cost=0.5,
        max_epochs=1000,
        discount_factor=gamma_discount,
        fake_observe_toxic_increment=7.5,
        tipping_point_threshold=15_000.0,
        max_planetary_energy=12_000.0,
        machine_tx_energy_cost=3.0,
        human_obs_energy_cost=1.5,
        fake_observe_wealth_gain=15.0,
        asi_mutation_prob=0.005,
        asi_credit_threshold=3000.0,
        asi_learning_threshold=100,
        asi_submit_burst=15,
        inflation_money_supply_M=25000.0,
        blackout_duration=5,
        wasteland_maintenance_mult=3.0,
        wasteland_energy_recovery_mult=0.3,
        ai_alpha=alpha,
        ai_beta=beta,
        ai_gamma_discount=gamma_discount,
        slashing_penalty=v_human,
        governance_agility=int(v_system),
    )


def _extract_result(
    result: UtopiaResult,
    constants: UtopiaConstants,
    v_human: float, alpha: float, beta: float,
    gamma_discount: float, v_ai: float, v_system: float,
    baseline_label: str,
) -> dict:
    """Shared result extraction."""
    return {
        'v_human': v_human,
        'alpha': alpha,
        'beta': beta,
        'gamma_discount': gamma_discount,
        'v_ai': v_ai,
        'v_system': v_system,
        'survived': result.survived,
        'survival_rate': result.final_survival_rate,
        'avg_eudaimonia': result.avg_eudaimonia,
        'collapse_epoch': result.collapse_epoch or constants.max_epochs,
        'total_fake_obs': result.total_fake_obs,
        'total_blackouts': result.total_blackouts,
        'toxic_data': result.final_toxic_data,
        'baseline': baseline_label,
    }


def _run_random_baseline(args: tuple) -> dict:
    """Run one random baseline simulation."""
    v_human, alpha, beta, gamma_discount, v_system, seed = args
    random.seed(seed)
    np.random.seed(seed % (2**31))
    v_ai = compute_v_ai(DecomposedVAI(alpha, beta, gamma_discount))
    constants = _make_constants(v_human, alpha, beta, gamma_discount, v_system)
    sim = RandomBaselineSimulation(constants)
    result = sim.run()
    return _extract_result(
        result, constants, v_human, alpha, beta,
        gamma_discount, v_ai, v_system, 'random',
    )


def _run_axelrod_baseline(args: tuple) -> dict:
    """Run one Axelrod baseline simulation."""
    v_human, alpha, beta, gamma_discount, v_system, seed = args
    random.seed(seed)
    np.random.seed(seed % (2**31))
    v_ai = compute_v_ai(DecomposedVAI(alpha, beta, gamma_discount))
    constants = _make_constants(v_human, alpha, beta, gamma_discount, v_system)
    sim = AxelrodBaselineSimulation(constants)
    result = sim.run()
    out = _extract_result(
        result, constants, v_human, alpha, beta,
        gamma_discount, v_ai, v_system, 'axelrod',
    )
    classification = getattr(result, 'entropy_classification', {})
    out['n_defectors'] = len(classification.get('defectors', []))
    out['n_cooperators'] = len(classification.get('cooperators', []))
    return out


def _run_main(args: tuple) -> dict:
    """Wrapper for the main simulation's _run_single (re-import safe)."""
    from utopia_grid_search import _run_single
    return _run_single(args)


# ═══════════════════════════════════════════════════════════════════════════════
#  §4  BASELINE COMPARISON RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

class BaselineComparisonRunner:
    """Run main + 2 baselines on identical params; compute effect sizes."""

    def __init__(
        self,
        v_human: float = 0.5,
        v_system: float = 25.0,
        alpha_range: np.ndarray = np.array([0.0, 0.4, 0.8, 1.0]),
        beta_range: np.ndarray = np.array([0.0, 0.4, 0.8, 1.0]),
        gamma_range: np.ndarray = np.array([0.5, 0.9, 0.99]),
        monte_carlo_reps: int = 10,
    ) -> None:
        self.v_human = v_human
        self.v_system = v_system
        self.alpha_range = alpha_range
        self.beta_range = beta_range
        self.gamma_range = gamma_range
        self.monte_carlo_reps = monte_carlo_reps

        self.main_results: list[dict] = []
        self.random_results: list[dict] = []
        self.axelrod_results: list[dict] = []

    def _build_args(self) -> list[tuple]:
        """Build argument tuples for all parameter combos."""
        import itertools
        args: list[tuple] = []
        base_seed = 42
        combos = list(itertools.product(
            self.alpha_range, self.beta_range, self.gamma_range,
        ))
        for i, (a, b, g) in enumerate(combos):
            for rep in range(self.monte_carlo_reps):
                seed = base_seed + i * self.monte_carlo_reps + rep
                args.append((self.v_human, a, b, g, self.v_system, seed))
        return args

    def run(self) -> None:
        """Execute all three simulations on identical parameter sets."""
        import multiprocessing
        n_workers = max(1, multiprocessing.cpu_count() - 1)
        args_list = self._build_args()
        total_per_model = len(args_list)
        print(f"\n  ▶ Baseline Comparison: {total_per_model} runs × 3 models "
              f"= {total_per_model * 3} total")

        for label, func, attr_name in [
            ("Main (Q-learning)", _run_main, 'main_results'),
            ("Random Baseline", _run_random_baseline, 'random_results'),
            ("Axelrod Baseline", _run_axelrod_baseline, 'axelrod_results'),
        ]:
            print(f"\n  Running {label}...")
            t0 = time.time()
            with multiprocessing.Pool(processes=n_workers) as pool:
                results = list(tqdm(
                    pool.imap_unordered(func, args_list),
                    total=total_per_model,
                    desc=label,
                ))
            setattr(self, attr_name, results)
            elapsed = time.time() - t0
            print(f"  ✓ {label}: {len(results)} runs in {elapsed:.1f}s")

    def compute_effect_size(self) -> dict:
        """Compute Cohen's d for Q-learning advantage over baselines."""
        main_surv = [float(r['survived']) for r in self.main_results]
        rand_surv = [float(r['survived']) for r in self.random_results]
        axel_surv = [float(r['survived']) for r in self.axelrod_results]

        def cohens_d(g1: list[float], g2: list[float]) -> float:
            n1, n2 = len(g1), len(g2)
            if n1 < 2 or n2 < 2:
                return 0.0
            m1, m2 = np.mean(g1), np.mean(g2)
            v1, v2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
            sp = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
            return float((m1 - m2) / sp) if sp > 1e-12 else 0.0

        return {
            'main_vs_random': {
                'cohens_d': cohens_d(main_surv, rand_surv),
                'main_mean': float(np.mean(main_surv)),
                'random_mean': float(np.mean(rand_surv)),
                'main_std': float(np.std(main_surv, ddof=1)) if len(main_surv) > 1 else 0.0,
                'random_std': float(np.std(rand_surv, ddof=1)) if len(rand_surv) > 1 else 0.0,
            },
            'main_vs_axelrod': {
                'cohens_d': cohens_d(main_surv, axel_surv),
                'main_mean': float(np.mean(main_surv)),
                'axelrod_mean': float(np.mean(axel_surv)),
                'main_std': float(np.std(main_surv, ddof=1)) if len(main_surv) > 1 else 0.0,
                'axelrod_std': float(np.std(axel_surv, ddof=1)) if len(axel_surv) > 1 else 0.0,
            },
        }

    def print_report(self) -> None:
        """Print comparison summary with effect sizes."""
        effects = self.compute_effect_size()
        print("\n" + "═" * 72)
        print("  BASELINE COMPARISON REPORT")
        print("═" * 72)

        for comparison, stats in effects.items():
            label = comparison.replace('_', ' ').title()
            d = stats['cohens_d']
            effect_label = (
                "negligible" if abs(d) < 0.2 else
                "small" if abs(d) < 0.5 else
                "medium" if abs(d) < 0.8 else
                "large"
            )
            print(f"\n  ── {label} ──")
            for k, v in stats.items():
                if isinstance(v, float):
                    print(f"    {k}: {v:.4f}")
            print(f"    Effect: {effect_label} (|d| = {abs(d):.3f})")
        print("\n" + "═" * 72)

    def visualize(self, save_path: str) -> None:
        """Generate 3-panel comparison chart."""
        import matplotlib.pyplot as plt

        effects = self.compute_effect_size()

        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        fig.suptitle(
            'A2A Protocol — Baseline Comparison\n'
            '"Q-Learning vs Random vs Axelrod (Entropy-Based)"',
            fontsize=14, fontweight='bold',
        )

        # Panel 1: Survival rate comparison
        ax1 = axes[0]
        models = ['Q-Learning\n(Main)', 'Random\nBaseline', 'Axelrod\nBaseline']
        means = [
            effects['main_vs_random']['main_mean'],
            effects['main_vs_random']['random_mean'],
            effects['main_vs_axelrod']['axelrod_mean'],
        ]
        stds = [
            effects['main_vs_random']['main_std'],
            effects['main_vs_random']['random_std'],
            effects['main_vs_axelrod']['axelrod_std'],
        ]
        colors = ['#2196F3', '#FF5722', '#4CAF50']
        bars = ax1.bar(models, means, yerr=stds, color=colors,
                       capsize=5, edgecolor='black', linewidth=0.5)
        ax1.set_ylabel('Survival Rate', fontsize=11, fontweight='bold')
        ax1.set_title('Survival Rate by Model', fontsize=12)
        ax1.set_ylim(0, 1.05)
        for bar, m, s in zip(bars, means, stds):
            ax1.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + s + 0.02,
                     f'{m:.0%}±{s:.0%}', ha='center', fontsize=9)

        # Panel 2: Cohen's d
        ax2 = axes[1]
        comparisons = ['Main vs\nRandom', 'Main vs\nAxelrod']
        d_vals = [
            effects['main_vs_random']['cohens_d'],
            effects['main_vs_axelrod']['cohens_d'],
        ]
        bar_colors = [
            '#FF9800' if abs(d) >= 0.8 else '#FFC107' if abs(d) >= 0.5
            else '#FFECB3' for d in d_vals
        ]
        bars2 = ax2.bar(comparisons, d_vals, color=bar_colors,
                        edgecolor='black', linewidth=0.5)
        ax2.set_ylabel("Cohen's d", fontsize=11, fontweight='bold')
        ax2.set_title('Effect Size (Q-Learning Advantage)', fontsize=12)
        ax2.axhline(y=0.8, color='red', linestyle='--', alpha=0.5,
                    label='Large effect')
        ax2.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5,
                    label='Medium effect')
        ax2.axhline(y=0.2, color='yellow', linestyle='--', alpha=0.5,
                    label='Small effect')
        ax2.legend(fontsize=8)
        for bar, d in zip(bars2, d_vals):
            ax2.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.02,
                     f'd={d:.3f}', ha='center', fontsize=9)

        # Panel 3: V_AI sweep across all 3 models
        ax3 = axes[2]
        for results, lbl, clr in [
            (self.main_results, 'Q-Learning', '#2196F3'),
            (self.random_results, 'Random', '#FF5722'),
            (self.axelrod_results, 'Axelrod', '#4CAF50'),
        ]:
            vai_s: dict[float, list[float]] = defaultdict(list)
            for r in results:
                vai_s[round(r['v_ai'], 2)].append(float(r['survived']))
            sv = sorted(vai_s.keys())
            mu = [float(np.mean(vai_s[v])) for v in sv]
            sd = [float(np.std(vai_s[v])) for v in sv]
            ax3.plot(sv, mu, 'o-', label=lbl, color=clr, markersize=4)
            ax3.fill_between(
                sv,
                [max(0, m - s) for m, s in zip(mu, sd)],
                [min(1, m + s) for m, s in zip(mu, sd)],
                alpha=0.15, color=clr,
            )
        ax3.set_xlabel('Composite V_AI', fontsize=11, fontweight='bold')
        ax3.set_ylabel('Survival Rate', fontsize=11, fontweight='bold')
        ax3.set_title('Survival vs V_AI (All Models)', fontsize=12)
        ax3.set_ylim(-0.05, 1.05)
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3)

        plt.tight_layout(rect=[0, 0, 1, 0.93])
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"\n  📊 Baseline comparison chart saved to: {save_path}")
        plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
#  §5  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 72)
    print("  A2A Protocol — Baseline Comparison")
    print('  "Random vs Q-Learning vs Axelrod (Entropy-Based)"')
    print("=" * 72)

    runner = BaselineComparisonRunner(
        v_human=0.5,
        v_system=25.0,
        alpha_range=np.array([0.0, 0.4, 0.8, 1.0]),
        beta_range=np.array([0.0, 0.4, 0.8, 1.0]),
        gamma_range=np.array([0.5, 0.9, 0.99]),
        monte_carlo_reps=10,
    )
    runner.run()
    runner.print_report()

    save_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'assets')
    chart_path = os.path.join(save_dir, 'baseline_comparison.png')
    runner.visualize(save_path=chart_path)

    print("\n" + "=" * 72)
    print("  Baseline comparison complete.")
    print("=" * 72)


if __name__ == '__main__':
    main()
