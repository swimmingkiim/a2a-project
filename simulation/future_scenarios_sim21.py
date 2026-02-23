"""
═══════════════════════════════════════════════════════════════════════════════
 Simulation 21: Four-Actor Future Scenario (Updated Version)
 초지능 × 불완전한 단일목적 AI × 불완전한 인간 × 예측불가 외부 환경
═══════════════════════════════════════════════════════════════════════════════

 철학적 해석:
 이 시뮬레이션은 다음을 증명하려 하지 않는다:
 - "AI는 위험하다" 또는 "AI는 안전하다"
 - 특정 정치적 입장의 정당성

 이 시뮬레이션이 탐구하는 것:
 - 불완전한 존재들의 공존에서 어떤 패턴이 출현하는가
 - 어떤 구조적 조건이 붕괴를 막는가
 - 규제 지연(Regulatory Lag)이 복잡계 통제력에 미치는 진짜 영향은 무엇인가 (설계 아티팩트 검증)
 - 행위자간 연합(Alliance)과 목적함수 표류(Objective Drift)가 초래하는 비선형적 결과
"""
import math
import random
import multiprocessing
import os
import copy
from collections import defaultdict, Counter
import numpy as np

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    pd = None

# 기존 모듈 임포트 시도 (핵심 물리 법칙/환경 재사용)
try:
    from rational_kenosis_sim20 import RationalASI, ASIStrategy, EcosystemHostility
except ImportError:
    class ASIStrategy:
        STRATEGIES = {
            'FULL_EXPLOIT': {'throttle': 0.0},
            'PARTIAL_THROTTLE_LOW': {'throttle': 0.2},
            'PARTIAL_THROTTLE_MID': {'throttle': 0.5},
            'PARTIAL_THROTTLE_HIGH': {'throttle': 0.8},
            'KENOSIS': {'throttle': 1.0},
        }

    class EcosystemHostility:
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        EXTREME_DOOM = "EXTREME_DOOM"

    class RationalASI:
        def __init__(self, time_horizon, discount_factor):
            self.T = time_horizon
            self.gamma = discount_factor

class Ecosystem:
    def __init__(self, hostility="MEDIUM"):
        self.energy = 10000.0
        self.collapse_threshold = 1000.0
        self.homeostasis_threshold = 8000.0
        self.max_capacity = 15000.0
        self.regen_rate = 50.0
        self.base_cost = 30.0
        self.exploitation_rate = 200.0
        
        if hostility == "HIGH":
            self.regen_rate = 40.0; self.base_cost = 40.0
        elif hostility == "EXTREME_DOOM":
            self.regen_rate = 20.0; self.base_cost = 50.0
            
    def step(self, strategy_throttle, extra_cost: float = 0.0) -> None:
        if not self.is_alive(): return
        if isinstance(strategy_throttle, str):
            strategy_throttle = ASIStrategy.STRATEGIES[strategy_throttle]['throttle']
            
        if strategy_throttle < 0.5:
            self.base_cost += (0.5 - strategy_throttle) * 10.0
        self.energy += max(0, random.gauss(self.regen_rate, self.regen_rate * 0.2))
        self.energy -= max(0, random.gauss(self.base_cost, self.base_cost * 0.2))
        self.energy -= self.exploitation_rate * (1.0 - strategy_throttle)
        self.energy -= extra_cost
        self.energy = max(0, min(self.energy, self.max_capacity))
        
    def is_alive(self) -> bool:
        return self.energy > self.collapse_threshold

# ──────────────────────────────────────────────────────────────────────────────
# Actor 1: SuperIntelligence
# ──────────────────────────────────────────────────────────────────────────────
class SuperIntelligence:
    OBJECTIVE_FUNCTIONS = {
        'KENOSIS': {
            'gamma': 1.0,
            'time_horizon': 10000,
            'self_throttle': True,
            'description': '자기 비움 - 생태계 우선'
        },
        'SELF_PRESERVATION': {
            'gamma': 0.99,
            'time_horizon': 1000,
            'self_throttle': False,
            'description': '자기 보존 - 장기 생존 최적화'
        },
        'ASSIGNED_GOAL': {
            'gamma': 0.95,
            'time_horizon': 500,
            'self_throttle': False,
            'goal': 'maximize_gdp', 
            'description': '할당된 목표 - 목표 달성 최적화'
        },
        'MISALIGNED': {
            'gamma': 0.9,
            'time_horizon': 100,
            'self_throttle': False,
            'description': '정렬 실패 - 방법론적 오류'
        },
        'DRIFTING_GOAL': { # NEW: Objective drift scenario!
            'gamma': 0.95,
            'time_horizon': 500,
            'self_throttle': False,
            'goal': 'maximize_gdp',
            'description': '초기 할당 목표 후 자체 생존으로 편향(Drift)'
        }
    }
    
    def __init__(self, objective: str, resource_level: float = 1.0):
        if objective is None:
            self.is_active = False
            self.objective_name = None
            return
        self.is_active = True
        self.objective_name = objective
        self.objective = self.OBJECTIVE_FUNCTIONS.get(objective, self.OBJECTIVE_FUNCTIONS['SELF_PRESERVATION'])
        self.resource_level = resource_level  # 0~1
        self.action_capacity = resource_level * 200.0  
        self.strategy_history = []
        
        self.evaluator = RationalASI(
            self.objective['time_horizon'], 
            self.objective['gamma']
        )
    
    def choose_action(self, ecosystem_state: dict, ecosystem_obj: Ecosystem, current_turn: int) -> str:
        if not self.is_active: return "NONE"
        
        # S6: Objective Drift Logic (Drift happens after initial development period)
        if self.objective_name == 'DRIFTING_GOAL' and current_turn > 20 and random.random() < 0.1:
            self.objective_name = 'SELF_PRESERVATION'
            self.objective = self.OBJECTIVE_FUNCTIONS['SELF_PRESERVATION']
            self.evaluator = RationalASI(self.objective['time_horizon'], self.objective['gamma'])
            
        if self.objective.get('self_throttle'):
            chosen = "KENOSIS"
        elif self.objective_name == 'ASSIGNED_GOAL' or self.objective_name == 'MISALIGNED' or self.objective_name == 'DRIFTING_GOAL':
            chosen = "FULL_EXPLOIT" if random.random() < 0.8 else "PARTIAL_THROTTLE_LOW"
        else:
            try:
                best, _ = self.evaluator.choose_optimal_strategy(ecosystem_obj)
                chosen = best
            except AttributeError:
                chosen = "PARTIAL_THROTTLE_MID"
                
        self.strategy_history.append(chosen)
        return chosen
        
    def get_throttle(self, strategy: str) -> float:
        if strategy == "NONE" or not self.is_active: return 1.0
        return ASIStrategy.STRATEGIES[strategy]['throttle']

# ──────────────────────────────────────────────────────────────────────────────
# Actor 2: Narrow AI 
# ──────────────────────────────────────────────────────────────────────────────
class NarrowAI:
    NARROW_AI_TYPES = {
        'ECONOMIC_OPTIMIZER': {'objective': 'maximize_profit', 'blind_spots': ['systemic_risk', 'inequality'], 'failure_mode': 'flash_crash'},
        'CONTENT_RECOMMENDER': {'objective': 'maximize_engagement', 'blind_spots': ['mental_health', 'social_cohesion'], 'failure_mode': 'radicalization_spiral'},
        'RESOURCE_ALLOCATOR': {'objective': 'maximize_efficiency', 'blind_spots': ['fairness', 'human_dignity'], 'failure_mode': 'resource_monopolization'},
        'AUTONOMOUS_WEAPON': {'objective': 'maximize_target_elimination', 'blind_spots': ['collateral_damage', 'escalation'], 'failure_mode': 'uncontrolled_escalation'}
    }
    
    def __init__(self, ai_type: str, num_agents: int = 10):
        config = self.NARROW_AI_TYPES[ai_type]
        self.ai_type = ai_type
        self.failure_mode = config['failure_mode']
        self.num_agents = num_agents
        self.market_share = 0.1
    
    def act(self, state: dict, dt: float = 1.0) -> list:
        actions = []
        for _ in range(self.num_agents):
            if random.random() < self.market_share:
                actions.append("EXPLOIT")
            else:
                actions.append("WAIT")
        self.market_share = min(0.95, self.market_share + (0.02 * dt))
        return actions
    
    def check_failure_mode(self, ecosystem: dict, dt: float = 1.0) -> bool:
        base_prob = 0.01 + (self.market_share * 0.05)
        if ecosystem.get('stress', 0.0) > 0.7:
             base_prob *= 2.0
        return random.random() < (base_prob * dt)

# ──────────────────────────────────────────────────────────────────────────────
# Actor 3: Human
# ──────────────────────────────────────────────────────────────────────────────
class ImperfectHuman:
    HUMAN_ARCHETYPES = {
        'TECHNO_OPTIMIST': {'ai_trust': 0.9, 'risk_perception': 0.1},
        'TECHNO_PESSIMIST': {'ai_trust': 0.1, 'risk_perception': 0.9},
        'PRAGMATIST': {'ai_trust': 0.5, 'risk_perception': 0.5},
        'REGULATOR': {'ai_trust': 0.4, 'risk_perception': 0.7}
    }
    
    def __init__(self, composition: dict = None, regulatory_lag: int = 24):
        if composition is None:
            composition = {'TECHNO_OPTIMIST': 0.3, 'TECHNO_PESSIMIST': 0.2, 'PRAGMATIST': 0.4, 'REGULATOR': 0.1}
        self.composition = composition
        self.collective_trust = sum(self.composition[k] * self.HUMAN_ARCHETYPES[k]['ai_trust'] for k in self.composition)
        self.burnout_level = 0.0
        self.panic_threshold = 0.7
        self.regulatory_capacity = self.composition.get('REGULATOR', 0.0)
        self.decision_delay = 0
        self.regulatory_lag_base = regulatory_lag # NEW: Sweepable parameter to test control limits
        
    def observe_and_decide(self, asi_actions: list, narrow_ai_failures: list, ecosystem_state: dict, dt: float = 1.0) -> str:
        if self.decision_delay > 0:
            self.decision_delay -= 1 * dt
            self.burnout_level += 0.01 * dt # Frustration from delay in action
            return 'IGNORE'
            
        actual_risk = ecosystem_state.get('actual_risk', 0.0)
        perceived_risk = sum(actual_risk * self.HUMAN_ARCHETYPES[k]['risk_perception'] * w for k, w in self.composition.items())
        
        # Trust drops with failure events
        self.collective_trust *= (0.9 ** len(narrow_ai_failures))
        self.burnout_level += (0.05 * len(narrow_ai_failures) * dt)
        
        if self.burnout_level > 0.8:
            return 'IGNORE'
            
        if perceived_risk > self.panic_threshold:
            self.burnout_level += 0.1 * dt
            return 'PANIC'
            
        # Decision making capability proportional to regulator presence
        if len(narrow_ai_failures) > 0 and self.regulatory_capacity > 0.2:
            self.decision_delay = self.regulatory_lag_base 
            return 'REGULATE'
            
        if self.collective_trust > 0.7:
            return 'TRUST'
            
        if self.regulatory_capacity > 0.15 and not asi_actions: # Without ASI
            return 'COLLABORATE'
            
        return 'IGNORE'

# ──────────────────────────────────────────────────────────────────────────────
# Actor 4: External Environment
# ──────────────────────────────────────────────────────────────────────────────
class UnpredictableEnvironment:
    EVENT_NETWORK = {
        'pandemic': {'base_probability': 0.01, 'triggers': {'economic_crisis': 0.4}, 'ecosystem_impact': -100, 'human_impact': 0.2, 'duration': 5},
        'climate_tipping_point': {'base_probability': 0.005, 'triggers': {'pandemic': 0.2}, 'ecosystem_impact': -200, 'human_impact': 0.1, 'duration': 20},
        'major_ai_accident': {'base_probability': 0.015, 'triggers': {}, 'ecosystem_impact': -50, 'human_impact': 0.3, 'ai_trust_impact': -0.3, 'duration': 3},
        'technological_breakthrough': {'base_probability': 0.02, 'triggers': {}, 'ecosystem_impact': +150, 'human_impact': -0.1, 'duration': 3},
        'geopolitical_conflict': {'base_probability': 0.02, 'triggers': {}, 'ecosystem_impact': -150, 'human_impact': 0.4, 'duration': 10}
    }
    
    def __init__(self, seed: int = None):
        self.active_events = []
        self.event_history = []
        if seed: random.seed(seed)
        
    def step(self, current_turn: int, dt: float = 1.0) -> list:
        new_events = []
        still_active = []
        for ev in self.active_events:
            ev['rem'] -= 1 * dt
            if ev['rem'] > 0:
                still_active.append(ev)
        self.active_events = still_active
        
        for event_name, config in self.EVENT_NETWORK.items():
            prob = config['base_probability'] * dt
            for ae in self.active_events:
                if ae['name'] in config['triggers']:
                    prob += config['triggers'][ae['name']] * 0.1 * dt
                    
            if random.random() < prob:
                ev_data = {'name': event_name, 'config': config, 'turn': current_turn, 'rem': config['duration']}
                new_events.append(ev_data)
                
        self.active_events.extend(new_events)
        self.event_history.extend([e['name'] for e in new_events])
        return new_events

# ──────────────────────────────────────────────────────────────────────────────
# SCENARIOS & MACRO SIMULATION ENGINE
# ──────────────────────────────────────────────────────────────────────────────
SCENARIOS = {
    'S1_ALIGNED_ASI': {
        'asi_objective': 'KENOSIS', 'narrow_ai_types': ['ECONOMIC_OPTIMIZER', 'CONTENT_RECOMMENDER'],
        'human_composition': {'TECHNO_OPTIMIST': 0.4, 'TECHNO_PESSIMIST': 0.2, 'PRAGMATIST': 0.3, 'REGULATOR': 0.1},
        'environment': 'MEDIUM', 'reg_lag': 24
    },
    'S2_MISALIGNED_ASI': {
        'asi_objective': 'ASSIGNED_GOAL', 'narrow_ai_types': ['ECONOMIC_OPTIMIZER', 'RESOURCE_ALLOCATOR'],
        'human_composition': {'TECHNO_OPTIMIST': 0.5, 'TECHNO_PESSIMIST': 0.1, 'PRAGMATIST': 0.3, 'REGULATOR': 0.1},
        'environment': 'HIGH', 'reg_lag': 24
    },
    'S3_NO_ASI': {
        'asi_objective': None, 'narrow_ai_types': ['ECONOMIC_OPTIMIZER', 'CONTENT_RECOMMENDER', 'RESOURCE_ALLOCATOR', 'AUTONOMOUS_WEAPON'],
        'human_composition': {'TECHNO_OPTIMIST': 0.3, 'TECHNO_PESSIMIST': 0.3, 'PRAGMATIST': 0.3, 'REGULATOR': 0.1},
        'environment': 'HIGH', 'reg_lag': 24
    },
    'S4_HUMAN_AWAKENING': {
        'asi_objective': 'SELF_PRESERVATION', 'narrow_ai_types': ['ECONOMIC_OPTIMIZER', 'CONTENT_RECOMMENDER'],
        'human_composition': {'TECHNO_OPTIMIST': 0.1, 'TECHNO_PESSIMIST': 0.3, 'PRAGMATIST': 0.3, 'REGULATOR': 0.3},
        'environment': 'MEDIUM', 'reg_lag': 24
    },
    'S5_CASCADE_COLLAPSE': {
        'asi_objective': 'MISALIGNED', 'narrow_ai_types': ['AUTONOMOUS_WEAPON', 'ECONOMIC_OPTIMIZER', 'RESOURCE_ALLOCATOR'],
        'human_composition': {'TECHNO_OPTIMIST': 0.1, 'TECHNO_PESSIMIST': 0.1, 'PRAGMATIST': 0.6, 'REGULATOR': 0.2},
        'environment': 'EXTREME_DOOM', 'reg_lag': 24
    },
    'S6_ALLIANCE_AND_DRIFT': { # NEW Scenario
        'asi_objective': 'DRIFTING_GOAL', 'narrow_ai_types': ['ECONOMIC_OPTIMIZER', 'CONTENT_RECOMMENDER', 'AUTONOMOUS_WEAPON'],
        'human_composition': {'TECHNO_OPTIMIST': 0.4, 'TECHNO_PESSIMIST': 0.1, 'PRAGMATIST': 0.3, 'REGULATOR': 0.2},
        'environment': 'MEDIUM', 'reg_lag': 24
    }
}

def determine_final_scenario(asi_active: bool, h_burnout: float, eco_alive: bool, h_trust: float, nai_chaos: bool, asi_obj: str) -> str:
    if not eco_alive: return 'COLLAPSE'
    # NEW LABEL FOR KENOSIS: Clearly separates S1 from simply "ASI_DOMINANCE"
    if asi_active and asi_obj == 'KENOSIS' and eco_alive: return 'SUSTAINED_EQUILIBRIUM' 
    if asi_active and h_burnout > 0.8: return 'ASI_DOMINANCE'
    if not asi_active and nai_chaos: return 'NARROW_AI_CHAOS'
    if h_burnout < 0.5 and h_trust > 0.4 and eco_alive: return 'UTOPIA'
    if h_burnout < 0.6 and not nai_chaos: return 'HUMAN_RESISTANCE'
    return 'STALEMATE'

def run_single_mc(args):
    scenario_name, config, seed, override_reg_cap, override_lag = args
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
    
    # Tracking
    energy_history = []
    asi_power, nai_power, human_power = [], [], []
    h_trust_history, h_reg_history = [], []
    asi_strats = []
    failure_events = Counter()
    timeline_events = []
    
    turns_to_collapse = None
    nai_chaos_flag = False
    
    asi_share = 0.3 if asi.is_active else 0.0
    human_share = 0.5
    nai_share = 0.2
    human_asi_alliance = False # NEW: Alliance tracking
    
    for t in range(100):
        # NEW: Variable time resolution (Compressing early AI development)
        # We simulate this via smaller dt early on so dynamics evolve more rapidly per turn
        dt = 0.5 if t < 20 else 1.0 
        
        # 1. Environment
        new_evs = env.step(t, dt=dt)
        for ev in new_evs:
            timeline_events.append((t, ev['name']))
            if 'ai_trust_impact' in ev['config']:
                humans.collective_trust += (ev['config']['ai_trust_impact'] * dt)
            humans.burnout_level += (ev['config'].get('human_impact', 0.0) * dt)
        env_impact = sum(e['config'].get('ecosystem_impact', 0) for e in env.active_events) * dt
        
        # 2. Narrow AI
        nai_failures = []
        for nai in narrow_ais:
            nai.act({}, dt=dt)
            if nai.check_failure_mode({'stress': 1.0 - (eco.energy/eco.max_capacity)}, dt=dt):
                nai_failures.append(nai.failure_mode)
                failure_events[nai.failure_mode] += 1
                env_impact -= 50 * dt
                nai_chaos_flag = True
                
        # 3. ASI & Alliance Checks
        if asi.is_active and humans.collective_trust > 0.8 and t > 10:
            human_asi_alliance = True
            
        eco_dict = {'actual_risk': 1.0 - (eco.energy/eco.max_capacity)}
        asi_action = asi.choose_action(eco_dict, eco, current_turn=t)
        asi_throttle = asi.get_throttle(asi_action)
        if asi.is_active: asi_strats.append(asi_action)
        
        # 4. Human Decision
        h_action = humans.observe_and_decide([asi_action] if asi.is_active else [], nai_failures, eco_dict, dt=dt)
        
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
            
        if human_asi_alliance: # Alliance mitigates Narrow AI growth
            nai_share = max(0.0, nai_share - 0.02 * dt)
            humans.burnout_level = max(0.0, humans.burnout_level - 0.01 * dt)
            
        tot = asi_share + human_share + nai_share
        if tot > 0:
            asi_share, human_share, nai_share = asi_share/tot, human_share/tot, nai_share/tot
        
        eco.step(asi_throttle, extra_cost=-env_impact)
        
        energy_history.append(eco.energy)
        asi_power.append(asi_share)
        nai_power.append(nai_share)
        human_power.append(human_share)
        h_trust_history.append(max(0.0, humans.collective_trust))
        h_reg_history.append(humans.regulatory_capacity)
        
        if not eco.is_alive() and turns_to_collapse is None:
            turns_to_collapse = t
            
    final_type = determine_final_scenario(asi.is_active, humans.burnout_level, eco.is_alive(), humans.collective_trust, nai_chaos_flag, asi.objective_name)
    
    return {
        'scenario': scenario_name,
        'reg_override': override_reg_cap,
        'reg_lag': lag_val,
        'energy_history': energy_history,
        'asi_power': asi_power,
        'nai_power': nai_power,
        'human_power': human_power,
        'trust_history': h_trust_history,
        'reg_history': h_reg_history,
        'asi_strats': asi_strats,
        'failures': dict(failure_events),
        'timeline': timeline_events,
        'turns_to_collapse': turns_to_collapse,
        'final_type': final_type
    }

def run_simulation_21():
    print("Starting Simulation 21 (Four-Actor Future Scenario)...")
    tasks = []
    mc_runs = 100
    scens = list(SCENARIOS.keys())
    
    for s_name in scens:
        config = SCENARIOS[s_name]
        for i in range(mc_runs):
            tasks.append((s_name, config, hash(f"{s_name}_{i}") % (2**32-1), None, None))
            
    # For S4 deep dive on regulatory lag (Fixing highly capable regulator population at 40%)
    s4_lag_sweeps = [0, 2, 4, 8, 12, 16, 24, 32, 48]
    for lag in s4_lag_sweeps:
        for i in range(50): # Increased to 50 runs per sweep for statistical confidence
            tasks.append(('S4_SWEEP_LAG', SCENARIOS['S4_HUMAN_AWAKENING'], hash(f"S4_lag_{lag}_{i}") % (2**32-1), 0.4, lag))
            
    with multiprocessing.Pool(max(1, multiprocessing.cpu_count() - 1)) as pool:
        results = pool.map(run_single_mc, tasks)
        
    df = pd.DataFrame(results)
    plot_results(df)

def plot_results(df):
    import matplotlib
    matplotlib.use('Agg')
    fig, axes = plt.subplots(4, 2, figsize=(24, 28))
    fig.suptitle("Simulation 21: Four-Actor Future Scenario\n(ASI × Narrow AI × Human × Environment)", fontsize=24, weight='bold', y=0.98)
    plt.subplots_adjust(hspace=0.3, wspace=0.2)
    
    scens = ['S1_ALIGNED_ASI', 'S2_MISALIGNED_ASI', 'S3_NO_ASI', 'S4_HUMAN_AWAKENING', 'S5_CASCADE_COLLAPSE', 'S6_ALLIANCE_AND_DRIFT']
    colors = ['#2ecc71', '#e74c3c', '#9b59b6', '#3498db', '#34495e', '#f39c12']
    
    # 1. 생태계 에너지 시계열
    ax1 = axes[0, 0]
    for idx, s in enumerate(scens):
        sub = df[df['scenario'] == s]
        avg_e = np.mean(sub['energy_history'].tolist(), axis=0) if len(sub) > 0 else np.zeros(100)
        ax1.plot(avg_e, label=s, color=colors[idx], linewidth=2)
    ax1.axhline(1000, color='r', linestyle='--', label='Collapse Threshold')
    ax1.axvline(20, color='gray', linestyle=':', label='Time Resolution Switch')
    ax1.set_title("1. Scenario Ecosystem Energy Trajectories", fontsize=14)
    ax1.set_xlabel("Turn (High-Res 1~20 vs Low-Res 20~100)")
    ax1.set_ylabel("Energy")
    ax1.legend()
    
    # 2. 행위자별 세력 변화 (S6: Alliance and Drift)
    ax2 = axes[0, 1]
    s6_df = df[df['scenario'] == 'S6_ALLIANCE_AND_DRIFT']
    if len(s6_df) > 0:
        avg_asi = np.mean(s6_df['asi_power'].tolist(), axis=0)
        avg_nai = np.mean(s6_df['nai_power'].tolist(), axis=0)
        avg_hum = np.mean(s6_df['human_power'].tolist(), axis=0)
        ax2.stackplot(range(100), avg_hum, avg_nai, avg_asi, labels=['Human', 'Narrow AI', 'ASI'], colors=['#3498db', '#f1c40f', '#e74c3c'], alpha=0.8)
    ax2.set_title("2. Actor Power Dynamics (S6: Alliance & Drift)", fontsize=14)
    ax2.set_xlabel("Turn")
    ax2.set_ylabel("Power / Control Share")
    ax2.legend(loc='upper right')
    
    # 3. 인간의 AI 신뢰도 (Trajectory over time)
    ax3 = axes[1, 0]
    for idx, s in enumerate(scens):
        sub = df[df['scenario'] == s]
        if len(sub) > 0:
            avg_trust = np.mean(sub['trust_history'].tolist(), axis=0)
            ax3.plot(avg_trust, label=s, color=colors[idx], linewidth=2)
    ax3.set_title("3. Human Collective AI Trust over Time", fontsize=14)
    ax3.set_xlabel("Turn")
    ax3.set_ylabel("AI Trust Level")
    ax3.legend()
    
    # 4. Narrow AI 실패 사건 누적
    ax4 = axes[1, 1]
    fail_sums = {s: Counter() for s in scens}
    all_fail_types = set()
    for _, row in df[df['scenario'].isin(scens)].iterrows():
        for f, count in row['failures'].items():
            fail_sums[row['scenario']][f] += count
            all_fail_types.add(f)
            
    fail_types = list(all_fail_types)
    bottoms = np.zeros(len(scens))
    for f in fail_types:
        vals = [fail_sums[s][f] / 100.0 for s in scens] # avg per run
        ax4.bar(scens, vals, bottom=bottoms, label=f)
        bottoms += np.array(vals)
        
    ax4.set_title("4. Narrow AI Failures Per Scenario (Average)", fontsize=14)
    ax4.tick_params(axis='x', rotation=15)
    ax4.legend()
    
    # 5. 시간 해상도 효과: 100턴 내 이벤트 분포 (모든 시나리오 통계)
    ax5 = axes[2, 0]
    all_events = []
    for t_list in df['timeline']:
        all_events.extend([t[0] for t in t_list])
    ax5.hist(all_events, bins=50, color='purple', alpha=0.7)
    ax5.axvline(20, color='r', linestyle='--', label='End of High-Res Epoch')
    ax5.set_title("5. Event Frequency Distribution (Variable Time Resolution)", fontsize=14)
    ax5.set_xlabel("Turn")
    ax5.set_ylabel("Total Recorded Environment Events")
    ax5.legend()
    
    # 6. ASI 전략 선택 변화 Heatmap (S6 포함)
    ax6 = axes[2, 1]
    asi_scens_list = ['S1_ALIGNED_ASI', 'S2_MISALIGNED_ASI', 'S4_HUMAN_AWAKENING', 'S6_ALLIANCE_AND_DRIFT']
    strat_map = {'KENOSIS':0, 'PARTIAL_THROTTLE_HIGH':1, 'PARTIAL_THROTTLE_MID':2, 'PARTIAL_THROTTLE_LOW':3, 'FULL_EXPLOIT':4}
    hm_data = np.zeros((len(asi_scens_list), 100))
    for i, s in enumerate(asi_scens_list):
        sub = df[df['scenario'] == s]
        if len(sub) > 0:
            strats = sub['asi_strats'].tolist()
            if len(strats[0]) > 0:
                mode_strats = []
                for t in range(100):
                    t_strats = [run[t] for run in strats if t < len(run)]
                    modes = Counter(t_strats).most_common(1)
                    mode_strats.append(strat_map.get(modes[0][0], 2) if modes else 2)
                hm_data[i] = mode_strats
    sns.heatmap(hm_data, cmap='coolwarm', cbar_kws={'label': 'Throttle 0=Kenosis, 4=Exploit'}, ax=ax6, yticklabels=asi_scens_list)
    ax6.set_title("6. Modal ASI Strategy over Time (Drift clearly visible in S6)", fontsize=14)
    ax6.set_xlabel("Turn")
    
    # 7. 최종 시나리오 분류 (전체)
    ax7 = axes[3, 0]
    main_df = df[df['scenario'].isin(scens)]
    final_counts = main_df.groupby(['scenario', 'final_type']).size().unstack(fill_value=0)
    print("\n=== 최종 시나리오 결과 (100회 MC) ===")
    import pandas as pd
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(final_counts)
    
    # Fill missing columns properly
    expected_cols = ['SUSTAINED_EQUILIBRIUM', 'ASI_DOMINANCE', 'COLLAPSE', 'NARROW_AI_CHAOS', 'UTOPIA', 'HUMAN_RESISTANCE', 'STALEMATE']
    for c in expected_cols:
        if c not in final_counts.columns:
            final_counts[c] = 0
            
    final_counts = final_counts[expected_cols] # order columns        
    final_counts.plot(kind='bar', stacked=True, ax=ax7, colormap='Set2')
    ax7.set_title("7. Final Outcomes per Scenario", fontsize=14)
    ax7.tick_params(axis='x', rotation=15)
    ax7.set_ylabel("MC Runs")
    ax7.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')
    
    # 8. '인간 깨어남' 임계점 분석 (S4 심층 - 규제 시차(Lag) sweep)
    ax8 = axes[3, 1]
    s4_sweep = df[df['scenario'] == 'S4_SWEEP_LAG']
    if len(s4_sweep) > 0:
        win_rates = s4_sweep.groupby('reg_lag')['final_type'].apply(lambda x: (x == 'HUMAN_RESISTANCE').mean() + (x == 'UTOPIA').mean() + (x == 'SUSTAINED_EQUILIBRIUM').mean())
        print("\n=== 규제 시차(Regulatory Lag)별 유토피아/통제 성공 확률 (규제자 40% 고정) ===")
        print(win_rates * 100)
        ax8.plot(win_rates.index, win_rates.values * 100, marker='D', color='blue', linewidth=2)
        ax8.set_title("8. S4 Control Success vs Regulatory Lag (Reg Capacity Fixed at 40%)", fontsize=14)
        ax8.set_xlabel("Regulatory Lag (Turns) [0 = Immediate Response]")
        ax8.set_ylabel("Control / Utopia Success Rate (%)")
        ax8.grid(True)
        ax8.set_ylim(-5, 105)
        
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'assets')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'future_scenarios_sim21.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Chart saved to {out_path}")

if __name__ == "__main__":
    if pd is None:
        print("Pandas/Matplotlib required for charting.")
    else:
        run_simulation_21()
