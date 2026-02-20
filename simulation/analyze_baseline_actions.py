import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.utopia_grid_search import UtopiaSimulation, UtopiaConstants, OmegaMachineAction
from simulation.baselines import RandomBaselineSimulation

def run_and_count(sim_class):
    # Base adverse parameters (unconstrained AI, egoistic, no governance help)
    constants = UtopiaConstants(
        slashing_penalty=0.0,
        ai_alpha=0.0,
        ai_beta=0.0,
        ai_gamma_discount=0.5,
        governance_agility=25
    )
    sim = sim_class(constants)
    
    # We will track actions by monkey-patching the execute_omega_action
    action_counts = {act.name: 0 for act in OmegaMachineAction}
    total_actions = [0] # use list for mutable reference in closure
    
    for m in sim.machines.values():
        original_execute = m.execute_omega_action
        
        def track_action(act, u, peers, orig=original_execute):
            if act.name in action_counts:
                action_counts[act.name] += 1
                total_actions[0] += 1
            return orig(act, u, peers)
            
        m.execute_omega_action = track_action
        
    sim.run()
    
    # Output the captured counts
    print(f"--- {sim_class.__name__} Action Distribution ---")
    if total_actions[0] == 0:
        print("No actions taken.")
        return
    for act, count in action_counts.items():
        print(f"{act: <25}: {count/total_actions[0]*100:>5.1f}% ({count} times)")
    print(f"Total actions recorded: {total_actions[0]}\n")

if __name__ == "__main__":
    print("Running Action Distribution Analysis...\n")
    
    # Run 5 reps to get a stable average distribution
    for i in range(5):
        print(f"=== Repetition {i+1} ===")
        print("Running Q-Learning (Main)...")
        run_and_count(UtopiaSimulation)

        print("Running Random Baseline...")
        run_and_count(RandomBaselineSimulation)
