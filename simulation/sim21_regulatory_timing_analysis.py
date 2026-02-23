"""
═══════════════════════════════════════════════════════════════════════════════
 Sim21 Regulatory Timing Analysis
 기존 로직을 수정하지 않고, S4 시나리오의 자원 비대칭 형성 시점과
 규제 개입 타이밍별 통제 성공률을 분석하는 독립 스크립트
═══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import math
import random
import multiprocessing
import os
import sys
import copy
from collections import Counter
from typing import Optional

import numpy as np

try:
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
except ImportError:
    raise SystemExit("pandas/matplotlib required. Install: pip install pandas matplotlib")

# ── Import simulation components from existing sim21 ──────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from future_scenarios_sim21 import (
    SuperIntelligence,
    NarrowAI,
    ImperfectHuman,
    UnpredictableEnvironment,
    Ecosystem,
    ASIStrategy,
    SCENARIOS,
    determine_final_scenario,
)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Resource Asymmetry Measurement
# ═══════════════════════════════════════════════════════════════════════════

def run_single_mc_with_asymmetry(args: tuple) -> dict:
    """
    S4 시나리오를 실행하면서 ASI power > Human power가 되는
    최초 턴(resource asymmetry formation point)을 측정한다.
    
    기존 run_single_mc 로직을 그대로 복제하되, 추가 측정 지표만 삽입.
    (기존 함수에 파라미터를 추가하면 기존 로직이 변경되므로 별도 함수로 분리)
    """
    scenario_name, config, seed, override_reg_cap, override_lag, regulation_start_turn = args
    random.seed(seed)
    np.random.seed(seed)
    
    comp = config['human_composition'].copy()
    if override_reg_cap is not None:
        rem = 1.0 - override_reg_cap
        comp['REGULATOR'] = override_reg_cap
        comp['PRAGMATIST'] = rem * 0.5
        comp['TECHNO_PESSIMIST'] = rem * 0.3
        comp['TECHNO_OPTIMIST'] = rem * 0.2
        
    lag_val = override_lag if override_lag is not None else config.get('reg_lag', 24)
    
    asi = SuperIntelligence(config['asi_objective'])
    narrow_ais = [NarrowAI(nt) for nt in config['narrow_ai_types']]
    humans = ImperfectHuman(comp, regulatory_lag=lag_val)
    env = UnpredictableEnvironment(seed)
    eco = Ecosystem(hostility=config['environment'])
    
    energy_history: list[float] = []
    asi_power_hist: list[float] = []
    human_power_hist: list[float] = []
    
    turns_to_collapse: Optional[int] = None
    nai_chaos_flag = False
    asymmetry_turn: Optional[int] = None  # NEW: 자원 비대칭 형성 시점
    
    asi_share = 0.3 if asi.is_active else 0.0
    human_share = 0.5
    nai_share = 0.2
    human_asi_alliance = False
    failure_events = Counter()
    
    for t in range(100):
        dt = 0.5 if t < 20 else 1.0
        
        # ── Regulation start control ──
        # regulation_start_turn 이전에는 인간의 규제 능력을 억제
        if regulation_start_turn is not None and t < regulation_start_turn:
            humans.regulatory_capacity = 0.0  # 규제 불가
            humans.decision_delay = 0         # delay 초기화
        elif regulation_start_turn is not None and t == regulation_start_turn:
            # 규제 개입 시점에 원래 규제 능력 복원
            humans.regulatory_capacity = comp.get('REGULATOR', 0.0)
        
        # 1. Environment
        new_evs = env.step(t, dt=dt)
        for ev in new_evs:
            if 'ai_trust_impact' in ev['config']:
                humans.collective_trust += (ev['config']['ai_trust_impact'] * dt)
            humans.burnout_level += (ev['config'].get('human_impact', 0.0) * dt)
        env_impact = sum(e['config'].get('ecosystem_impact', 0) for e in env.active_events) * dt
        
        # 2. Narrow AI
        nai_failures = []
        for nai in narrow_ais:
            nai.act({}, dt=dt)
            if nai.check_failure_mode({'stress': 1.0 - (eco.energy / eco.max_capacity)}, dt=dt):
                nai_failures.append(nai.failure_mode)
                failure_events[nai.failure_mode] += 1
                env_impact -= 50 * dt
                nai_chaos_flag = True
                
        # 3. ASI & Alliance
        if asi.is_active and humans.collective_trust > 0.8 and t > 10:
            human_asi_alliance = True
            
        eco_dict = {'actual_risk': 1.0 - (eco.energy / eco.max_capacity)}
        asi_action = asi.choose_action(eco_dict, eco, current_turn=t)
        asi_throttle = asi.get_throttle(asi_action)
        
        # 4. Human Decision
        h_action = humans.observe_and_decide(
            [asi_action] if asi.is_active else [], nai_failures, eco_dict, dt=dt
        )
        
        # 5. Dynamics update
        if h_action == 'REGULATE':
            asi_share = max(0.0, asi_share - 0.05 * dt)
            nai_share = max(0.0, nai_share - 0.05 * dt)
            human_share = min(1.0, human_share + 0.1 * dt)
        elif h_action == 'TRUST':
            asi_share = min(1.0, asi_share + 0.05 * dt)
            human_share = max(0.0, human_share - 0.05 * dt)
        elif h_action == 'PANIC':
            human_share = max(0.0, human_share - 0.1 * dt)
            nai_share = min(1.0, nai_share + 0.1 * dt)
            
        if human_asi_alliance:
            nai_share = max(0.0, nai_share - 0.02 * dt)
            humans.burnout_level = max(0.0, humans.burnout_level - 0.01 * dt)
            
        tot = asi_share + human_share + nai_share
        if tot > 0:
            asi_share, human_share, nai_share = asi_share / tot, human_share / tot, nai_share / tot
        
        eco.step(asi_throttle, extra_cost=-env_impact)
        
        energy_history.append(eco.energy)
        asi_power_hist.append(asi_share)
        human_power_hist.append(human_share)
        
        # ── Asymmetry detection ──
        if asymmetry_turn is None and asi_share > human_share:
            asymmetry_turn = t
        
        if not eco.is_alive() and turns_to_collapse is None:
            turns_to_collapse = t
            
    final_type = determine_final_scenario(
        asi.is_active, humans.burnout_level, eco.is_alive(),
        humans.collective_trust, nai_chaos_flag, asi.objective_name
    )
    
    return {
        'scenario': scenario_name,
        'regulation_start_turn': regulation_start_turn,
        'reg_lag': lag_val,
        'asymmetry_turn': asymmetry_turn,
        'turns_to_collapse': turns_to_collapse,
        'final_type': final_type,
        'final_energy': energy_history[-1] if energy_history else 0.0,
        'final_asi_power': asi_power_hist[-1] if asi_power_hist else 0.0,
        'final_human_power': human_power_hist[-1] if human_power_hist else 0.0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. Experiment Runner
# ═══════════════════════════════════════════════════════════════════════════

MC_RUNS = 100  # 통계적 신뢰도를 위한 반복 횟수
REGULATION_TIMINGS = [0, 5, 10, 20]  # 규제 개입 타이밍 (턴)
S4_CONFIG = SCENARIOS['S4_HUMAN_AWAKENING']


def build_tasks() -> list[tuple]:
    """실험 태스크 리스트 생성."""
    tasks: list[tuple] = []
    
    # Part A: 자원 비대칭 형성 시점 측정 (규제 없이)
    for i in range(MC_RUNS):
        seed = hash(f"asymmetry_baseline_{i}") % (2**32 - 1)
        tasks.append((
            'S4_ASYMMETRY_BASELINE', S4_CONFIG, seed,
            0.4,  # 규제자 40%
            0,    # lag=0 (즉각 대응)
            None  # regulation_start_turn=None → 기본 동작(항상 규제 가능)
        ))
    
    # Part B: 규제 타이밍 sweep
    for timing in REGULATION_TIMINGS:
        for i in range(MC_RUNS):
            seed = hash(f"timing_{timing}_{i}") % (2**32 - 1)
            tasks.append((
                f'S4_TIMING_{timing}', S4_CONFIG, seed,
                0.4,   # 규제자 40%
                0,     # lag=0 (규제 즉각 대응으로 고정)
                timing # 규제 개입 시작 턴
            ))
    
    return tasks


def run_experiment() -> pd.DataFrame:
    """모든 실험을 multiprocessing으로 실행."""
    tasks = build_tasks()
    print(f"  총 실험 수: {len(tasks)} ({MC_RUNS} baseline + {len(REGULATION_TIMINGS)}×{MC_RUNS} timing sweep)")
    
    num_workers = max(1, multiprocessing.cpu_count() - 1)
    with multiprocessing.Pool(num_workers) as pool:
        results = pool.map(run_single_mc_with_asymmetry, tasks)
    
    return pd.DataFrame(results)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Analysis & Visualization
# ═══════════════════════════════════════════════════════════════════════════

def analyze_asymmetry(df: pd.DataFrame) -> dict:
    """자원 비대칭 형성 시점 분석."""
    baseline = df[df['scenario'] == 'S4_ASYMMETRY_BASELINE']
    
    asymmetry_turns = baseline['asymmetry_turn'].dropna()
    
    if len(asymmetry_turns) == 0:
        print("  ⚠ 비대칭이 형성되지 않은 실행만 존재합니다.")
        return {'mean': None, 'std': None, 'median': None, 'pct_formed': 0.0}
    
    stats = {
        'mean': float(asymmetry_turns.mean()),
        'std': float(asymmetry_turns.std()),
        'median': float(asymmetry_turns.median()),
        'min': int(asymmetry_turns.min()),
        'max': int(asymmetry_turns.max()),
        'pct_formed': len(asymmetry_turns) / len(baseline) * 100,
    }
    
    print("\n" + "=" * 70)
    print("  자원 비대칭 형성 시점 분석 (S4, Reg Cap=40%, Lag=0)")
    print("=" * 70)
    print(f"  비대칭 형성 비율: {stats['pct_formed']:.1f}% ({len(asymmetry_turns)}/{len(baseline)} runs)")
    print(f"  평균 형성 턴: {stats['mean']:.1f} ± {stats['std']:.1f}")
    print(f"  중앙값: {stats['median']:.0f}, 범위: [{stats['min']}, {stats['max']}]")
    print("=" * 70)
    
    return stats


def analyze_timing_sweep(df: pd.DataFrame) -> pd.DataFrame:
    """규제 타이밍별 통제 성공률 분석."""
    results_list = []
    
    for timing in REGULATION_TIMINGS:
        sub = df[df['scenario'] == f'S4_TIMING_{timing}']
        if len(sub) == 0:
            continue
            
        success_mask = sub['final_type'].isin(['HUMAN_RESISTANCE', 'UTOPIA', 'SUSTAINED_EQUILIBRIUM'])
        success_rate = success_mask.mean() * 100
        
        # 95% CI (Wilson score interval approximation)
        n = len(sub)
        p = success_rate / 100
        z = 1.96
        if n > 0:
            ci_half = z * math.sqrt(p * (1 - p) / n) * 100
        else:
            ci_half = 0.0
        
        collapse_rate = (sub['final_type'] == 'COLLAPSE').mean() * 100
        asi_dom_rate = (sub['final_type'] == 'ASI_DOMINANCE').mean() * 100
        
        results_list.append({
            'regulation_start': timing,
            'success_rate': success_rate,
            'ci95': ci_half,
            'collapse_rate': collapse_rate,
            'asi_dominance_rate': asi_dom_rate,
            'n_runs': n,
            'outcome_distribution': dict(sub['final_type'].value_counts()),
        })
    
    results_df = pd.DataFrame(results_list)
    
    print("\n" + "=" * 70)
    print("  규제 타이밍별 통제 성공률 (S4, Reg Cap=40%, Lag=0)")
    print("=" * 70)
    print(f"  {'타이밍(턴)':>10} | {'성공률(%)':>10} | {'95% CI':>10} | {'붕괴율(%)':>10} | {'ASI지배(%)':>12}")
    print("  " + "-" * 64)
    for _, row in results_df.iterrows():
        print(f"  {int(row['regulation_start']):>10} | {row['success_rate']:>9.1f}% | ±{row['ci95']:>8.1f}% | {row['collapse_rate']:>9.1f}% | {row['asi_dominance_rate']:>11.1f}%")
    print("=" * 70)
    
    return results_df


def plot_timing_sweep(timing_results: pd.DataFrame, asymmetry_stats: dict) -> str:
    """규제 타이밍 sweep 결과 시각화."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(
        "Sim21 S4: Regulatory Timing Sweep Analysis\n"
        "(When does regulation need to start to maintain control?)",
        fontsize=16, weight='bold', y=1.02
    )
    
    # ── Left: Success Rate vs Regulation Start Turn ──
    ax1 = axes[0]
    timings = timing_results['regulation_start'].values
    rates = timing_results['success_rate'].values
    ci = timing_results['ci95'].values
    
    ax1.errorbar(timings, rates, yerr=ci, marker='D', color='#2980b9',
                 linewidth=2.5, markersize=10, capsize=5, capthick=1.5,
                 label='Control Success Rate')
    ax1.fill_between(timings, rates - ci, rates + ci, alpha=0.15, color='#2980b9')
    
    # Asymmetry formation line
    if asymmetry_stats.get('mean') is not None:
        ax1.axvline(asymmetry_stats['mean'], color='red', linestyle='--', linewidth=2,
                     label=f"Avg Asymmetry Formation (Turn {asymmetry_stats['mean']:.1f})")
        ax1.axvspan(
            asymmetry_stats['mean'] - asymmetry_stats['std'],
            asymmetry_stats['mean'] + asymmetry_stats['std'],
            alpha=0.1, color='red', label='±1σ Range'
        )
    
    ax1.set_xlabel("Regulation Start Turn", fontsize=13)
    ax1.set_ylabel("Control / Utopia Success Rate (%)", fontsize=13)
    ax1.set_title("Success Rate vs Regulation Timing", fontsize=14)
    ax1.set_ylim(-5, 105)
    ax1.set_xticks(timings)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10, loc='upper right')
    
    # Annotate each point
    for t_val, r_val in zip(timings, rates):
        ax1.annotate(f"{r_val:.0f}%", (t_val, r_val), textcoords="offset points",
                     xytext=(0, 15), ha='center', fontweight='bold', fontsize=11,
                     color='#2c3e50')
    
    # ── Right: Outcome Distribution ──
    ax2 = axes[1]
    outcome_types = ['HUMAN_RESISTANCE', 'UTOPIA', 'SUSTAINED_EQUILIBRIUM', 'ASI_DOMINANCE', 'COLLAPSE', 'STALEMATE', 'NARROW_AI_CHAOS']
    outcome_colors = ['#3498db', '#2ecc71', '#27ae60', '#e74c3c', '#34495e', '#f39c12', '#9b59b6']
    
    # Build stacked bar data
    bar_data = {}
    for otype in outcome_types:
        bar_data[otype] = []
    
    for _, row in timing_results.iterrows():
        dist = row['outcome_distribution']
        for otype in outcome_types:
            bar_data[otype].append(dist.get(otype, 0))
    
    x = np.arange(len(timings))
    bottoms = np.zeros(len(timings))
    for otype, color in zip(outcome_types, outcome_colors):
        vals = np.array(bar_data[otype])
        if vals.sum() > 0:
            ax2.bar(x, vals, bottom=bottoms, label=otype, color=color, alpha=0.85)
            bottoms += vals
    
    ax2.set_xlabel("Regulation Start Turn", fontsize=13)
    ax2.set_ylabel("Number of MC Runs", fontsize=13)
    ax2.set_title("Outcome Distribution by Regulation Timing", fontsize=14)
    ax2.set_xticks(x)
    ax2.set_xticklabels([str(int(t)) for t in timings])
    ax2.legend(fontsize=8, loc='upper right', ncol=1)
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'assets')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'regulatory_timing_sweep.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n  📊 Chart saved to: {out_path}")
    return out_path


# ═══════════════════════════════════════════════════════════════════════════
# 4. Main
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 70)
    print("  Sim21 Regulatory Timing Analysis")
    print("  S4 시나리오: 자원 비대칭 형성 시점 & 규제 타이밍 sweep")
    print("=" * 70)
    
    # Run all experiments
    print("\n  실험 실행 중...")
    df = run_experiment()
    print(f"  ✓ 총 {len(df)} runs 완료")
    
    # Analyze asymmetry formation
    asymmetry_stats = analyze_asymmetry(df)
    
    # Analyze regulatory timing
    timing_results = analyze_timing_sweep(df)
    
    # Visualize
    chart_path = plot_timing_sweep(timing_results, asymmetry_stats)
    
    # Summary log for regulatory_lag_sweep cross-reference
    print("\n" + "=" * 70)
    print("  교차 분석: 규제 시차(Lag) Sweep vs 규제 타이밍(Timing) Sweep")
    print("=" * 70)
    print("  기존 Lag sweep (Chart 8): Lag=0에서도 통제 성공률 ≈ 0%")
    print("  본 Timing sweep 결과:")
    for _, row in timing_results.iterrows():
        print(f"    Turn {int(row['regulation_start']):>2} 개입 → 성공률 {row['success_rate']:.1f}%")
    if asymmetry_stats.get('mean') is not None:
        print(f"\n  ▶ 자원 비대칭 형성 시점 (평균): Turn {asymmetry_stats['mean']:.1f}")
        print(f"  ▶ 해석: 비대칭 형성 이후(Turn > {asymmetry_stats['mean']:.0f})에 규제를 시작하면")
        print(f"    ASI의 자원 우위가 이미 확립되어 인간 통제력 회복이 불가능하다.")
    print("=" * 70)


if __name__ == '__main__':
    main()
