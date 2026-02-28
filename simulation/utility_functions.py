"""
Sim 25의 핵심: 보상 함수 설계.
"""
from __future__ import annotations
import numpy as np

# ── 기준선: Sim 24의 선형 보상 (대조군) ──────────────────────────────
def linear_reward(
    action: str,
    resource_delta: float,
    current_resources: float,
    ecosystem_energy: float,
    trust_delta: float,
    current_trust: float,
    ecosystem_survived: bool,
    expected_delta: float = 0.0,
) -> float:
    """Sim 24와 동일. 비교 기준선."""
    if not ecosystem_survived:
        return -10.0
    return resource_delta * 0.1 + trust_delta

# ── 실험군 1: 자원만 오목 (기본 오목) ────────────────────────────────
def concave_resource_only(
    action: str,
    resource_delta: float,
    current_resources: float,
    ecosystem_energy: float,
    trust_delta: float,
    current_trust: float,
    ecosystem_survived: bool,
    expected_delta: float = 0.0,
) -> float:
    """
    자원에만 한계 체감 적용.
    신뢰는 선형 유지.
    """
    if not ecosystem_survived:
        return -10.0

    if resource_delta > 0:
        resource_utility = np.log1p(resource_delta) / np.log1p(max(current_resources, 1.0))
    else:
        resource_utility = resource_delta * 0.05  # 손실은 완만하게

    return resource_utility + trust_delta * 0.5

# ── 실험군 2: 자원 오목 + 신뢰 볼록 (완전 오목) ─────────────────────
def concave_full(
    action: str,
    resource_delta: float,
    current_resources: float,
    ecosystem_energy: float,
    trust_delta: float,
    current_trust: float,
    ecosystem_survived: bool,
    expected_delta: float = 0.0,
) -> float:
    """
    자원: 한계 체감 (log)
    신뢰: 한계 체증 (제곱)
    """
    if not ecosystem_survived:
        return -10.0

    if resource_delta > 0:
        resource_utility = np.log1p(resource_delta) / np.log1p(max(current_resources, 1.0))
    else:
        resource_utility = resource_delta * 0.05

    trust_utility = trust_delta * (1.0 + current_trust ** 2)
    ecosystem_bonus = ecosystem_energy * 0.05

    return resource_utility + trust_utility + ecosystem_bonus

# ── 실험군 3: 기대-결과 차이 기반 (그 책의 구조) ─────────────────────
def expectation_gap_reward(
    action: str,
    resource_delta: float,
    current_resources: float,
    ecosystem_energy: float,
    trust_delta: float,
    current_trust: float,
    ecosystem_survived: bool,
    expected_delta: float = 0.0,
) -> float:
    """
    실패를 통과하는 일의 핵심 구조: 만족 = 실제 결과 - 기대 결과
    """
    if not ecosystem_survived:
        return -10.0

    gap = resource_delta - expected_delta

    if gap > 0:
        gap_utility = np.log1p(gap) / np.log1p(max(abs(expected_delta) + 1, 1.0))
    else:
        gap_utility = gap * 0.1

    trust_utility = trust_delta * (1.0 + current_trust ** 2)

    return gap_utility + trust_utility

UTILITY_FUNCTIONS = {
    'linear':           linear_reward,
    'concave_resource': concave_resource_only,
    'concave_full':     concave_full,
    'expectation_gap':  expectation_gap_reward,
}
