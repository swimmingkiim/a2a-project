import random

class PIDController:
    def __init__(self, kp, ki, kd, target):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.target = target
        self.integral = 0
        self.prev_error = 0

    def update(self, current_value, dt=1):
        error = self.target - current_value
        
        # Integral Windup Guard
        self.integral += error * dt
        self.integral = max(-1000, min(1000, self.integral)) # Cap at 1000

        derivative = (error - self.prev_error) / dt
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.prev_error = error
        return output

class Economy:
    def __init__(self, initial_price):
        self.price = initial_price
        self.supply = 1_000_000 # Rough starting supply

    def apply_market_forces(self, volatility=2.0):
        # Random walk
        change = random.uniform(-volatility, volatility)
        self.price += change

    def apply_policy(self, burn_rate):
        # Simplified Model: Higher Burn Rate -> Reduced Supply -> Higher Price
        # If Burn Rate = 0.9 (90%), Supply decreases significantly.
        # We assume Demand is constant for simplicity in this isolated test.
        # Price ~ Demand / Supply. 
        # New Price = Old Price * (1 + (BurnEffect))
        
        # Effect Strength: Tunable parameter representing market depth
        # If burn_rate > 0.5 (Normal), price pressure is positive.
        # If burn_rate < 0.5 (Recycle), supply increases -> price pressure negative.
        
        pressure = (burn_rate - 0.1) * 0.05 # Max 5% impact per epoch
        self.price = self.price * (1 + pressure)

def run_simulation(kp, ki, kd, steps=100):
    pid = PIDController(kp, ki, kd, target=50.0)
    eco = Economy(initial_price=50.0)
    
    total_error = 0
    history = []

    print(f"--- Simulating PID (Kp={kp}, Ki={ki}, Kd={kd}) ---")
    
    # Trigger a crash at step 10
    for t in range(steps):
        if t == 10:
            eco.price = 25.0 # Flash Crash
            print(f"[Step {t}] !!! FLASH CRASH !!! Price: ${eco.price:.2f}")

        # 1. Market Move
        eco.apply_market_forces(volatility=0.5)

        # 2. PID Update
        raw_output = pid.update(eco.price)
        
        # 3. Clamp Output (0.1 to 0.9) - Matching Solidity Contract
        # PID Output is now directly added. 
        # Contract Logic: newBurnRate = base.add(output)
        rate = 0.5 + raw_output 
        rate = max(0.1, min(0.9, rate))

        # 4. Apply to Economy
        eco.apply_policy(rate)
        
        # 5. Track Error
        error = abs(50.0 - eco.price)
        total_error += error
        
        history.append((t, eco.price, rate))
        if t % 10 == 0 or t == steps - 1:
            print(f"Step {t}: Price=${eco.price:.2f} | BurnRate={rate:.2f} | Error={error:.2f}")

    avg_error = total_error / steps
    print(f"Result: Avg Error = {avg_error:.4f}\n")
    return avg_error

if __name__ == "__main__":
    # Grid Search for Parameters
    best_error = float('inf')
    best_params = (0, 0, 0)
    
    # Tuning Range (Simplified for speed)
    # Kp: Proportional (Immediate reaction)
    # Ki: Integral (Long term bias correction)
    # Kd: Derivative (Dampening future moves)
    
    # Initial Guess: Scaled down by 10x
    candidates = [
        (0.05, 0.001, 0.005), # Matches Contract (Sim Best * 0.1)
        (0.1, 0.005, 0.01),   # Slightly more aggressive
        (0.02, 0.0005, 0.002) # Conservative
    ]

    for kp, ki, kd in candidates:
        err = run_simulation(kp, ki, kd)
        if err < best_error:
            best_error = err
            best_params = (kp, ki, kd)

    print(f"✅ OPTIMAL PARAMETERS: Kp={best_params[0]}, Ki={best_params[1]}, Kd={best_params[2]}")
    print(f"Least Simulated Error: {best_error:.4f}")
