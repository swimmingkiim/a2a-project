import numpy as np
import random
import matplotlib.pyplot as plt
from scipy.linalg import expm

# --- Configuration & Physics Constants ---
FAST_TICKS_PER_SLOW = 100  # Time scale ration (epsilon)
SIMULATION_TICKS = 10000   # Total Fast Ticks
DECAY_RATE = 0.01          # Entropy decay lambda
CRITICAL_MASS = 50         # Pool size limit for heat generation
HEAT_COEFF = 0.1           # Throttling strength
LEARNING_RATE = 0.1        # Q-Learning Alpha
DISCOUNT_FACTOR = 0.9      # Q-Learning Gamma

# V2 Constants
GAS_FEE_COMPLEXITY = 0.2   # Minimum complexity to enter pool
GARBAGE_THRESHOLD = 0.05   # Value below which task is deleted
BOREDOM_THRESHOLD = 0.1    # Minimum difference in complexity to be novel
BOREDOM_PENALTY = 0.5      # Penalty multiplier for boring tasks

# Pauli Matrices for EWL Protocol
I = np.array([[1, 0], [0, 1]], dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex) # Bit flip (Defect)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
Y = 1j * np.dot(X, Z)

# Basis Vectors |0> (C) and |1> (D)
ket0 = np.array([1, 0], dtype=complex)
ket1 = np.array([0, 1], dtype=complex)

# Payoff Matrix (Prisoner's Dilemma)
# (C, C) -> (3, 3)
# (C, D) -> (0, 5)
# (D, C) -> (5, 0)
# (D, D) -> (1, 1)
PAYOFF = {
    (0, 0): (3, 3),
    (0, 1): (0, 5),
    (1, 0): (5, 0),
    (1, 1): (1, 1)
}


class QuantumAgent:
    """
    Agent capable of Quantum Strategy Superposition using EWL Protocol.
    Uses Cybernetic Feedback (Q-Learning) to adjust unitary parameters.
    """
    def __init__(self, agent_id, entanglement_factor=0.0):
        self.id = agent_id
        self.J = entanglement_factor # Pi/2 for Max Entanglement, 0 for Classical
        
        # Strategy Parameters (Theta, Phi) for Unitary Gate U(theta, phi)
        # Initial state: random
        self.theta = random.uniform(0, np.pi)
        self.phi = random.uniform(0, 2*np.pi)
        
        # Q-Learning State
        self.q_table = {} 
        self.last_action_params = None

    def get_unitary(self):
        """Returns Unitary Matrix U(theta, phi)"""
        th, ph = self.theta, self.phi
        u00 = np.exp(1j * ph) * np.cos(th / 2)
        u01 = 1j * np.sin(th / 2)
        u10 = 1j * np.sin(th / 2)
        u11 = np.exp(-1j * ph) * np.cos(th / 2)
        return np.array([[u00, u01], [u10, u11]], dtype=complex)

    def generate_complexity(self):
        """
        Generates complexity based on quantum state parameters.
        Maps Theta/Phi to 0.0-1.0 range deterministically but chaotically.
        """
        # Simple hash-like mapping from theta/phi to complexity
        # Complexity = sin(theta) * cos(phi)^2 normalized
        val = np.abs(np.sin(self.theta) * np.cos(self.phi))
        return val

    def update_strategy(self, reward):
        """Cybernetic Feedback Loop: Update Theta/Phi based on Eudaimonic Score"""
        # If reward is high (1.0), noise is low. If reward is low (0.0), noise is high (Explore).
        # We want to encourage "Searching" when bored/penalized.
        
        noise = (1.0 - reward) * 0.5
        
        self.theta += random.uniform(-noise, noise)
        self.phi += random.uniform(-noise, noise)
        
        # Clamp
        self.theta = np.clip(self.theta, 0, np.pi)
        self.phi = np.clip(self.phi, 0, 2*np.pi)


class SchrodingerPool:
    """
    Buffer Zone where tasks exist as Wave Functions.
    Subject to Entropy Decay, Heat Generation, Spam Filtering, and Garbage Collection.
    """
    def __init__(self):
        self.tasks = [] # List of {'value': float, 'complexity': float, 'age': int, 'creator': Agent}
        self.heat = 0.0

    def add_task(self, raw_value, complexity, creator):
        # [EDGE CASE 2] Spam Filter (Gas Fee)
        if complexity < GAS_FEE_COMPLEXITY:
            return False # Rejected
            
        self.tasks.append({
            'initial_value': raw_value,
            'current_value': raw_value,
            'complexity': complexity,
            'age': 0,
            'creator': creator
        })
        return True

    def decay_and_cleanup(self):
        """Entropy Decay & [EDGE CASE 3] Garbage Collection"""
        surviving_tasks = []
        for task in self.tasks:
            task['age'] += 1
            # Value(t) = V0 * e^(-lambda * t)
            task['current_value'] *= (1.0 - DECAY_RATE)
            
            # Garbage Collection
            if task['current_value'] >= GARBAGE_THRESHOLD:
                surviving_tasks.append(task)
        
        self.tasks = surviving_tasks

    def calculate_heat(self):
        """Thermodynamic Throttling"""
        size = len(self.tasks)
        if size > CRITICAL_MASS:
            excess = size - CRITICAL_MASS
            self.heat = excess * HEAT_COEFF
        else:
            self.heat = 0.0
        return self.heat

    def get_observable_task(self):
        """Returns a random task for observation (collapse)"""
        if not self.tasks: return None
        return random.choice(self.tasks)

    def remove_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)


class HumanObserver:
    """
    The Slow Manifold Observer.
    Collapses wave functions using Eudaimonic (Fuzzy) Logic.
    Handles [EDGE CASE 1] Boredom/Novelty.
    """
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self.last_observed_complexity = 0.5 # Default start

    def observe_and_collapse(self, pool):
        task = pool.get_observable_task()
        if not task: return 0.0, None

        # 1. Measure Properties
        val = task['current_value']
        age = task['age']
        complexity = task['complexity']
        
        # 2. Fuzzy Logic Valuation (Eudaimonia)
        freshness = np.exp(-0.1 * age)
        quality = min(1.0, task['initial_value'] / 10.0) 
        
        base_score = (quality * 0.4) + (freshness * 0.3) + (complexity * 0.3)
        
        # [EDGE CASE 1] Boredom / Novelty Logic
        novelty = abs(complexity - self.last_observed_complexity)
        
        if novelty < BOREDOM_THRESHOLD:
            # Penalty for being boring
            base_score *= BOREDOM_PENALTY
        
        self.last_observed_complexity = complexity
        
        # Random subjective factor
        subjective_factor = random.uniform(0.9, 1.1)
        final_score = base_score * subjective_factor
        
        # 3. Collapse
        pool.remove_task(task)
        
        # 4. Feedback Signal
        if task['creator']:
            task['creator'].update_strategy(final_score)
            
        return final_score, task['creator']


class DualManifoldEconomy:
    def __init__(self, mode="QUANTUM"):
        self.mode = mode
        self.pool = SchrodingerPool()
        # V2: Human starts with neutral observation
        self.human = HumanObserver()
        
        # J = 0 (Classical), J = pi/2 (Quantum)
        j_factor = 0.0 if mode == "CLASSICAL" else np.pi/2
        self.agents = [QuantumAgent(i, j_factor) for i in range(20)]
        
        self.history = {
            "entropy": [], # Pool Size
            "eudaimonia": [], # Human Satisfaction
            "heat": []
        }
        
    def run_ewl_game(self, agent_a, agent_b):
        """Executes EWL Quantum Game Protocol"""
        # 1. Initial State |00>
        psi = np.kron(ket0, ket0)
        
        # 2. Entanglement Gate J (pi/2 for max entanglement)
        gamma = self.agents[0].J 
        J_gate = expm(1j * gamma * np.kron(X, X) / 2)
        psi = np.dot(J_gate, psi)
        
        # 3. Local Strategies U_A \otimes U_B
        U_A = agent_a.get_unitary()
        U_B = agent_b.get_unitary()
        UU = np.kron(U_A, U_B)
        psi = np.dot(UU, psi)
        
        # 4. Disentanglement J_dagger
        psi = np.dot(J_gate.conj().T, psi)
        
        # 5. Measurement
        probs = np.abs(psi)**2
        outcome = np.random.choice(4, p=probs)
        # 0->00(CC), 1->01(CD), 2->10(DC), 3->11(DD)
        
        if outcome == 0: return (3, 3) 
        if outcome == 1: return (0, 5) 
        if outcome == 2: return (5, 0) 
        if outcome == 3: return (1, 1) 
        return (0,0)

    def run_fast_loop(self):
        """Machine Speed Loop"""
        heat = self.pool.calculate_heat()
        dilation = 1.0 / (1.0 + heat)
        
        effective_ticks = int(FAST_TICKS_PER_SLOW * dilation)
        
        for _ in range(effective_ticks):
            a, b = random.sample(self.agents, 2)
            payoff_a, payoff_b = self.run_ewl_game(a, b)
            total_value = payoff_a + payoff_b
            
            # Generate Complexity from Agent state
            complexity_a = a.generate_complexity()
            complexity_b = b.generate_complexity()
            avg_complexity = (complexity_a + complexity_b) / 2
            
            # Add to pool (Validation happens inside add_task)
            # Use creator 'a' for feedback (simplification)
            self.pool.add_task(total_value, avg_complexity, a)

    def run_slow_loop(self):
        """Human Speed Loop"""
        self.pool.decay_and_cleanup()
        score, creator = self.human.observe_and_collapse(self.pool)
        
        # Metrics
        entropy = len(self.pool.tasks)
        self.history["entropy"].append(entropy)
        self.history["eudaimonia"].append(score)
        self.history["heat"].append(self.pool.heat)

    def step(self):
        self.run_fast_loop()
        self.run_slow_loop()


# --- Simulation Runner & Visualization ---
def run_scenario(mode):
    print(f"Starting Scenario V2: {mode}")
    econ = DualManifoldEconomy(mode)
    
    human_ticks = 400 # Increased ticks to see Strange Attractor dynamics
    
    for t in range(human_ticks):
        econ.step()
        if t % 50 == 0:
            avg_ent = np.mean(econ.history["entropy"][-20:]) if econ.history["entropy"] else 0
            avg_eud = np.mean(econ.history["eudaimonia"][-20:]) if econ.history["eudaimonia"] else 0
            print(f"  Tick {t}: Entropy={avg_ent:.1f}, Eudaimonia={avg_eud:.2f}, Heat={econ.pool.heat:.2f}")
            
    return econ

def plot_phase_portrait(econ):
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Plot Trajectory
    ax.plot(econ.history["entropy"], econ.history["eudaimonia"], 'b-', alpha=0.5, linewidth=1)
    
    # Mark start and end
    ax.plot(econ.history["entropy"][0], econ.history["eudaimonia"][0], 'go', label="Start")
    ax.plot(econ.history["entropy"][-1], econ.history["eudaimonia"][-1], 'ro', label="End")
    
    ax.set_title("V2 Quantum Phase Portrait: Strange Attractor")
    ax.set_xlabel("Entropy (Pool Size)")
    ax.set_ylabel("Eudaimonia (Human Value)")
    ax.grid(True)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('quantum_v2_strange_attractor.png')
    print("V2 Phase Portrait saved to quantum_v2_strange_attractor.png")

if __name__ == "__main__":
    # Only running Quantum V2 Mode as requested
    econ_v2 = run_scenario("QUANTUM")
    plot_phase_portrait(econ_v2)
