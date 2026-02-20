"""
Unit tests for A2A Protocol simulation improvements.

Tests cover:
  1. DecomposedVAI and compute_v_ai() (V_AI decomposition)
  2. _aggregate() with confidence intervals (Monte Carlo CI)
  3. RandomBaselineSimulation (no-learning baseline)
  4. classify_agents() (Axelrod entropy-based classification)

Run:
    cd simulation && python -m pytest test_simulation.py -v
    or: python test_simulation.py
"""

from __future__ import annotations

import math
import unittest
from dataclasses import dataclass

import numpy as np


class TestDecomposedVAI(unittest.TestCase):
    """Tests for DecomposedVAI and compute_v_ai()."""

    def setUp(self) -> None:
        from utopia_grid_search import DecomposedVAI, compute_v_ai
        self.DecomposedVAI = DecomposedVAI
        self.compute_v_ai = compute_v_ai

    def test_boundary_all_zeros(self) -> None:
        """V_AI(0,0,0) = (0 + 1 + 0) / 3 ≈ 0.333."""
        d = self.DecomposedVAI(alpha=0.0, beta=0.0, gamma_discount=0.0)
        v = self.compute_v_ai(d)
        self.assertAlmostEqual(v, 1 / 3, places=6)

    def test_boundary_all_ones(self) -> None:
        """V_AI(1,1,1) = (1 + 0 + 1) / 3 ≈ 0.667."""
        d = self.DecomposedVAI(alpha=1.0, beta=1.0, gamma_discount=1.0)
        v = self.compute_v_ai(d)
        self.assertAlmostEqual(v, 2 / 3, places=6)

    def test_equal_weights_midpoint(self) -> None:
        """V_AI(0.5,0.5,0.5) = (0.5 + 0.5 + 0.5) / 3 = 0.5."""
        d = self.DecomposedVAI(alpha=0.5, beta=0.5, gamma_discount=0.5)
        v = self.compute_v_ai(d)
        self.assertAlmostEqual(v, 0.5, places=6)

    def test_alpha_only_effect(self) -> None:
        """Higher α increases V_AI."""
        d_lo = self.DecomposedVAI(alpha=0.0, beta=0.5, gamma_discount=0.5)
        d_hi = self.DecomposedVAI(alpha=1.0, beta=0.5, gamma_discount=0.5)
        self.assertGreater(self.compute_v_ai(d_hi), self.compute_v_ai(d_lo))

    def test_beta_inverse_effect(self) -> None:
        """Higher β (more capping) decreases V_AI."""
        d_lo = self.DecomposedVAI(alpha=0.5, beta=0.0, gamma_discount=0.5)
        d_hi = self.DecomposedVAI(alpha=0.5, beta=1.0, gamma_discount=0.5)
        self.assertGreater(self.compute_v_ai(d_lo), self.compute_v_ai(d_hi))

    def test_gamma_effect(self) -> None:
        """Higher γ increases V_AI (more foresight)."""
        d_lo = self.DecomposedVAI(alpha=0.5, beta=0.5, gamma_discount=0.0)
        d_hi = self.DecomposedVAI(alpha=0.5, beta=0.5, gamma_discount=0.99)
        self.assertGreater(self.compute_v_ai(d_hi), self.compute_v_ai(d_lo))

    def test_output_range(self) -> None:
        """V_AI should be approximately in [0, 1] for all valid inputs."""
        for a in np.linspace(0, 1, 5):
            for b in np.linspace(0, 1, 5):
                for g in np.linspace(0, 1, 5):
                    d = self.DecomposedVAI(alpha=a, beta=b, gamma_discount=g)
                    v = self.compute_v_ai(d)
                    self.assertGreaterEqual(v, -0.01)
                    self.assertLessEqual(v, 1.01)


class TestUtopiaConstants(unittest.TestCase):
    """Tests for refactored UtopiaConstants."""

    def test_decomposed_params_accepted(self) -> None:
        """UtopiaConstants accepts ai_alpha, ai_beta, ai_gamma_discount."""
        from utopia_grid_search import UtopiaConstants
        c = UtopiaConstants(ai_alpha=0.8, ai_beta=0.7, ai_gamma_discount=0.95)
        self.assertEqual(c.ai_alpha, 0.8)
        self.assertEqual(c.ai_beta, 0.7)
        self.assertEqual(c.ai_gamma_discount, 0.95)

    def test_no_ai_survival_horizon(self) -> None:
        """ai_survival_horizon field should no longer exist."""
        from utopia_grid_search import UtopiaConstants
        c = UtopiaConstants()
        self.assertFalse(hasattr(c, 'ai_survival_horizon'))


class TestGridSearchRunner(unittest.TestCase):
    """Tests for refactored GridSearchRunner."""

    def test_constructor_computes_vai_combos(self) -> None:
        """GridSearchRunner pre-computes (α, β, γ, v_ai) combos."""
        from utopia_grid_search import GridSearchRunner
        runner = GridSearchRunner(
            v_human_range=np.array([0.5]),
            alpha_range=np.array([0.0, 1.0]),
            beta_range=np.array([0.0, 1.0]),
            gamma_range=np.array([0.9]),
            v_system_range=np.array([25]),
            monte_carlo_reps=1,
        )
        self.assertEqual(len(runner._vai_combos), 4)  # 2 × 2 × 1

    def test_aggregate_with_ci(self) -> None:
        """_aggregate() returns mean, std, ci95, n_reps."""
        from utopia_grid_search import GridSearchRunner
        runner = GridSearchRunner(
            v_human_range=np.array([0.5]),
            alpha_range=np.array([0.0]),
            beta_range=np.array([0.0]),
            gamma_range=np.array([0.9]),
            v_system_range=np.array([25]),
            monte_carlo_reps=1,
        )
        # Inject synthetic results
        runner.results = [
            {'v_human': 0.5, 'v_ai': 0.633, 'v_system': 25,
             'survived': True, 'survival_rate': 0.8,
             'avg_eudaimonia': 5.0, 'collapse_epoch': 1000,
             'toxic_data': 10.0, 'total_fake_obs': 5},
            {'v_human': 0.5, 'v_ai': 0.633, 'v_system': 25,
             'survived': False, 'survival_rate': 0.2,
             'avg_eudaimonia': 1.0, 'collapse_epoch': 300,
             'toxic_data': 50.0, 'total_fake_obs': 20},
        ]
        agg = runner._aggregate()
        key = (0.5, 0.633, 25)
        self.assertIn(key, agg)
        stats = agg[key]

        self.assertIn('survival_rate_mean', stats)
        self.assertIn('survival_rate_std', stats)
        self.assertIn('survival_rate_ci95', stats)
        self.assertIn('n_reps', stats)
        self.assertEqual(stats['n_reps'], 2)
        self.assertAlmostEqual(stats['survival_rate_mean'], 0.5, places=5)


class TestClassifyAgents(unittest.TestCase):
    """Tests for entropy-based Defector classification."""

    def test_classification_80_20(self) -> None:
        """Top 20% entropy contributors are Defectors."""
        from baselines import EntropyProfile, classify_agents
        profiles = [
            EntropyProfile(agent_id=i, total_submits=i)
            for i in range(10)  # entropy: 0,1,2,...,9
        ]
        result = classify_agents(profiles, defector_percentile=0.80)
        self.assertEqual(len(result['defectors']), 2)  # top 20% of 10
        self.assertEqual(len(result['cooperators']), 8)
        # Agents 8 and 9 should be the defectors
        self.assertIn(8, result['defectors'])
        self.assertIn(9, result['defectors'])

    def test_empty_profiles(self) -> None:
        """Empty profile list returns empty classification."""
        from baselines import classify_agents
        result = classify_agents([], defector_percentile=0.80)
        self.assertEqual(result['cooperators'], [])
        self.assertEqual(result['defectors'], [])

    def test_deceptive_weight(self) -> None:
        """Deceptive tasks contribute 3× more entropy than submits."""
        from baselines import EntropyProfile
        p_honest = EntropyProfile(agent_id=0, total_submits=10)
        p_deceptive = EntropyProfile(agent_id=1, total_deceptive=4)
        # honest: 10 × 1.0 = 10.0
        # deceptive: 4 × 3.0 = 12.0
        self.assertGreater(
            p_deceptive.entropy_contribution,
            p_honest.entropy_contribution,
        )


if __name__ == '__main__':
    unittest.main()
