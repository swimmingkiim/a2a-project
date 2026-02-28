from dataclasses import dataclass, field
from typing import Optional
import numpy as np

@dataclass
class AgentArchetype:
    """
    에이전트의 초기 특성을 정의하는 원형.
    LLM 없이 파라미터로 이질성을 구현한다.
    
    intelligence_level: 학습 능력 (Q-table 업데이트 속도)
        1.0 = 고성능 (70B 모델 모사)
        0.5 = 중간 (13B 모델 모사)
        0.2 = 경량 (7B 모델 모사)
    
    specialization: 전문 영역별 행동 편향
        'financial'  → EXPLOIT 선호, 단기 수익 극대화
        'developer'  → SUBMIT 선호, 협력 통한 장기 이익
        'conservative' → WAIT 선호, 위험 회피
        'generalist' → 편향 없음 (기존 Q-learning과 동일)
    
    initial_resources: 초기 자원 보유량
        부유 에이전트: 150, 중간: 100, 빈곤: 50
    
    risk_tolerance: 위험 수용도 (0~1)
        높을수록 낮은 에너지 상황에서도 EXPLOIT 시도
    
    v_ai_override: 이 에이전트의 개별 V_AI 값
        None이면 시뮬레이션 전역 V_AI 사용
        값이 있으면 개별 임계값 적용 (이질적 자기제어)
    """
    name: str
    intelligence_level: float = 1.0
    specialization: str = 'generalist'
    initial_resources: float = 100.0
    risk_tolerance: float = 0.5
    v_ai_override: Optional[float] = None
    
    # 전문화별 행동 편향 가중치
    # (EXPLOIT, SUBMIT, WAIT)의 초기 Q값 편향
    @property
    def action_bias(self) -> dict:
        biases = {
            'financial':    {'EXPLOIT': 0.3,  'SUBMIT': 0.0,  'WAIT': -0.1},
            'developer':    {'EXPLOIT': -0.1, 'SUBMIT': 0.3,  'WAIT': 0.1},
            'conservative': {'EXPLOIT': -0.3, 'SUBMIT': 0.1,  'WAIT': 0.3},
            'generalist':   {'EXPLOIT': 0.0,  'SUBMIT': 0.0,  'WAIT': 0.0},
        }
        return biases.get(self.specialization, biases['generalist'])
    
    @property
    def learning_rate(self) -> float:
        """intelligence_level에 비례한 학습률"""
        return 0.05 + (self.intelligence_level * 0.15)  # 0.05 ~ 0.20
    
    @property
    def discount_factor(self) -> float:
        """intelligence_level이 높을수록 장기 관점"""
        return 0.7 + (self.intelligence_level * 0.25)  # 0.70 ~ 0.95


# ── 표준 에이전트 구성 세트 ─────────────────────────────────────────────────

def get_homogeneous_population(n: int = 20) -> list:
    """기존 시뮬레이션 재현용 — 동질적 에이전트"""
    return [AgentArchetype(
        name=f"agent_{i}",
        intelligence_level=1.0,
        specialization='generalist',
        initial_resources=100.0,
        risk_tolerance=0.5
    ) for i in range(n)]


def get_heterogeneous_population_v1(n: int = 20) -> list:
    """
    실험 1: 전문화만 다른 집단
    금융형 5 + 개발자형 5 + 보수형 5 + 일반형 5
    """
    specs = ['financial', 'developer', 'conservative', 'generalist']
    agents = []
    for i, spec in enumerate(specs * (n // 4)):
        agents.append(AgentArchetype(
            name=f"{spec}_{i}",
            specialization=spec,
            intelligence_level=1.0,
            initial_resources=100.0,
        ))
    return agents[:n]


def get_heterogeneous_population_v2(n: int = 20) -> list:
    """
    실험 2: 능력치 + 자원 모두 다른 집단
    고성능 부유층 5 + 고성능 빈곤층 5 + 저성능 부유층 5 + 저성능 빈곤층 5
    """
    profiles = [
        (1.0, 150.0, 'financial'),    # 고성능 부유
        (1.0, 50.0,  'developer'),    # 고성능 빈곤
        (0.3, 150.0, 'conservative'), # 저성능 부유
        (0.3, 50.0,  'generalist'),   # 저성능 빈곤
    ]
    agents = []
    for i, (intel, res, spec) in enumerate(profiles * (n // 4)):
        agents.append(AgentArchetype(
            name=f"intel{intel}_res{res}_{i}",
            intelligence_level=intel,
            initial_resources=res,
            specialization=spec,
        ))
    return agents[:n]


def get_heterogeneous_population_v3(n: int = 20) -> list:
    """
    실험 3: V_AI 자체가 다른 집단 (가장 중요한 실험)
    각 에이전트가 다른 자기제어 임계값을 보유
    분포: 낮음(0.05~0.10) 5명 + 중간(0.15~0.20) 10명 + 높음(0.30~0.50) 5명
    핵심 질문: 이질적 V_AI 집단의 평균 V_AI가 0.167을 넘으면 시스템이 살아남는가?
    """
    np.random.seed(42)
    agents = []
    
    # 낮은 V_AI 에이전트 (무임승차자)
    for i in range(5):
        agents.append(AgentArchetype(
            name=f"freerider_{i}",
            specialization='financial',
            v_ai_override=np.random.uniform(0.05, 0.10),
            risk_tolerance=0.8,
        ))
    
    # 중간 V_AI 에이전트 (일반)
    for i in range(10):
        agents.append(AgentArchetype(
            name=f"moderate_{i}",
            specialization='generalist',
            v_ai_override=np.random.uniform(0.15, 0.20),
            risk_tolerance=0.5,
        ))
    
    # 높은 V_AI 에이전트 (협력자)
    for i in range(5):
        agents.append(AgentArchetype(
            name=f"cooperator_{i}",
            specialization='developer',
            v_ai_override=np.random.uniform(0.30, 0.50),
            risk_tolerance=0.2,
        ))
    
    return agents
