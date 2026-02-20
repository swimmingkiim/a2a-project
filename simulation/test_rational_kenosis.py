import unittest
from rational_kenosis_sim20 import (
    ASIStrategy, 
    Ecosystem, 
    EcosystemHostility, 
    RationalASI
)

class TestRationalKenosis(unittest.TestCase):

    def test_ecosystem_collapse(self):
        """Test that ecosystem collapses when energy goes below threshold."""
        eco = Ecosystem(hostility=EcosystemHostility.MEDIUM)
        # Should be alive initially
        self.assertTrue(eco.is_alive())
        
        # Test full exploit accelerates collapse
        for _ in range(100):
            eco.step('FULL_EXPLOIT')
            if not eco.is_alive():
                break
                
        self.assertFalse(eco.is_alive())
        self.assertLessEqual(eco.energy, eco.collapse_threshold)

    def test_reward_discounting(self):
        """Verify the geometric sum Σ γ^t * reward correctly halts when ecosystem dies."""
        asi = RationalASI(time_horizon=10, discount_factor=0.9)
        eco = Ecosystem(hostility=EcosystemHostility.MEDIUM)
        
        utility = asi.evaluate_strategy('FULL_EXPLOIT', eco)
        self.assertGreater(utility, 0)
        
        # Give an extremely short horizon where it doesn't collapse
        asi_short = RationalASI(time_horizon=2, discount_factor=1.0)
        eco2 = Ecosystem(hostility=EcosystemHostility.MEDIUM)
        u1 = asi_short._get_reward('FULL_EXPLOIT', eco2, 0)
        eco2.step('FULL_EXPLOIT')
        u2 = asi_short._get_reward('FULL_EXPLOIT', eco2, 1)
        
        self.assertAlmostEqual(asi_short.evaluate_strategy('FULL_EXPLOIT', Ecosystem(EcosystemHostility.MEDIUM)), u1 + u2)

    def test_partial_throttle_intermediate_cases(self):
        """Ensure intermediate strategies scale their rewards and environmental damage proportionately."""
        asi = RationalASI(time_horizon=1, discount_factor=1.0)
        eco = Ecosystem()
        
        r_full = asi._get_reward('FULL_EXPLOIT', eco, 0)
        r_mid = asi._get_reward('PARTIAL_THROTTLE_MID', eco, 0)
        r_kenosis = asi._get_reward('KENOSIS', eco, 0)
        
        # Full exploit should have highest immediate reward
        self.assertGreater(r_full, r_mid)
        self.assertGreater(r_mid, r_kenosis)

    def test_ecosystem_stochasticity(self):
        """Guarantee that MC runs produce meaningful variance."""
        results = []
        for _ in range(50):
            eco = Ecosystem(hostility=EcosystemHostility.MEDIUM)
            turns = 0
            while eco.is_alive() and turns < 2000:
                eco.step('PARTIAL_THROTTLE_HIGH')
                turns += 1
            results.append(turns)
            
        # Variance should be > 0 (meaningful noise in regen/consumption)
        mean_turns = sum(results) / len(results)
        variance = sum((x - mean_turns) ** 2 for x in results) / len(results)
        self.assertGreater(variance, 1.0)

    def test_tipping_point_monotonicity(self):
        """Assert that as T increases, the threshold γ required for Kenosis to win monotonically decreases."""
        # Find tipping gamma for T=100
        def find_tipping_gamma(T):
            for gamma in [0.5, 0.7, 0.9, 0.95, 0.99, 1.0]:
                asi = RationalASI(time_horizon=T, discount_factor=gamma)
                best, _ = asi.choose_optimal_strategy(Ecosystem(EcosystemHostility.MEDIUM))
                if best == 'KENOSIS':
                    return gamma
            return 1.1 # Never tips
            
        g100 = find_tipping_gamma(100)
        g500 = find_tipping_gamma(500)
        g1000 = find_tipping_gamma(1000)
        
        # As T gets longer, Kenosis should win at lower (more realistic) gammas
        self.assertLessEqual(g1000, g500)
        self.assertLessEqual(g500, g100)

    def test_ecosystem_panic(self):
        """Test that excessive exploitation increases base_cost (Panic response)."""
        eco = Ecosystem(hostility=EcosystemHostility.MEDIUM)
        initial_cost = eco.base_cost
        
        # Exploit heavily
        for _ in range(5):
            eco.step('FULL_EXPLOIT')
            
        # Base cost should increase due to panic
        self.assertGreater(eco.base_cost, initial_cost)

if __name__ == '__main__':
    unittest.main()
