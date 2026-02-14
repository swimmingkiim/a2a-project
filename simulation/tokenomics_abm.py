import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random

# --- Configuration & Constants ---
INITIAL_SUPPLY = 50_000_000
INITIAL_FIAT_RESERVE = 1_000_000
INITIAL_TOKEN_RESERVE = 1_000_000
TARGET_CIRCULATING_SUPPLY = 30_000_000
TICKS = 10000
CRISIS_ONSET_TICK = 5000

# Quadratic Staking
STAKING_K = 0.0001

# PID Coefficients
KP = 0.5e-7
KI = 0.1e-8
KD = 0.1e-7

class PIDController:
    def __init__(self, kp, ki, kd, target):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.target = target
        self.prev_error = 0
        self.integral = 0

    def update(self, current_value, dt=1):
        error = current_value - self.target
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.prev_error = error
        return output

class LiquidityPool:
    def __init__(self, reserve_token, reserve_fiat):
        self.reserve_token = reserve_token
        self.reserve_fiat = reserve_fiat
        self.k = reserve_token * reserve_fiat

    def get_price(self):
        if self.reserve_token == 0: return float('inf')
        return self.reserve_fiat / self.reserve_token

    def swap_token_for_fiat(self, token_amount):
        if token_amount <= 0: return 0
        token_amount = min(token_amount, self.reserve_token * 0.5)
        new_reserve_token = self.reserve_token + token_amount
        new_reserve_fiat = self.k / new_reserve_token
        fiat_out = self.reserve_fiat - new_reserve_fiat
        self.reserve_token = new_reserve_token
        self.reserve_fiat = new_reserve_fiat
        return fiat_out

    def swap_fiat_for_token(self, fiat_amount):
        if fiat_amount <= 0: return 0
        fiat_amount = min(fiat_amount, self.reserve_fiat * 0.5)
        new_reserve_fiat = self.reserve_fiat + fiat_amount
        new_reserve_token = self.k / new_reserve_fiat
        token_out = self.reserve_token - new_reserve_token
        self.reserve_fiat = new_reserve_fiat
        self.reserve_token = new_reserve_token
        return token_out

class Economy:
    def __init__(self):
        self.total_supply = INITIAL_SUPPLY
        self.circulating_supply = INITIAL_SUPPLY
        self.staked_supply = 0
        self.burn_rate = 0.01
        
        # Macro Variables
        self.fiat_interest_rate = 0.04
        self.compute_cost_usd = 0.50
        self.fiat_inflow_multiplier = 1.0 # Budget scale
        self.network_uptime = 1.0 # Probability of SP being online
        self.spawn_rate = 1.0 # Probability multiplier for new agents
        
        self.amm = LiquidityPool(INITIAL_TOKEN_RESERVE, INITIAL_FIAT_RESERVE)
        self.pid = PIDController(KP, KI, KD, TARGET_CIRCULATING_SUPPLY)
        
        self.history = {
            "total_supply": [],
            "circulating_supply": [],
            "burn_rate": [],
            "token_price": [],
            "gini": [],
            "active_providers": []
        }

    def update_metrics(self, agents):
        self.staked_supply = sum(a.staked_amount for a in agents)
        self.circulating_supply = self.total_supply - self.staked_supply
        
        pid_output = self.pid.update(self.circulating_supply)
        # Fix: Max Burn Rate increased to 0.9
        self.burn_rate = max(0.001, min(0.9, 0.01 + pid_output))
        
        price = self.amm.get_price()
        
        wealths = [a.get_total_wealth(price) for a in agents]
        gini = self.calculate_gini(wealths)
        
        active_providers = sum(1 for a in agents if isinstance(a, ServiceProvider) and a.active)

        self.history["total_supply"].append(self.total_supply)
        self.history["circulating_supply"].append(self.circulating_supply)
        self.history["burn_rate"].append(self.burn_rate)
        self.history["token_price"].append(price)
        self.history["gini"].append(gini)
        self.history["active_providers"].append(active_providers)

    def calculate_staking_cost(self, amount):
        return STAKING_K * (amount ** 2)

    def handle_staking_penalty(self, penalty_amount):
        self.total_supply -= penalty_amount

    def burn_tokens(self, amount):
        self.total_supply -= amount

    def calculate_gini(self, wealths):
        if not wealths or sum(wealths) == 0: return 0
        sorted_wealths = sorted(wealths)
        n = len(wealths)
        cum_wealth = np.cumsum(sorted_wealths)
        return (n + 1 - 2 * np.sum(cum_wealth) / cum_wealth[-1]) / n

    def get_staking_yield(self):
        base_yield = 0.05 
        activity_bonus = self.burn_rate * 0.5
        return base_yield + activity_bonus

    # --- Crisis Generators ---
    def trigger_war_crisis(self):
        print("!!! CRISIS START: WAR & SUPPLY CHAIN COLLAPSE !!!")
        self.compute_cost_usd *= 4.0 # 300% increase
        self.fiat_interest_rate = 0.20 # Flight to safety
        self.fiat_inflow_multiplier = 0.3 # 70% reduction

    def trigger_drought_crisis(self):
        print("!!! CRISIS START: DROUGHT & POWER SHORTAGE !!!")
        self.compute_cost_usd *= 2.5 # 150% increase
        self.network_uptime = 0.8 # 20% downtime

    def trigger_export_ban_crisis(self):
        print("!!! CRISIS START: EXPORT BAN !!!")
        self.spawn_rate = 0 # No new agents

    def trigger_political_crisis(self, agents):
        print("!!! CRISIS START: POLITICAL IMPEACHMENT !!!")
        # Increase panic probability for Speculators
        for agent in agents:
            if isinstance(agent, Speculator):
                agent.panic_prob_multiplier = 50

class Agent:
    def __init__(self, unique_id, initial_token, initial_fiat):
        self.id = unique_id
        self.balance_token = initial_token
        self.balance_fiat = initial_fiat
        self.staked_amount = 0

    def get_total_wealth(self, token_price):
        return self.balance_fiat + (self.balance_token + self.staked_amount) * token_price

    def step(self, economy, agents):
        pass

class ServiceProvider(Agent):
    def __init__(self, unique_id, initial_token, initial_fiat):
        super().__init__(unique_id, initial_token, initial_fiat)
        self.active = True
        self.unprofitable_ticks = 0

    def step(self, economy, agents):
        # Drought check: Network Uptime
        if random.random() > economy.network_uptime:
            return # Offline due to power outage

        if not self.active:
            price = economy.amm.get_price()
            if (10 * price) > economy.compute_cost_usd * 2: 
                self.active = True
            return

        # 1. Profitability Check
        earning_potential_tokens = random.uniform(10, 100)
        current_price = economy.amm.get_price()
        revenue_usd = earning_potential_tokens * current_price
        
        work_units = earning_potential_tokens / 10
        cost_usd = work_units * economy.compute_cost_usd
        
        profit_usd = revenue_usd - cost_usd
        
        if profit_usd < 0:
            self.unprofitable_ticks += 1
            if self.unprofitable_ticks > 10: 
                self.active = False
                self.unstake_all(economy)
                return
        else:
            self.unprofitable_ticks = 0

        self.balance_token += earning_potential_tokens
        economy.total_supply += earning_potential_tokens
        self.balance_fiat -= cost_usd

        if self.balance_fiat < 0:
            debt = abs(self.balance_fiat)
            tokens_needed = debt / current_price * 1.1
            fiat_raised = economy.amm.swap_token_for_fiat(min(self.balance_token, tokens_needed))
            self.balance_fiat += fiat_raised
            
            if self.balance_fiat < 0:
                self.active = False
                self.unstake_all(economy)
                return

        # 2. Stake Strategy
        desired_stake = self.balance_token * 0.5 
        cost = economy.calculate_staking_cost(desired_stake)
        
        if self.balance_token > (desired_stake + cost):
            self.balance_token -= (desired_stake + cost)
            self.staked_amount += desired_stake
            economy.handle_staking_penalty(cost)
        
        # 3. Operations Selling
        if self.balance_fiat < 500:
            sell_amt = self.balance_token * 0.2
            fiat_gained = economy.amm.swap_token_for_fiat(sell_amt)
            self.balance_token -= sell_amt
            self.balance_fiat += fiat_gained

    def unstake_all(self, economy):
        if self.staked_amount > 0:
            self.balance_token += self.staked_amount
            self.staked_amount = 0

class Consumer(Agent):
    def step(self, economy, agents):
        # 1. Income (External Fiat Inflow) taking into account Crisis Multiplier
        income = random.uniform(100, 500) * economy.fiat_inflow_multiplier
        self.balance_fiat += income
        
        # 2. Buy Tokens (Price Sensitive & Strict Budget)
        price = economy.amm.get_price()
        
        # Fix: Strict Budget - estimate service cost
        estimated_service_cost_tokens = 10 # approximate cost for a service
        estimated_cost_fiat = estimated_service_cost_tokens * price
        
        if estimated_cost_fiat > self.balance_fiat:
             # Too expensive, buy nothing
             return
             
        base_budget = self.balance_fiat * 0.5
        if price > 20: base_budget *= 0.5
        if price > 50: base_budget *= 0.1
            
        tokens_bought = economy.amm.swap_fiat_for_token(base_budget)
        self.balance_fiat -= base_budget
        self.balance_token += tokens_bought
        
        # 3. Consume
        sp_agents = [a for a in agents if isinstance(a, ServiceProvider) and a.active]
        if sp_agents and self.balance_token > 0:
            spend_amount = self.balance_token * 0.8
            burn_amt = spend_amount * economy.burn_rate
            pay_amt = spend_amount - burn_amt
            
            economy.burn_tokens(burn_amt)
            
            recipient = random.choice(sp_agents)
            recipient.balance_token += pay_amt
            self.balance_token -= spend_amount

class Speculator(Agent):
    def __init__(self, unique_id, initial_token, initial_fiat):
        super().__init__(unique_id, initial_token, initial_fiat)
        self.panic_prob_multiplier = 1.0

    def step(self, economy, agents):
        current_price = economy.amm.get_price()
        if not hasattr(self, 'last_price'): self.last_price = current_price
        price_change = (current_price - self.last_price) / self.last_price if self.last_price else 0
        self.last_price = current_price
        
        # Political Crisis Logic: Panic Sell Probability
        base_panic_prob = 0.001
        if random.random() < (base_panic_prob * self.panic_prob_multiplier):
            self.panic_dump(economy)
            return

        staking_yield = economy.get_staking_yield()
        risk_free_rate = economy.fiat_interest_rate
        
        if risk_free_rate > (staking_yield + 0.02):
            self.capital_flight(economy)
            return

        if price_change > 0.05:
            buy_amt = self.balance_fiat * 0.5
            tokens = economy.amm.swap_fiat_for_token(buy_amt)
            self.balance_fiat -= buy_amt
            self.balance_token += tokens
            
        elif price_change < -0.05:
            sell_amt = self.balance_token * 0.5
            fiat = economy.amm.swap_token_for_fiat(sell_amt)
            self.balance_token -= sell_amt
            self.balance_fiat += fiat

    def capital_flight(self, economy):
        if self.staked_amount > 0:
            self.balance_token += self.staked_amount
            self.staked_amount = 0
        
        if self.balance_token > 0:
            fiat = economy.amm.swap_token_for_fiat(self.balance_token)
            self.balance_token = 0
            self.balance_fiat += fiat

    def panic_dump(self, economy):
        self.capital_flight(economy)


# --- Simulation Runner ---
def run_scenario(scenario_name, generator_func):
    economy = Economy()
    agents = []
    
    for i in range(20): agents.append(ServiceProvider(i, 2000, 2000))
    for i in range(50): agents.append(Consumer(20+i, 100, 1000))
    for i in range(10): agents.append(Speculator(70+i, 5000, 5000))
    
    print(f"--- Running Scenario: {scenario_name} ---")
    
    for tick in range(TICKS):
        random.shuffle(agents)
        
        # Spawn Logic (Export Ban check)
        if economy.spawn_rate > 0 and random.random() < (0.005 * economy.spawn_rate):
             # Small chance of new ServiceProvider entering
             agents.append(ServiceProvider(1000+tick, 1000, 1000))

        for agent in agents:
            agent.step(economy, agents)
            
        economy.update_metrics(agents)
        
        if tick == CRISIS_ONSET_TICK:
            generator_func(economy, agents)
            
    print(f"Scenario {scenario_name} Complete.\n")
    return economy

# --- Visualization ---
def plot_scenario(economy, scenario_name, ax_row):
    df = pd.DataFrame(economy.history)
    
    # Supply
    ax_row[0].plot(df['total_supply'], label='Total')
    ax_row[0].plot(df['circulating_supply'], label='Circulating', linestyle='--')
    ax_row[0].axvline(x=CRISIS_ONSET_TICK, color='r', linestyle=':')
    ax_row[0].set_title(f'{scenario_name}: Supply')
    
    # Price
    ax_row[1].plot(df['token_price'], color='green')
    ax_row[1].axvline(x=CRISIS_ONSET_TICK, color='r', linestyle=':')
    ax_row[1].set_title(f'{scenario_name}: Price')
    
    # Active Providers
    ax_row[2].plot(df['active_providers'], color='blue')
    ax_row[2].axvline(x=CRISIS_ONSET_TICK, color='r', linestyle=':')
    ax_row[2].set_title(f'{scenario_name}: Active SPs')
    ax_row[2].set_ylim(bottom=0)

# --- Main Driver ---
if __name__ == "__main__":
    
    # Wrapper lambdas for scenarios
    def war_wrapper(econ, agents): econ.trigger_war_crisis()
    def drought_wrapper(econ, agents): econ.trigger_drought_crisis()
    def export_wrapper(econ, agents): econ.trigger_export_ban_crisis()
    def politics_wrapper(econ, agents): econ.trigger_political_crisis(agents)

    scenarios = [
        ("C A: WAR", war_wrapper),
        ("C B: DROUGHT", drought_wrapper),
        ("C C: EXPORT BAN", export_wrapper),
        ("C D: POLITICAL", politics_wrapper)
    ]
    
    # 4 Scenarios, 3 Plots each -> 4 rows, 3 cols
    fig, axs = plt.subplots(4, 3, figsize=(15, 20))
    plt.subplots_adjust(hspace=0.4)
    
    for i, (name, func) in enumerate(scenarios):
        econ = run_scenario(name, func)
        plot_scenario(econ, name, axs[i])
        
        # Analysis Print
        final_sps = sum(1 for a in econ.history["active_providers"][-100:] if a > 0) / 100 # avg last 100 ticks
        print(f"[{name}] Final Active SPs (approx): {final_sps:.1f}")
        
    plt.tight_layout()
    plt.savefig('crisis_simulation_results.png')
    print("All simulations complete. Results saved to crisis_simulation_results.png")
