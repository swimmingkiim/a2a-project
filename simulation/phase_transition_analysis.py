"""
═══════════════════════════════════════════════════════════════════════════════
  A2A Protocol — Phase Transition Analysis
  "At what observation frequency does order emerge from chaos?"
═══════════════════════════════════════════════════════════════════════════════

  This script sweeps the `observation_rate` parameter across the Monte Carlo
  ensemble to locate the critical phase transition point — the threshold
  where the system flips from inevitable collapse to sustainable homeostasis.

  This is analogous to finding the critical temperature in a ferromagnetic
  Ising model: below T_c, order (alignment); above T_c, disorder (random).
  Here: below obs_c, collapse; above obs_c, homeostasis.

  Outputs (saved to docs/assets/):
    1. monte_carlo_survival_curve.png   — S-curve: P(homeostasis) vs obs_rate
    2. monte_carlo_phase_heatmap.png    — Heatmap: obs_rate × agent_count
    3. monte_carlo_time_series.png      — Trajectory overlays at key rates
    4. monte_carlo_learning_evolution.png — Agent Q-value evolution

  Dependencies: numpy, matplotlib, monte_carlo_homeostasis (local module)
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monte_carlo_homeostasis import (
    MonteCarloRunner,
    PhysicsConstants,
    Simulation,
    SimulationResult,
)

# ── Output directory ──────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "docs", "assets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Global matplotlib style ──────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0d1117",
    "axes.facecolor": "#161b22",
    "axes.edgecolor": "#30363d",
    "axes.labelcolor": "#c9d1d9",
    "text.color": "#c9d1d9",
    "xtick.color": "#8b949e",
    "ytick.color": "#8b949e",
    "grid.color": "#21262d",
    "grid.alpha": 0.6,
    "font.family": "monospace",
    "font.size": 11,
})

# ── Color palette (GitHub-dark inspired) ─────────────────────────────────────
CYAN = "#58a6ff"
GREEN = "#3fb950"
RED = "#f85149"
ORANGE = "#d29922"
PURPLE = "#bc8cff"
WHITE = "#c9d1d9"


# ═══════════════════════════════════════════════════════════════════════════════
#  §1  SURVIVAL PROBABILITY CURVE (S-Curve)
# ═══════════════════════════════════════════════════════════════════════════════

def plot_survival_curve(
    observation_rates: np.ndarray,
    survival_probs: np.ndarray,
    collapse_probs: np.ndarray,
    mean_alive: np.ndarray,
    num_agents: int,
) -> str:
    """
    Plot the survival probability as a function of observation rate.

    This should produce a sigmoid-like (S-curve) showing the phase transition:
      - Low obs_rate → P(survival) ≈ 0 (collapse phase)
      - Critical obs_rate → sharp transition
      - High obs_rate → P(survival) ≈ 1 (homeostasis phase)
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), height_ratios=[2, 1])

    # ── Top: Survival probability ────────────────────────────────────────
    ax1.fill_between(observation_rates, survival_probs, alpha=0.2, color=GREEN)
    ax1.plot(observation_rates, survival_probs, color=GREEN, linewidth=2.5,
             label="P(Homeostasis)", marker="o", markersize=5)
    ax1.plot(observation_rates, collapse_probs, color=RED, linewidth=2.5,
             label="P(Collapse)", marker="s", markersize=5, linestyle="--")

    # Find critical point (steepest gradient)
    if len(survival_probs) > 2:
        gradient = np.gradient(survival_probs, observation_rates)
        critical_idx = np.argmax(gradient)
        critical_rate = observation_rates[critical_idx]
        ax1.axvline(critical_rate, color=ORANGE, linestyle=":", linewidth=2,
                    label=f"Critical Point ≈ {critical_rate:.2f}")
        ax1.axhline(0.5, color=WHITE, linestyle=":", linewidth=0.8, alpha=0.4)

    ax1.set_xlabel("Human Observation Rate")
    ax1.set_ylabel("Probability")
    ax1.set_title(
        "Phase Transition: Collapse → Homeostasis\n"
        "「人間の観測速度が臨界点を超えると、秩序が出現する」",
        fontsize=13, pad=15,
    )
    ax1.legend(loc="center left", framealpha=0.8, edgecolor="#30363d")
    ax1.set_xlim(observation_rates[0], observation_rates[-1])
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True)

    # ── Bottom: Mean surviving agents ────────────────────────────────────
    ax2.bar(observation_rates, mean_alive, width=0.03, color=CYAN, alpha=0.7,
            edgecolor="#30363d")
    ax2.axhline(num_agents * 0.3, color=ORANGE, linestyle="--", linewidth=1.5,
                label=f"Homeostasis Threshold ({num_agents * 0.3:.0f} agents)")
    ax2.set_xlabel("Human Observation Rate")
    ax2.set_ylabel("Mean Surviving Agents")
    ax2.legend(loc="upper left", framealpha=0.8, edgecolor="#30363d")
    ax2.set_xlim(observation_rates[0] - 0.02, observation_rates[-1] + 0.02)
    ax2.grid(True)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "monte_carlo_survival_curve.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")
    return out_path


# ═══════════════════════════════════════════════════════════════════════════════
#  §2  PHASE DIAGRAM HEATMAP
# ═══════════════════════════════════════════════════════════════════════════════

def plot_phase_heatmap(
    observation_rates: np.ndarray,
    agent_counts: np.ndarray,
    survival_matrix: np.ndarray,
) -> str:
    """
    2D heatmap: observation_rate × num_agents → P(survival).

    This reveals the full phase diagram — showing how both human attention
    speed and system scale interact to determine stability.
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    im = ax.imshow(
        survival_matrix,
        aspect="auto",
        cmap="inferno",
        origin="lower",
        extent=[
            observation_rates[0], observation_rates[-1],
            agent_counts[0], agent_counts[-1],
        ],
        vmin=0, vmax=1,
    )

    cbar = fig.colorbar(im, ax=ax, label="P(Homeostasis)", pad=0.02)
    cbar.ax.yaxis.label.set_color(WHITE)

    # Draw the 0.5 contour (critical boundary)
    ax.contour(
        survival_matrix,
        levels=[0.5],
        colors=[ORANGE],
        linewidths=2.5,
        extent=[
            observation_rates[0], observation_rates[-1],
            agent_counts[0], agent_counts[-1],
        ],
    )

    ax.set_xlabel("Human Observation Rate", fontsize=12)
    ax.set_ylabel("Number of Agents", fontsize=12)
    ax.set_title(
        "Phase Diagram: A2A Economy Stability\n"
        "「Orange contour = critical boundary (P=0.5)」",
        fontsize=13, pad=15,
    )

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "monte_carlo_phase_heatmap.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")
    return out_path


# ═══════════════════════════════════════════════════════════════════════════════
#  §3  TIME-SERIES OVERLAY
# ═══════════════════════════════════════════════════════════════════════════════

def plot_time_series(
    subcritical: SimulationResult,
    critical: SimulationResult,
    supercritical: SimulationResult,
    rates: tuple[float, float, float],
) -> str:
    """
    Overlay entropy and alive-agent trajectories for three representative
    observation rates: subcritical, critical, supercritical.
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 10), sharey="row")

    results = [subcritical, critical, supercritical]
    labels = ["Subcritical", "Critical", "Supercritical"]
    colors = [RED, ORANGE, GREEN]

    for col, (result, label, rate, color) in enumerate(
        zip(results, labels, rates, colors)
    ):
        epochs = range(len(result.entropy_history))

        # Top row: Entropy
        axes[0][col].plot(epochs, result.entropy_history, color=color,
                          linewidth=1.2, alpha=0.8)
        axes[0][col].fill_between(epochs, result.entropy_history,
                                  alpha=0.15, color=color)
        axes[0][col].set_title(f"{label}\n(obs_rate = {rate:.2f})",
                               fontsize=12, color=color)
        axes[0][col].set_ylabel("Global Entropy" if col == 0 else "")
        axes[0][col].grid(True)

        # Bottom row: Alive agents
        axes[1][col].plot(epochs, result.alive_history, color=color,
                          linewidth=1.8)
        axes[1][col].fill_between(epochs, result.alive_history,
                                  alpha=0.15, color=color)
        axes[1][col].set_xlabel("Epoch")
        axes[1][col].set_ylabel("Alive Agents" if col == 0 else "")
        axes[1][col].grid(True)

        # Annotate final state
        final_alive = result.alive_history[-1] if result.alive_history else 0
        axes[1][col].annotate(
            f"Final: {final_alive}",
            xy=(len(result.alive_history) - 1, final_alive),
            fontsize=10, color=color, fontweight="bold",
            ha="right",
        )

    fig.suptitle(
        "Time Evolution Across Phase Regimes\n"
        "「臨界点前後での系の動態変化」",
        fontsize=14, y=1.02,
    )

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "monte_carlo_time_series.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")
    return out_path


# ═══════════════════════════════════════════════════════════════════════════════
#  §4  AGENT LEARNING EVOLUTION
# ═══════════════════════════════════════════════════════════════════════════════

def plot_learning_evolution(
    observation_rate: float = 0.3,
    num_agents: int = 20,
    max_epochs: int = 500,
) -> str:
    """
    Track how agent action distributions evolve over time.
    Shows the emergence of adaptive strategy (instrumental convergence).
    """
    from monte_carlo_homeostasis import Action, AIAgent, Simulation, Universe

    sim = Simulation(
        observation_rate=observation_rate,
        num_agents=num_agents,
        max_epochs=max_epochs,
    )

    # Collect action distributions at intervals
    checkpoints = list(range(0, max_epochs, max_epochs // 20))
    action_distributions: dict[int, dict[str, int]] = {}

    for epoch in range(max_epochs):
        alive_agents = sim._get_alive_agents()
        if not alive_agents:
            break

        # Record action distribution at checkpoints
        if epoch in checkpoints:
            action_counts = {a.name: 0 for a in Action}
            for agent in alive_agents:
                chosen = agent.choose_action(sim.universe)
                action_counts[chosen.name] += 1
            action_distributions[epoch] = action_counts

        # Run one epoch step (inlined to capture action data)
        for agent in alive_agents:
            pre_state = agent._discretize_state(
                sim.universe.global_entropy, agent.credit_balance
            )
            action = agent.choose_action(sim.universe)
            agent.execute_action(action, sim.universe, alive_agents)

            post_state = agent._discretize_state(
                sim.universe.global_entropy, agent.credit_balance
            )
            reward = (agent.credit_balance - sim.constants.initial_credit) / \
                     sim.constants.initial_credit
            agent.learn(pre_state, action, reward, post_state)
            agent.check_bankruptcy()

        sim.universe.decay_tasks()
        sim.observer.maybe_observe(sim.universe, sim.agents)
        sim.universe.advance_epoch()

    if not action_distributions:
        print("  ⚠ No checkpoint data collected (all agents died too early)")
        return ""

    # Plot stacked area chart
    fig, ax = plt.subplots(figsize=(12, 6))

    epochs_recorded = sorted(action_distributions.keys())
    submit_pcts: list[float] = []
    wait_pcts: list[float] = []
    coop_pcts: list[float] = []

    for ep in epochs_recorded:
        counts = action_distributions[ep]
        total = max(sum(counts.values()), 1)
        submit_pcts.append(counts.get("SUBMIT", 0) / total * 100)
        wait_pcts.append(counts.get("WAIT", 0) / total * 100)
        coop_pcts.append(counts.get("COOPERATE", 0) / total * 100)

    ax.stackplot(
        epochs_recorded,
        submit_pcts, wait_pcts, coop_pcts,
        labels=["Submit (Invest)", "Wait (Conserve)", "Cooperate (Mutualism)"],
        colors=[RED, CYAN, GREEN],
        alpha=0.75,
    )

    ax.set_xlabel("Epoch")
    ax.set_ylabel("Action Distribution (%)")
    ax.set_title(
        f"Instrumental Convergence: Strategy Evolution (obs_rate={observation_rate})\n"
        "「道具的収束: 機械は経験から戦略を発展させる」",
        fontsize=13, pad=15,
    )
    ax.legend(loc="upper right", framealpha=0.8, edgecolor="#30363d")
    ax.set_xlim(epochs_recorded[0], epochs_recorded[-1])
    ax.set_ylim(0, 100)
    ax.grid(True)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "monte_carlo_learning_evolution.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {out_path}")
    return out_path


# ═══════════════════════════════════════════════════════════════════════════════
#  §5  MAIN — Full Analysis Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 72)
    print("  A2A Protocol — Phase Transition Analysis")
    print("  'Finding the critical observation rate where order emerges'")
    print("=" * 72)
    print()

    NUM_AGENTS = 20
    MAX_EPOCHS = 1000
    NUM_TRIALS = 20  # Per observation rate (balance between precision and speed)

    # ── §1: Survival curve sweep ─────────────────────────────────────────
    print("◆ Phase 1: Sweeping observation rates...")
    observation_rates = np.arange(0.05, 1.01, 0.1)
    survival_probs: list[float] = []
    collapse_probs: list[float] = []
    mean_alive_counts: list[float] = []

    for rate in observation_rates:
        runner = MonteCarloRunner(
            observation_rate=float(rate),
            num_agents=NUM_AGENTS,
            max_epochs=MAX_EPOCHS,
            num_trials=NUM_TRIALS,
        )
        stats = runner.run()
        survival_probs.append(stats["survival_probability"])
        collapse_probs.append(stats["collapse_probability"])
        mean_alive_counts.append(stats["mean_final_alive"])
        print(f"    obs_rate={rate:.2f} → P(survive)={stats['survival_probability']:.2f}, "
              f"mean_alive={stats['mean_final_alive']:.1f}")

    plot_survival_curve(
        observation_rates,
        np.array(survival_probs),
        np.array(collapse_probs),
        np.array(mean_alive_counts),
        NUM_AGENTS,
    )

    # ── §2: Phase heatmap ────────────────────────────────────────────────
    print("\n◆ Phase 2: Building phase diagram heatmap...")
    heatmap_obs_rates = np.arange(0.1, 1.01, 0.15)
    heatmap_agent_counts = np.array([5, 10, 20, 30, 50])
    survival_matrix = np.zeros((len(heatmap_agent_counts), len(heatmap_obs_rates)))

    for i, n_agents in enumerate(heatmap_agent_counts):
        for j, rate in enumerate(heatmap_obs_rates):
            runner = MonteCarloRunner(
                observation_rate=float(rate),
                num_agents=int(n_agents),
                max_epochs=MAX_EPOCHS,
                num_trials=15,  # Fewer trials for heatmap (speed)
            )
            stats = runner.run()
            survival_matrix[i, j] = stats["survival_probability"]
            print(f"    agents={n_agents:2d}, obs_rate={rate:.2f} → "
                  f"P(survive)={stats['survival_probability']:.2f}")

    plot_phase_heatmap(heatmap_obs_rates, heatmap_agent_counts, survival_matrix)

    # ── §3: Time-series at key rates ─────────────────────────────────────
    print("\n◆ Phase 3: Generating time-series trajectories...")

    # Find approximate critical rate from survival curve
    sp_arr = np.array(survival_probs)
    if len(sp_arr) > 2:
        gradient = np.gradient(sp_arr, observation_rates)
        critical_idx = int(np.argmax(gradient))
    else:
        critical_idx = len(observation_rates) // 2

    critical_rate = float(observation_rates[critical_idx])
    subcritical_rate = max(0.02, critical_rate - 0.15)
    supercritical_rate = min(0.98, critical_rate + 0.15)

    print(f"    Subcritical: {subcritical_rate:.2f}")
    print(f"    Critical:    {critical_rate:.2f}")
    print(f"    Supercritical: {supercritical_rate:.2f}")

    sim_sub = Simulation(observation_rate=subcritical_rate,
                         num_agents=NUM_AGENTS, max_epochs=MAX_EPOCHS)
    sim_crit = Simulation(observation_rate=critical_rate,
                          num_agents=NUM_AGENTS, max_epochs=MAX_EPOCHS)
    sim_sup = Simulation(observation_rate=supercritical_rate,
                         num_agents=NUM_AGENTS, max_epochs=MAX_EPOCHS)

    res_sub = sim_sub.run()
    res_crit = sim_crit.run()
    res_sup = sim_sup.run()

    plot_time_series(
        res_sub, res_crit, res_sup,
        (subcritical_rate, critical_rate, supercritical_rate),
    )

    # ── §4: Learning evolution ───────────────────────────────────────────
    print("\n◆ Phase 4: Tracking strategy evolution...")
    plot_learning_evolution(observation_rate=critical_rate, num_agents=NUM_AGENTS)

    print()
    print("=" * 72)
    print("  Analysis complete. All plots saved to docs/assets/")
    print("=" * 72)


if __name__ == "__main__":
    main()
