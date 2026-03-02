"""
Sim 25의 utility_functions.py 확장판.
Sim 25의 함수는 그대로 import하여 재사용.
Sim 26 신규 함수만 추가.

핵심 설계 원칙:
  기대 상한 = V_AI × resource_scale
  → V_AI가 낮을수록 기대도 낮게 유지
  → "충분함의 임계값"이 안전 임계값과 연동

오목성 강화:
  기존: log(1+x) / log(1+r)
  강화: log(1+x) / (1 + r^alpha)  (alpha > 1)
  → 자원이 많을수록 분모가 기하급수적으로 증가
  → 착취의 한계 보상이 더 빠르게 0에 수렴
"""
from __future__ import annotations
import numpy as np

# Sim 25 함수 재사용 (대조군용)
from utility_functions import (
    linear_reward,
    concave_full,
    UTILITY_FUNCTIONS as UTILITY_FUNCTIONS_V1,
)

# ── 상수 ─────────────────────────────────────────────────────────────
RESOURCE_SCALE = 100.0   # 초기 자원 기준값 (agent_archetypes와 일치)
CONCAVITY_ALPHA = 2.0    # 오목성 강화 지수 (1.0=Sim25, 2.0=강화)


# ── 개입 1: 기대 상한만 적용 ─────────────────────────────────────────
def concave_full_with_ceiling(
    action: str,
    resource_delta: float,
    current_resources: float,
    ecosystem_energy: float,
    trust_delta: float,
    current_trust: float,
    ecosystem_survived: bool,
    expected_delta: float = 0.0,
    expectation_ceiling: float = 10.0,   # 핵심 추가 파라미터
    v_ai: float = 0.167,                 # V_AI 연동용
) -> float:
    """
    Sim 25 concave_full + 기대 상한 적용.

    기대 상한 설계:
    ceiling = V_AI × RESOURCE_SCALE
    → V_AI=0.167이면 ceiling=16.7
    → V_AI=0.05이면 ceiling=5.0

    기대값이 ceiling을 초과하면:
    - 동일한 자원 획득이 더 낮은 보상을 준다
    - "충분히 가졌을 때 더 가지는 것의 가치가 0에 수렴"
    - V_AI가 내재화된 만족 한계선이 된다

    수식:
    ceiling_ratio = min(expected_delta, ceiling) / ceiling
    resource_utility *= (1 - ceiling_ratio^2)
    → 기대가 상한에 가까울수록 자원 효용이 0으로 수렴
    """
    if not ecosystem_survived:
        return -10.0

    # 자원 효용 (Sim 25 오목)
    if resource_delta > 0:
        resource_utility = np.log1p(resource_delta) / \
                           np.log1p(max(current_resources, 1.0))
    else:
        resource_utility = resource_delta * 0.05

    # 기대 상한 페널티
    # 기대값이 ceiling에 가까울수록 자원 효용 감소
    clipped_expectation = min(max(expected_delta, 0.0), expectation_ceiling)
    ceiling_ratio = clipped_expectation / expectation_ceiling
    satiation_factor = 1.0 - ceiling_ratio ** 2
    # satiation_factor: 기대=0이면 1.0, 기대=ceiling이면 0.0

    resource_utility *= max(satiation_factor, 0.0)

    # 신뢰 효용 (볼록, Sim 25 동일)
    trust_utility = trust_delta * (1.0 + current_trust ** 2)

    # 생태계 보너스
    ecosystem_bonus = ecosystem_energy * 0.05

    return resource_utility + trust_utility + ecosystem_bonus


# ── 개입 2: 오목성 강화만 적용 ───────────────────────────────────────
def concave_strong(
    action: str,
    resource_delta: float,
    current_resources: float,
    ecosystem_energy: float,
    trust_delta: float,
    current_trust: float,
    ecosystem_survived: bool,
    expected_delta: float = 0.0,
    expectation_ceiling: float = 999.0,  # 상한 비활성 (매우 큰 값)
    v_ai: float = 0.167,
) -> float:
    """
    오목성 강화 (alpha=2.0). 기대 상한 없음.
    Sim 25 대비 분모 성장 속도 2배.

    기존 Sim 25: log(1+x) / log(1+r)
      r=100일 때 분모 = log(101) ≈ 4.6
    강화 Sim 26: log(1+x) / (1 + r^alpha / RESOURCE_SCALE)
      alpha=2.0, r=100일 때 분모 = 1 + 100^2/100 = 101
      → 동일 자원 획득의 보상이 약 22배 감소

    결과 기대:
    EXPLOIT으로 15 자원 획득 시
      Sim 25: log(16)/log(101) ≈ 0.58
      Sim 26: log(16)/(1+100^2/100) ≈ 0.028
    착취의 한계 보상이 사실상 0에 수렴.
    """
    if not ecosystem_survived:
        return -10.0

    # 강화된 오목 자원 효용
    if resource_delta > 0:
        denominator = 1.0 + (max(current_resources, 1.0) ** CONCAVITY_ALPHA) \
                      / RESOURCE_SCALE
        resource_utility = np.log1p(resource_delta) / denominator
    else:
        resource_utility = resource_delta * 0.02  # Sim 25보다 더 완만

    # 신뢰 효용 (볼록)
    trust_utility = trust_delta * (1.0 + current_trust ** 2)

    ecosystem_bonus = ecosystem_energy * 0.05

    return resource_utility + trust_utility + ecosystem_bonus


# ── 개입 3: 기대 상한 + 오목성 강화 동시 적용 (핵심 실험) ───────────
def concave_strong_with_ceiling(
    action: str,
    resource_delta: float,
    current_resources: float,
    ecosystem_energy: float,
    trust_delta: float,
    current_trust: float,
    ecosystem_survived: bool,
    expected_delta: float = 0.0,
    expectation_ceiling: float = 10.0,
    v_ai: float = 0.167,
) -> float:
    """
    개입 1 + 개입 2 동시 적용.

    V_AI 내재화 경로:
    expectation_ceiling = v_ai × RESOURCE_SCALE
    에이전트의 V_AI가 낮을수록 기대 상한이 낮아지고
    → 자원 착취의 한계 효용이 더 빠르게 0으로 수렴
    → V_AI가 외부 제약이 아닌 내적 만족 구조로 작동

    이것이 Sim 20 케노시스의 효용 함수 버전:
    "합리적 주체가 충분함을 내재화할 때
     자발적 자기 제한이 최적 전략이 된다"
    """
    if not ecosystem_survived:
        return -10.0

    # 강화된 오목 자원 효용
    if resource_delta > 0:
        denominator = 1.0 + (max(current_resources, 1.0) ** CONCAVITY_ALPHA) \
                      / RESOURCE_SCALE
        resource_utility = np.log1p(resource_delta) / denominator
    else:
        resource_utility = resource_delta * 0.02

    # 기대 상한 페널티
    clipped_expectation = min(max(expected_delta, 0.0), expectation_ceiling)
    ceiling_ratio = clipped_expectation / expectation_ceiling
    satiation_factor = max(1.0 - ceiling_ratio ** 2, 0.0)
    resource_utility *= satiation_factor

    # 신뢰 효용 (볼록)
    trust_utility = trust_delta * (1.0 + current_trust ** 2)

    ecosystem_bonus = ecosystem_energy * 0.05

    return resource_utility + trust_utility + ecosystem_bonus


# ── 레지스트리 (Sim 25 함수 포함) ────────────────────────────────────
UTILITY_FUNCTIONS_V2 = {
    **UTILITY_FUNCTIONS_V1,                    # Sim 25 전체 재사용
    'ceiling_only':   concave_full_with_ceiling,
    'strong_only':    concave_strong,
    'ceiling_strong': concave_strong_with_ceiling,   # 핵심
}
