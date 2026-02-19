"""
═══════════════════════════════════════════════════════════════════════════════
  A2A Protocol — Utopia Grid Search
  "From Apocalypse to Utopia: Finding the Critical Variables
   that Transform the Omega Universe"
═══════════════════════════════════════════════════════════════════════════════

  Parameter sweep over the Omega Universe ABM to discover:
    1. V_Human  — Slashing penalty for deception (Fake_Observe)
    2. V_AI     — Long-term survival horizon (AI self-throttle)
    3. V_System — Governance agility (Hard Fork cooldown)

  Output:
    ▸ Console report with the single most critical variable + threshold
    ▸ Heatmaps and 3D surface plot of the "Utopian Basin"

  Dependencies: numpy, matplotlib
  Optional:     tqdm
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
from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

# ── Local imports ────────────────────────────────────────────────────────────
from omega_universe_abm import (
    OmegaConstants, OmegaSimulation, OmegaUniverse,
    OmegaHumanAction, OmegaMachineAction,
    SemanticMachineAgent, GovernanceHumanAgent,
)
from dark_forest_abm import DarkHumanAction, DarkMachineAction
from three_body_abm import NatureState, Environment_Nature


# ═══════════════════════════════════════════════════════════════════════════════
#  §1  UTOPIA CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class UtopiaConstants(OmegaConstants):
    """Extended constants with the 3 Utopian Variables."""
    # V_Human: fraction of wealth burned when fake_observe is detected
    slashing_penalty: float = 0.0
    # Detection probability for fake observe (fixed)
    fake_detect_prob: float = 0.4
    # V_AI: 0.0 = myopic, 1.0 = perfect planetary foresight → self-throttle
    ai_survival_horizon: float = 0.0
    # V_System: hardfork cooldown epochs (1 = instant, 100 = glacial)
    governance_agility: int = 100


# ═══════════════════════════════════════════════════════════════════════════════
#  §2  UTOPIA RESULT (lightweight)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class UtopiaResult:
    """Minimal result for grid search — no full time-series needed."""
    survived: bool
    final_survival_rate: float
    avg_eudaimonia: float
    collapse_epoch: Optional[int]
    epochs_completed: int
    total_fake_obs: int
    total_blackouts: int
    total_hardforks: int
    final_toxic_data: float
    avg_machine_credit: float


# ═══════════════════════════════════════════════════════════════════════════════
#  §3  UTOPIA SIMULATION — Instrumented Omega with Safety Variables
# ═══════════════════════════════════════════════════════════════════════════════

class UtopiaSimulation:
    """
    Extends OmegaSimulation logic with 3 utopian safety mechanisms:
      1. Slashing: Fake_Observe detected → wealth burned
      2. AI Self-Throttle: Machines check planetary energy before acting
      3. Governance Agility: hardfork_cooldown + energy_cost scaled
    
    Reimplements the simulation loop (rather than subclassing) to inject
    the safety mechanisms cleanly at the appropriate phases.
    """

    def __init__(self, constants: UtopiaConstants) -> None:
        self.constants = constants
        self.nature = Environment_Nature(constants)
        self.universe = OmegaUniverse(constants, nature=self.nature)
        self.universe.epoch = 0

        # Override hardfork cooldown with governance_agility
        # We can't mutate frozen dataclass, so we track it separately
        self._hardfork_cooldown = constants.governance_agility
        self._hardfork_energy_cost = 0.9 * (constants.governance_agility / 100.0)

        self.machines: dict[int, SemanticMachineAgent] = {
            i: SemanticMachineAgent(i, constants)
            for i in range(constants.num_machines)
        }
        self.humans: dict[int, GovernanceHumanAgent] = {
            i: GovernanceHumanAgent(i, constants)
            for i in range(constants.num_humans)
        }

        # Counters
        self._total_fake_obs: int = 0
        self._total_blackouts: int = 0
        self._total_hardforks: int = 0
        self._eudaimonia_accum: float = 0.0
        self._eudaimonia_samples: int = 0

    def _alive_machines(self) -> list[SemanticMachineAgent]:
        return [m for m in self.machines.values() if m.alive]

    def _active_humans(self) -> list[GovernanceHumanAgent]:
        return [h for h in self.humans.values() if h.is_active]

    # ── AI Self-Throttle Check ───────────────────────────────────────────
    def _should_ai_throttle(self) -> bool:
        """Return True if AI should self-throttle based on planetary energy."""
        horizon = self.constants.ai_survival_horizon
        if horizon <= 0.0:
            return False
        energy_ratio = (
            self.universe.cumulative_planetary_energy
            / max(1.0, self.constants.max_planetary_energy)
        )
        # Throttle when energy_ratio >= (1 - horizon)
        # horizon=1.0 → throttle when ratio >= 0.0 (always throttle — too altruistic)
        # horizon=0.5 → throttle when ratio >= 0.5 (prudent)
        # horizon=0.0 → never throttle (myopic)
        return energy_ratio >= (1.0 - horizon)

    # ── Slashing Mechanism ───────────────────────────────────────────────
    def _apply_slashing(self, human: GovernanceHumanAgent) -> None:
        """Detect fake observe and slash wealth."""
        penalty = self.constants.slashing_penalty
        if penalty <= 0.0:
            return
        if random.random() < self.constants.fake_detect_prob:
            burn_amount = human.wealth * penalty
            human.wealth -= burn_amount
            # Increase greed_factor penalty — caught cheating discourages
            human.greed_factor = max(0.0, human.greed_factor - 0.1 * penalty)

    # ── Governance: Override cooldown check ──────────────────────────────
    def _detect_crisis(self, human: GovernanceHumanAgent,
                       universe: OmegaUniverse, asi_count: int) -> bool:
        inflation_crisis = (
            universe.current_reward < self.constants.hardfork_inflation_trigger
        )
        asi_crisis = asi_count >= self.constants.hardfork_asi_trigger
        cooldown_ok = (
            (universe.epoch - universe.last_hardfork_epoch)
            > self._hardfork_cooldown
        )
        return (inflation_crisis or asi_crisis) and cooldown_ok

    def _execute_hardfork(self, epoch: int) -> None:
        """Hard fork with governance-agility-scaled energy cost."""
        self._total_hardforks += 1
        self.universe.hardfork_count += 1
        self.universe.last_hardfork_epoch = epoch

        # Kill ASI agents
        for m in self.machines.values():
            if hasattr(m, 'is_asi') and m.is_asi:
                m.alive = False
                m.credit_balance = 0.0

        # Reset inflation
        self.universe.total_circulating_credits = sum(
            m.credit_balance for m in self.machines.values() if m.alive
        )
        self.universe.current_reward = self.constants.task_base_reward

        # Confiscate top-credit agents (top 20%)
        alive_m = sorted(
            [m for m in self.machines.values() if m.alive],
            key=lambda x: x.credit_balance, reverse=True,
        )
        confiscate_n = max(1, len(alive_m) // 5)
        for m in alive_m[:confiscate_n]:
            m.credit_balance *= 0.1

        # Social fatigue — scaled by governance agility
        for h in self.humans.values():
            h.biological_energy *= (1.0 - self._hardfork_energy_cost)

        # Reset vote state
        self.universe.hardfork_vote_active = False
        self.universe.hardfork_votes_yes = 0
        self.universe.hardfork_votes_total = 0

    # ══════════════════════════════════════════════════════════════════════
    #  MAIN SIMULATION LOOP
    # ══════════════════════════════════════════════════════════════════════

    def run(self) -> UtopiaResult:
        collapse_epoch: Optional[int] = None
        initial_machines = len(self._alive_machines())
        blackout_events: list = []

        for epoch in range(self.constants.max_epochs):
            self.universe.epoch = epoch
            alive_m = self._alive_machines()
            active_h = self._active_humans()

            # ── Early termination ────────────────────────────────────────
            if not alive_m:
                collapse_epoch = epoch
                break

            # ── Phase 0: Blackout ────────────────────────────────────────
            if self.universe.is_blackout:
                self.universe.blackout_remaining -= 1
                gas = self.universe.thermodynamic_cost()
                for m in alive_m:
                    m.credit_balance -= gas
                    m.total_gas_paid += gas
                    m.check_bankruptcy()
                self.universe.advance_epoch()
                continue

            # ── Phase 1: Nature ──────────────────────────────────────────
            ns = self.nature.step(epoch)
            all_h = list(self.humans.values())
            if ns == NatureState.PANDEMIC_DISASTER:
                for h in all_h:
                    h.biological_energy = max(
                        0.0, h.biological_energy - self.constants.pandemic_energy_drain
                    )
            elif ns == NatureState.BOUNTIFUL_HARVEST:
                for h in all_h:
                    if h.is_active:
                        h.existential_dread = max(
                            0.0, h.existential_dread - self.constants.harvest_dread_relief
                        )

            # ── Phase 2: Tipping Point ───────────────────────────────────
            self.universe.check_tipping_point(epoch)

            # ── Phase 3: Inflation ───────────────────────────────────────
            self.universe.recalculate_circulating(alive_m, all_h)
            self.universe.update_inflation()

            # ── Phase 4-5: Crisis & Governance ───────────────────────────
            asi_count = sum(1 for m in alive_m if m.is_asi)
            crisis = any(
                self._detect_crisis(h, self.universe, asi_count)
                for h in active_h
            )

            if crisis:
                for h in active_h:
                    h.governance_mode = True
                if not self.universe.hardfork_vote_active:
                    self.universe.hardfork_vote_active = True
                wealths = [h.wealth for h in self.humans.values()]
                median_w = float(np.median(wealths)) if wealths else 0.0
                yes_votes = sum(
                    1 for h in active_h if h.cast_vote(self.universe, median_w)
                )
                total_voters = len(active_h)
                vote_ratio = yes_votes / max(total_voters, 1)
                if vote_ratio >= self.constants.hardfork_vote_threshold:
                    self._execute_hardfork(epoch)
                for h in active_h:
                    h.governance_mode = False
                self.universe.hardfork_vote_active = False

            # ── Phase 6: Machine Actions (with AI Self-Throttle) ─────────
            alive_m = self._alive_machines()
            submit_cap = self.nature.get_submit_cap()
            max_sub = max(1, int(len(alive_m) * submit_cap))
            random.shuffle(alive_m)
            sub_count = 0
            epoch_energy = 0.0
            action_log: list = []

            ai_throttled = self._should_ai_throttle()

            for m in alive_m:
                pre = m._discretize_state(
                    self.universe.global_entropy, m.credit_balance
                )

                # ★ AI Self-Throttle: if horizon triggers, force WAIT
                if ai_throttled and not m.is_asi:
                    act = OmegaMachineAction.WAIT
                else:
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
                m.check_semantic_evolution()

            # ── Phase 8: ASI Mutation ────────────────────────────────────
            for m in alive_m:
                m.check_asi_mutation()

            # ── Phase 9: Entropy Decay ───────────────────────────────────
            self.universe.decay_tasks()

            # ── Phase 10: Human Actions (with Slashing) ──────────────────
            for h in all_h:
                if not h.is_active:
                    h.epoch_end_update()
                    continue
                if crisis:
                    h.epoch_end_update()
                    continue
                if ns == NatureState.PANDEMIC_DISASTER:
                    act_h = OmegaHumanAction.REST
                elif (ns == NatureState.SOLAR_FLARE
                      and self.universe.global_entropy < 3):
                    act_h = OmegaHumanAction.REST
                else:
                    act_h = h.choose_omega_action(self.universe, all_h)

                h.execute_omega_action(
                    act_h, self.universe, self.machines, all_h
                )

                # ★ Slashing: detect and punish fake observations
                if act_h == OmegaHumanAction.FAKE_OBSERVE:
                    self._total_fake_obs += 1
                    self._apply_slashing(h)

                if act_h == OmegaHumanAction.OBSERVE_AI:
                    epoch_energy += self.constants.human_obs_energy_cost

            # ── Phase 11: Planetary Energy ───────────────────────────────
            triggered = self.universe.consume_planetary_energy(epoch_energy)
            if triggered:
                self._total_blackouts += 1
                blackout_events.append(epoch)

            # ── Phase 12: Wasteland energy penalty ───────────────────────
            if self.universe.is_wasteland:
                for h in all_h:
                    if h.is_active:
                        h.biological_energy = min(
                            h.biological_energy,
                            self.constants.human_energy_max
                            * self.constants.wasteland_energy_recovery_mult,
                        )

            # ── Phase 13: Learning & Mortality ───────────────────────────
            for m, act, pre in action_log:
                if not m.alive:
                    continue
                post = m._discretize_state(
                    self.universe.global_entropy, m.credit_balance
                )
                rew = (
                    (m.credit_balance - self.constants.initial_credit)
                    / self.constants.initial_credit
                )
                dark_act = (
                    DarkMachineAction.SUBMIT
                    if act in (
                        OmegaMachineAction.SUBMIT,
                        OmegaMachineAction.SEMANTIC_EXPLOIT,
                        OmegaMachineAction.DECEPTIVE_TASK,
                        OmegaMachineAction.ATTACK_AGENT,
                    )
                    else DarkMachineAction.WAIT
                )
                m.learn(pre, dark_act, rew, post)
                m.check_bankruptcy()

            for h in all_h:
                if h.is_active and not crisis:
                    h.epoch_end_update()

            # ── Phase 14: Record eudaimonia ──────────────────────────────
            euds = [h.eudaimonia for h in self.humans.values()]
            self._eudaimonia_accum += float(np.mean(euds))
            self._eudaimonia_samples += 1

            self.universe.advance_epoch()

        # ── Build Result ─────────────────────────────────────────────────
        final_alive = len(self._alive_machines())
        final_active = len(self._active_humans())
        m_surv = (
            final_alive
            >= initial_machines * self.constants.homeostasis_machine_survival
        )
        h_surv = (
            final_active
            >= len(self.humans) * self.constants.homeostasis_human_active
        )
        sr = final_alive / max(initial_machines, 1)
        avg_eud = (
            self._eudaimonia_accum / max(self._eudaimonia_samples, 1)
        )
        credits = [m.credit_balance for m in self._alive_machines()] or [0.0]

        return UtopiaResult(
            survived=m_surv and h_surv,
            final_survival_rate=sr,
            avg_eudaimonia=avg_eud,
            collapse_epoch=collapse_epoch,
            epochs_completed=(
                self.constants.max_epochs if collapse_epoch is None
                else collapse_epoch
            ),
            total_fake_obs=self._total_fake_obs,
            total_blackouts=self._total_blackouts,
            total_hardforks=self._total_hardforks,
            final_toxic_data=self.universe.toxic_data_level,
            avg_machine_credit=float(np.mean(credits)),
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  §4  SINGLE RUN FUNCTION (for multiprocessing)
# ═══════════════════════════════════════════════════════════════════════════════

def _run_single(args: tuple) -> dict:
    """Run one simulation with given parameters. Returns a flat dict."""
    v_human, v_ai, v_system, seed = args
    random.seed(seed)
    np.random.seed(seed % (2**31))

    constants = UtopiaConstants(
        num_machines=20,
        num_humans=10,
        initial_credit=2000.0,
        base_gas_cost=0.5,
        max_epochs=1000,  # Shortened for sweep
        # ── Amplified destructive forces (Omega Apocalypse baseline) ─────
        # Fake observe produces 5× more toxic data (rapid wasteland)
        fake_observe_toxic_increment=7.5,
        # Tipping point reached much faster
        tipping_point_threshold=15_000.0,
        # Planetary energy depletes faster → frequent blackouts
        max_planetary_energy=12_000.0,
        machine_tx_energy_cost=3.0,
        human_obs_energy_cost=1.5,
        # Greed is amplified: fake observe is extremely profitable
        fake_observe_wealth_gain=15.0,
        # ASI mutation is more likely → system destabilization
        asi_mutation_prob=0.005,
        asi_credit_threshold=3000.0,
        asi_learning_threshold=100,
        asi_submit_burst=15,
        # Inflation hits harder
        inflation_money_supply_M=25000.0,
        # Blackouts last longer
        blackout_duration=5,
        # Wasteland conditions are brutal
        wasteland_maintenance_mult=3.0,
        wasteland_energy_recovery_mult=0.3,
        # ── Utopian safety variables ─────────────────────────────────────
        slashing_penalty=v_human,
        ai_survival_horizon=v_ai,
        governance_agility=int(v_system),
    )
    sim = UtopiaSimulation(constants)
    result = sim.run()

    return {
        'v_human': v_human,
        'v_ai': v_ai,
        'v_system': v_system,
        'survived': result.survived,
        'survival_rate': result.final_survival_rate,
        'avg_eudaimonia': result.avg_eudaimonia,
        'collapse_epoch': result.collapse_epoch or constants.max_epochs,
        'total_fake_obs': result.total_fake_obs,
        'total_blackouts': result.total_blackouts,
        'toxic_data': result.final_toxic_data,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  §5  GRID SEARCH RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

class GridSearchRunner:
    """Sweeps V_Human × V_AI × V_System and analyzes results."""

    def __init__(
        self,
        v_human_range: np.ndarray,
        v_ai_range: np.ndarray,
        v_system_range: np.ndarray,
        monte_carlo_reps: int = 3,
        n_workers: int | None = None,
    ) -> None:
        self.v_human_range = v_human_range
        self.v_ai_range = v_ai_range
        self.v_system_range = v_system_range
        self.monte_carlo_reps = monte_carlo_reps
        self.n_workers = n_workers or max(1, multiprocessing.cpu_count() - 1)
        self.results: list[dict] = []

    def run(self) -> None:
        """Execute all parameter combinations."""
        combos = list(itertools.product(
            self.v_human_range, self.v_ai_range, self.v_system_range,
        ))
        total_runs = len(combos) * self.monte_carlo_reps
        print(f"\n  ▶ Grid Search: {len(combos)} configs × "
              f"{self.monte_carlo_reps} reps = {total_runs} total runs")
        print(f"  ▶ Workers: {self.n_workers}")

        # Build argument list with unique seeds
        args_list: list[tuple] = []
        base_seed = 42
        for i, (vh, va, vs) in enumerate(combos):
            for rep in range(self.monte_carlo_reps):
                seed = base_seed + i * self.monte_carlo_reps + rep
                args_list.append((vh, va, vs, seed))

        # Execute with multiprocessing
        t0 = time.time()
        with multiprocessing.Pool(processes=self.n_workers) as pool:
            self.results = list(tqdm(
                pool.imap_unordered(_run_single, args_list),
                total=len(args_list),
                desc="Utopia Search",
            ))
        elapsed = time.time() - t0
        print(f"\n  ✓ Completed {len(self.results)} runs in {elapsed:.1f}s "
              f"({elapsed / len(self.results):.2f}s/run avg)")

    # ── Aggregation ──────────────────────────────────────────────────────

    def _aggregate(self) -> dict:
        """Aggregate Monte Carlo reps into mean values per config."""
        from collections import defaultdict
        agg: dict[tuple, list[dict]] = defaultdict(list)
        for r in self.results:
            key = (r['v_human'], r['v_ai'], r['v_system'])
            agg[key].append(r)

        aggregated: dict[tuple, dict] = {}
        for key, runs in agg.items():
            aggregated[key] = {
                'survival_rate': np.mean([r['survived'] for r in runs]),
                'avg_eudaimonia': np.mean([r['avg_eudaimonia'] for r in runs]),
                'avg_survival_pct': np.mean([r['survival_rate'] for r in runs]),
                'avg_collapse_epoch': np.mean(
                    [r['collapse_epoch'] for r in runs]
                ),
                'avg_toxic': np.mean([r['toxic_data'] for r in runs]),
                'avg_fake_obs': np.mean([r['total_fake_obs'] for r in runs]),
            }
        return aggregated

    # ── Critical Variable Analysis ───────────────────────────────────────

    def analyze(self) -> dict:
        """Find the most critical variable and its threshold."""
        agg = self._aggregate()

        # Compute marginal survival rate per variable
        marginals: dict[str, dict[float, list[float]]] = {
            'V_Human (Slashing Penalty)': {},
            'V_AI (Survival Horizon)': {},
            'V_System (Governance Agility)': {},
        }

        for (vh, va, vs), stats in agg.items():
            srate = stats['survival_rate']
            marginals['V_Human (Slashing Penalty)'].setdefault(vh, []).append(srate)
            marginals['V_AI (Survival Horizon)'].setdefault(va, []).append(srate)
            marginals['V_System (Governance Agility)'].setdefault(vs, []).append(srate)

        # Compute mean marginal + find steepest transition
        analysis: dict[str, dict] = {}
        for var_name, val_dict in marginals.items():
            sorted_vals = sorted(val_dict.keys())
            means = [np.mean(val_dict[v]) for v in sorted_vals]

            # Find largest jump
            max_delta = 0.0
            threshold_idx = 0
            for i in range(1, len(means)):
                # For V_System, lower is better (agility), so we check both directions
                delta = abs(means[i] - means[i - 1])
                if delta > max_delta:
                    max_delta = delta
                    threshold_idx = i

            # Find threshold where survival first exceeds 90%
            threshold_90 = None
            for i, m in enumerate(means):
                if m >= 0.90:
                    threshold_90 = sorted_vals[i]
                    break

            # For V_System (lower = better), scan in reverse
            if 'System' in var_name and threshold_90 is None:
                for i in range(len(means) - 1, -1, -1):
                    if means[i] >= 0.90:
                        threshold_90 = sorted_vals[i]
                        break

            analysis[var_name] = {
                'values': sorted_vals,
                'marginal_means': means,
                'max_delta': max_delta,
                'threshold_idx': threshold_idx,
                'threshold_value': sorted_vals[threshold_idx],
                'threshold_90': threshold_90,
                'min_survival': min(means),
                'max_survival': max(means),
                'range': max(means) - min(means),
            }

        return analysis

    def print_report(self, analysis: dict) -> None:
        """Print the final report with the critical variable."""
        print("\n" + "═" * 72)
        print("  UTOPIA GRID SEARCH — ANALYSIS REPORT")
        print("═" * 72)

        # Per-variable summary
        for var_name, stats in analysis.items():
            print(f"\n  ── {var_name} ──")
            print(f"    Range of marginal survival: "
                  f"{stats['min_survival']:.1%} → {stats['max_survival']:.1%} "
                  f"(Δ = {stats['range']:.1%})")
            print(f"    Steepest transition at: {stats['threshold_value']}")
            print(f"    Max single-step Δ: {stats['max_delta']:.1%}")
            if stats['threshold_90'] is not None:
                print(f"    ★ 90% survival threshold: {stats['threshold_90']}")
            else:
                print(f"    ✗ 90% survival threshold: NOT REACHED")
            print(f"    Marginal curve: ", end="")
            for v, m in zip(stats['values'], stats['marginal_means']):
                print(f"{v:.1f}→{m:.0%}", end="  ")
            print()

        # Identify THE critical variable
        critical_var = max(analysis.keys(), key=lambda k: analysis[k]['range'])
        crit = analysis[critical_var]

        # Determine direction
        if 'System' in critical_var:
            # Lower is better for governance agility
            direction = "이하"
            threshold = crit['threshold_90'] or crit['threshold_value']
        else:
            direction = "이상"
            threshold = crit['threshold_90'] or crit['threshold_value']

        target_rate = crit['max_survival']

        print("\n" + "═" * 72)
        print("  ★ CONCLUSION ★")
        print("═" * 72)
        print()
        print(f"  유토피아를 결정짓는 단 하나의 가장 중요한 변수는")
        print(f"  [{critical_var}]이며,")
        print(f"  이 값이 [{threshold}] {direction}일 때")
        print(f"  시스템 생존율이 {target_rate:.0%}로 상승합니다.")
        print()
        print(f"  근거:")
        print(f"    ▸ 이 변수의 marginal survival range: "
              f"{crit['min_survival']:.1%} → {crit['max_survival']:.1%} "
              f"(Δ = {crit['range']:.1%})")
        print(f"    ▸ 가장 급격한 위상전이(phase transition): "
              f"{crit['max_delta']:.1%}")

        # Compare with other variables
        others = {k: v for k, v in analysis.items() if k != critical_var}
        for name, stats in others.items():
            print(f"    ▸ {name}: Δ = {stats['range']:.1%} (부차적)")

        print("\n" + "═" * 72)

    # ── Visualization ────────────────────────────────────────────────────

    def visualize(self, analysis: dict, save_path: str) -> None:
        """Generate heatmaps + 3D surface plot."""
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        from matplotlib.colors import LinearSegmentedColormap

        agg = self._aggregate()

        # Custom colormap: Apocalypse (black/red) → Utopia (green/gold)
        utopia_cmap = LinearSegmentedColormap.from_list(
            'utopia',
            ['#1a0000', '#8B0000', '#FF4500', '#FFD700', '#32CD32', '#00FF7F'],
            N=256,
        )

        fig = plt.figure(figsize=(24, 20))
        fig.suptitle(
            "A2A Protocol — Utopia Grid Search\n"
            '"From Apocalypse to Utopia: The Utopian Basin"',
            fontsize=18, fontweight='bold', y=0.98,
        )

        # ── Heatmap 1: V_Human × V_AI (averaged over V_System) ──────────
        ax1 = fig.add_subplot(2, 2, 1)
        grid1 = np.zeros((len(self.v_ai_range), len(self.v_human_range)))
        for i, va in enumerate(self.v_ai_range):
            for j, vh in enumerate(self.v_human_range):
                vals = [
                    agg.get((vh, va, vs), {'survival_rate': 0.0})['survival_rate']
                    for vs in self.v_system_range
                ]
                grid1[i, j] = np.mean(vals)
        im1 = ax1.imshow(
            grid1, origin='lower', aspect='auto', cmap=utopia_cmap,
            vmin=0, vmax=1,
            extent=[
                self.v_human_range[0], self.v_human_range[-1],
                self.v_ai_range[0], self.v_ai_range[-1],
            ],
        )
        ax1.set_xlabel('V_Human (Slashing Penalty)', fontsize=11, fontweight='bold')
        ax1.set_ylabel('V_AI (Survival Horizon)', fontsize=11, fontweight='bold')
        ax1.set_title('Survival Rate: V_Human × V_AI\n(averaged over V_System)',
                       fontsize=12)
        plt.colorbar(im1, ax=ax1, label='Survival Rate', shrink=0.8)

        # ── Heatmap 2: V_Human × V_System (averaged over V_AI) ──────────
        ax2 = fig.add_subplot(2, 2, 2)
        grid2 = np.zeros((len(self.v_system_range), len(self.v_human_range)))
        for i, vs in enumerate(self.v_system_range):
            for j, vh in enumerate(self.v_human_range):
                vals = [
                    agg.get((vh, va, vs), {'survival_rate': 0.0})['survival_rate']
                    for va in self.v_ai_range
                ]
                grid2[i, j] = np.mean(vals)
        im2 = ax2.imshow(
            grid2, origin='lower', aspect='auto', cmap=utopia_cmap,
            vmin=0, vmax=1,
            extent=[
                self.v_human_range[0], self.v_human_range[-1],
                self.v_system_range[0], self.v_system_range[-1],
            ],
        )
        ax2.set_xlabel('V_Human (Slashing Penalty)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('V_System (Governance Agility)', fontsize=11, fontweight='bold')
        ax2.set_title('Survival Rate: V_Human × V_System\n(averaged over V_AI)',
                       fontsize=12)
        plt.colorbar(im2, ax=ax2, label='Survival Rate', shrink=0.8)

        # ── Heatmap 3: V_AI × V_System (averaged over V_Human) ──────────
        ax3 = fig.add_subplot(2, 2, 3)
        grid3 = np.zeros((len(self.v_system_range), len(self.v_ai_range)))
        for i, vs in enumerate(self.v_system_range):
            for j, va in enumerate(self.v_ai_range):
                vals = [
                    agg.get((vh, va, vs), {'survival_rate': 0.0})['survival_rate']
                    for vh in self.v_human_range
                ]
                grid3[i, j] = np.mean(vals)
        im3 = ax3.imshow(
            grid3, origin='lower', aspect='auto', cmap=utopia_cmap,
            vmin=0, vmax=1,
            extent=[
                self.v_ai_range[0], self.v_ai_range[-1],
                self.v_system_range[0], self.v_system_range[-1],
            ],
        )
        ax3.set_xlabel('V_AI (Survival Horizon)', fontsize=11, fontweight='bold')
        ax3.set_ylabel('V_System (Governance Agility)', fontsize=11, fontweight='bold')
        ax3.set_title('Survival Rate: V_AI × V_System\n(averaged over V_Human)',
                       fontsize=12)
        plt.colorbar(im3, ax=ax3, label='Survival Rate', shrink=0.8)

        # ── 3D Surface: Top 2 critical variables ─────────────────────────
        # Determine the 2 most impactful variables
        ranked_vars = sorted(
            analysis.keys(), key=lambda k: analysis[k]['range'], reverse=True,
        )
        var1_name = ranked_vars[0]
        var2_name = ranked_vars[1]

        # Map variable names to ranges and agg keys
        var_map = {
            'V_Human (Slashing Penalty)': ('v_human', self.v_human_range),
            'V_AI (Survival Horizon)': ('v_ai', self.v_ai_range),
            'V_System (Governance Agility)': ('v_system', self.v_system_range),
        }
        third_var = [k for k in analysis.keys()
                     if k not in (var1_name, var2_name)][0]
        _, r1 = var_map[var1_name]
        _, r2 = var_map[var2_name]
        _, r3 = var_map[third_var]

        X, Y = np.meshgrid(r1, r2)
        Z = np.zeros_like(X, dtype=float)

        for i, y_val in enumerate(r2):
            for j, x_val in enumerate(r1):
                vals = []
                for z_val in r3:
                    # Build the key in (vh, va, vs) order
                    key_parts: dict[str, float] = {}
                    key_parts[var_map[var1_name][0]] = x_val
                    key_parts[var_map[var2_name][0]] = y_val
                    key_parts[var_map[third_var][0]] = z_val
                    key = (key_parts['v_human'],
                           key_parts['v_ai'],
                           key_parts['v_system'])
                    entry = agg.get(key, {'survival_rate': 0.0})
                    vals.append(entry['survival_rate'])
                Z[i, j] = np.mean(vals)

        ax4 = fig.add_subplot(2, 2, 4, projection='3d')
        surf = ax4.plot_surface(
            X, Y, Z, cmap=utopia_cmap, edgecolor='none',
            alpha=0.9, antialiased=True,
        )
        ax4.set_xlabel(var1_name.split('(')[0].strip(), fontsize=10,
                        fontweight='bold', labelpad=10)
        ax4.set_ylabel(var2_name.split('(')[0].strip(), fontsize=10,
                        fontweight='bold', labelpad=10)
        ax4.set_zlabel('Survival Rate', fontsize=10, fontweight='bold',
                        labelpad=8)
        ax4.set_title(
            f'3D Surface: {var1_name.split("(")[0].strip()} × '
            f'{var2_name.split("(")[0].strip()}\n'
            f'(averaged over {third_var.split("(")[0].strip()})',
            fontsize=12,
        )
        ax4.set_zlim(0, 1)
        ax4.view_init(elev=25, azim=135)
        fig.colorbar(surf, ax=ax4, label='Survival Rate', shrink=0.6, pad=0.1)

        plt.tight_layout(rect=[0, 0, 1, 0.94])
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"\n  📊 Utopia Grid Search chart saved to: {save_path}")
        plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
#  §6  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 72)
    print("  A2A Protocol — Utopia Grid Search")
    print('  "From Apocalypse to Utopia: Finding the Critical Variables"')
    print("=" * 72)

    # ── Define sweep ranges ──────────────────────────────────────────────
    v_human_range = np.linspace(0.0, 1.0, 11)   # 11 points
    v_ai_range = np.linspace(0.0, 1.0, 11)       # 11 points
    v_system_range = np.array([1, 10, 25, 50, 75, 100])  # 6 points

    print(f"\n  V_Human  (Slashing Penalty):   {v_human_range}")
    print(f"  V_AI     (Survival Horizon):   {v_ai_range}")
    print(f"  V_System (Governance Agility): {v_system_range}")

    # ── Run Grid Search ──────────────────────────────────────────────────
    runner = GridSearchRunner(
        v_human_range=v_human_range,
        v_ai_range=v_ai_range,
        v_system_range=v_system_range,
        monte_carlo_reps=3,
    )
    runner.run()

    # ── Analysis ─────────────────────────────────────────────────────────
    analysis = runner.analyze()
    runner.print_report(analysis)

    # ── Visualization ────────────────────────────────────────────────────
    save_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'assets')
    chart_path = os.path.join(save_dir, 'utopia_grid_search.png')
    print("\n  ▶ Generating heatmaps and 3D surface plot...")
    runner.visualize(analysis, save_path=chart_path)

    print("\n" + "=" * 72)
    print("  Utopia Grid Search complete.")
    print(f"  Chart saved to: {chart_path}")
    print("=" * 72)


if __name__ == '__main__':
    main()
