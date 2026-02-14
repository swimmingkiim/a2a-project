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
        # We simplify state space to just "Last Outcome" (0=Defect, 1=Cooperate/HighScore) for demo
        self.q_table = {} 
        self.last_action_params = None

    def get_unitary(self):
        """Returns Unitary Matrix U(theta, phi)"""
        # U(theta, phi) ~ Rotation on Bloch Sphere
        # U = [[e^(iphi) cos(theta/2), i sin(theta/2)], [i sin(theta/2), e^(-iphi) cos(theta/2)]]
        # Simplified 1-qubit gate for strategy selection
        th, ph = self.theta, self.phi
        u00 = np.exp(1j * ph) * np.cos(th / 2)
        u01 = 1j * np.sin(th / 2)
        u10 = 1j * np.sin(th / 2)
        u11 = np.exp(-1j * ph) * np.cos(th / 2)
        return np.array([[u00, u01], [u10, u11]], dtype=complex)

    def update_strategy(self, reward):
        """Cybernetic Feedback Loop: Update Theta/Phi based on Eudaimonic Score"""
        # Gradient ascent-like simple RL update
        # If reward is high, reinforce current direction. If low, perturb.
        
        # Simple Hill Climbing / Q-Learning Approximation
        step_size = LEARNING_RATE * (reward - 0.5) # + if good, - if bad
        
        # Perturb towards "Cooperation" (Theta=0) if reward is high? 
        # Actually, let's just use random perturbation scaled by inverse reward (Exploration)
        # If reward is high (1.0), noise is 0. If reward is low (0.0), noise is high.
        noise = (1.0 - reward) * 0.5
        
        self.theta += random.uniform(-noise, noise)
        self.phi += random.uniform(-noise, noise)
        
        # Clamp
        self.theta = np.clip(self.theta, 0, np.pi)
        self.phi = np.clip(self.phi, 0, 2*np.pi)


class SchrodingerPool:
    """
    Buffer Zone where tasks exist as Wave Functions.
    Subject to Entropy Decay and generates Heat.
    """
    def __init__(self):
        self.tasks = [] # List of {'value': float, 'age': int, 'creator': Agent}
        self.heat = 0.0

    def add_task(self, raw_value, creator):
        self.tasks.append({
            'initial_value': raw_value,
            'current_value': raw_value,
            'age': 0,
            'creator': creator
        })

    def decay(self):
        """Entropy Decay: Value decreases over time"""
        for task in self.tasks:
            task['age'] += 1
            # Value(t) = V0 * e^(-lambda * t)
            task['current_value'] *= (1.0 - DECAY_RATE)

    def calculate_heat(self):
        """Thermodynamic Throttling"""
        size = len(self.tasks)
        if size > CRITICAL_MASS:
            # Heat increases quadratically with excess size
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
    """
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def observe_and_collapse(self, pool):
        task = pool.get_observable_task()
        if not task: return 0.0, None

        # 1. Measure Properties
        val = task['current_value']
        age = task['age']
        
        # 2. Fuzzy Logic Valuation (Eudaimonia)
        # "Freshness" matters (low age). "Complexity" (initial value) matters.
        freshness = np.exp(-0.1 * age)
        quality = min(1.0, task['initial_value'] / 10.0) # Normalize
        
        # Non-linear "Magic" metric
        eudaimonia_score = (quality * 0.7) + (freshness * 0.3)
        
        # Random subjective factor ("Does this spark joy?")
        subjective_factor = random.uniform(0.8, 1.2)
        final_score = eudaimonia_score * subjective_factor
        
        # 3. Collapse
        pool.remove_task(task)
        
        # 4. Feedback Signal
        if task['creator']:
            task['creator'].update_strategy(final_score)
            
        return final_score, task['creator']


class DualManifoldEconomy:
    def __init__(self, mode="CLASSICAL"):
        self.mode = mode
        self.pool = SchrodingerPool()
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
        
        # 2. Entanglement Gate J
        # J = exp(i * gamma * D \otimes D / 2), where D = Z for simplicity in some EWL variants,
        # or typically J makes the state (|00> + i|11>) / sqrt(2) at max entanglement.
        # Strict EWL uses J = exp(i * gamma * X \otimes X / 2) usually for PD?
        # Let's use the standard "EWL" operator J = exp(i * gamma * SigmaX x SigmaX / 2)
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
        # Probabilities of basis states |00>, |01>, |10>, |11>
        probs = np.abs(psi)**2
        
        # Collapse to a state (CC, CD, DC, DD)
        outcome = np.random.choice(4, p=probs)
        # 0->00(CC), 1->01(CD), 2->10(DC), 3->11(DD)
        
        if outcome == 0: return (3, 3) # CC
        if outcome == 1: return (0, 5) # CD
        if outcome == 2: return (5, 0) # DC
        if outcome == 3: return (1, 1) # DD
        return (0,0)

    def run_fast_loop(self):
        """Machine Speed Loop"""
        # Calculate Time Dilation from Heat
        heat = self.pool.calculate_heat()
        dilation = 1.0 / (1.0 + heat)
        
        effective_ticks = int(FAST_TICKS_PER_SLOW * dilation)
        
        for _ in range(effective_ticks):
            # Random Pair
            a, b = random.sample(self.agents, 2)
            
            # Game
            payoff_a, payoff_b = self.run_ewl_game(a, b)
            
            # Value Creation (Sum of payoffs)
            # In Quantum/Cooperative mode -> 6 (3+3)
            # In Defect mode -> 2 (1+1)
            total_value = payoff_a + payoff_b
            
            # In Classical Mode: Instant Realization (No Pool, No Human)
            # But prompt asks to compare "Pool + Human" (Quantum) vs "Instant" (Classical)?
            # Prompt says: Scenario A (Classical): "Humans excluded, instant... entropy explosion"
            # Actually if instant, entropy is 0. 
            # Re-reading: "No human observation" -> Machines just pile up stuff?
            # Or Machines consume it themselves efficiently?
            # Let's interpret Scenario A as: Machines interact, but NO Eudaimonic Collapse mechanism exists to clear the buffer meaningfully,
            # or the Buffer just fills up with "junk" (low quality).
            
            if self.mode == "CLASSICAL":
                # Simulated "Instant Settlement" but low Eudaimonia
                # No pool accumulation, but also no Feedback Loop for Quality. 
                # Just raw output.
                # To match "Entropy Explosion" requirement: Maybe they produce junk that PILES up
                # and hits the limit?
                self.pool.add_task(total_value, None) # No creator tracking needed really
            else:
                # Quantum Mode: Add to Pool
                self.pool.add_task(total_value, a)

    def run_slow_loop(self):
        """Human Speed Loop"""
        # Decay
        self.pool.decay()
        
        # Collapse
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
    print(f"Starting Scenario: {mode}")
    econ = DualManifoldEconomy(mode)
    
    # Run
    # Simulation ticks is "Fast Ticks"? No, let's say Ticks = Slow Ticks (Human Seconds) 
    # to make it manageable, inside each is N fast ticks.
    human_ticks = 200 # Total human interactions
    
    for t in range(human_ticks):
        econ.step()
        if t % 20 == 0:
            avg_ent = np.mean(econ.history["entropy"][-20:]) if econ.history["entropy"] else 0
            print(f"  Tick {t}: Entropy={avg_ent:.1f}, Heat={econ.pool.heat:.2f}")
            
    return econ

def plot_phase_portraits(econ_classical, econ_quantum):
    fig, axs = plt.subplots(1, 2, figsize=(16, 6))
    
    # 1. Classical Phase Portrait
    axs[0].plot(econ_classical.history["entropy"], econ_classical.history["eudaimonia"], 'r-', alpha=0.6)
    axs[0].set_title("Scenario A: Classical (Fast Manifold Only)")
    axs[0].set_xlabel("Entropy (Pending Tasks)")
    axs[0].set_ylabel("Realized Eudaimonia")
    axs[0].grid(True)
    
    # 2. Quantum Phase Portrait
    axs[1].plot(econ_quantum.history["entropy"], econ_quantum.history["eudaimonia"], 'b-', alpha=0.6)
    axs[1].set_title("Scenario B: Quantum (Dual Manifold)")
    axs[1].set_xlabel("Entropy (Pending Tasks)")
    axs[1].set_ylabel("Realized Eudaimonia")
    axs[1].grid(True)
    
    plt.tight_layout()
    plt.savefig('quantum_phase_portrait.png')
    print("Phase Portrait saved to quantum_phase_portrait.png")

if __name__ == "__main__":
    # Scenario A: Classical (J=0, No Human Feedback effectively)
    econ_class = run_scenario("CLASSICAL")
    
    # Scenario B: Quantum (J=pi/2, Human Feedback Loop)
    econ_quant = run_scenario("QUANTUM")
    
    plot_phase_portraits(econ_class, econ_quant)
