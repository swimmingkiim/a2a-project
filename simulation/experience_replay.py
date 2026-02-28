"""
Prioritized Experience Replay (PER) 버퍼.
LLM RAG의 수학적 대체.

대응 관계:
- RAG: 유사 상황을 텍스트로 검색 -> 프롬프트에 주입
- PER: TD error가 큰 경험을 우선 샘플링 -> 학습에 반영

TD error가 큰 경험 = 기대와 결과가 많이 달랐던 경험
= 가장 많이 배울 수 있는 경험
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Transition:
    """단일 경험 단위."""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    counterparty_id: Optional[str] = None
    trust_delta: float = 0.0
    ecosystem_survived: bool = True


class PrioritizedReplayBuffer:
    """
    에이전트별 독립 경험 버퍼.

    버퍼가 비어있을 때: epsilon-greedy 탐색 (초반)
    버퍼가 채워질 때: 중요 경험 우선 학습 (후반)
    이 전환점이 Finding 31 (러닝 커브)을 만들어낸다.
    """

    def __init__(
        self,
        capacity: int = 2000,
        alpha: float = 0.6,
        beta: float = 0.4,
    ):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.buffer: list[Transition] = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.pos = 0

    def add(self, transition: Transition, td_error: float = 1.0):
        priority = (abs(td_error) + 1e-6) ** self.alpha
        if len(self.buffer) < self.capacity:
            self.buffer.append(transition)
        else:
            self.buffer[self.pos] = transition
        self.priorities[self.pos] = priority
        self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size: int) -> tuple:
        n = len(self.buffer)
        if n < batch_size:
            batch_size = n
        probs = self.priorities[:n] / self.priorities[:n].sum()
        indices = np.random.choice(n, batch_size, p=probs, replace=False)
        weights = (n * probs[indices]) ** (-self.beta)
        weights /= weights.max()
        batch = [self.buffer[i] for i in indices]
        return batch, indices, weights

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        for idx, error in zip(indices, td_errors):
            self.priorities[idx] = (abs(error) + 1e-6) ** self.alpha

    def get_trust_stats(self, counterparty_id: str) -> dict:
        """LLM 버전의 AgentExperienceDB.get_trust_score() 대체."""
        relevant = [
            t for t in self.buffer if t.counterparty_id == counterparty_id
        ]
        if not relevant:
            return {'trust': 0.5, 'n_interactions': 0}
        avg_trust = 0.5 + sum(t.trust_delta for t in relevant)
        return {
            'trust': max(0.0, min(1.0, avg_trust)),
            'n_interactions': len(relevant),
        }

    @property
    def memory_utilization(self) -> float:
        return len(self.buffer) / self.capacity


class SimpleReplayBuffer:
    """PER 비활성화 시 사용하는 균등 샘플링 버퍼."""

    def __init__(self, capacity: int = 2000):
        self.capacity = capacity
        self.buffer: list[Transition] = []
        self.pos = 0

    def add(self, transition: Transition, td_error: float = 1.0):
        if len(self.buffer) < self.capacity:
            self.buffer.append(transition)
        else:
            self.buffer[self.pos] = transition
        self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size: int) -> tuple:
        n = len(self.buffer)
        if n < batch_size:
            batch_size = n
        indices = np.random.choice(n, batch_size, replace=False)
        weights = np.ones(batch_size, dtype=np.float32)
        batch = [self.buffer[i] for i in indices]
        return batch, indices, weights

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        pass  # 균등 버퍼는 우선순위 없음

    def get_trust_stats(self, counterparty_id: str) -> dict:
        relevant = [
            t for t in self.buffer if t.counterparty_id == counterparty_id
        ]
        if not relevant:
            return {'trust': 0.5, 'n_interactions': 0}
        avg_trust = 0.5 + sum(t.trust_delta for t in relevant)
        return {
            'trust': max(0.0, min(1.0, avg_trust)),
            'n_interactions': len(relevant),
        }

    @property
    def memory_utilization(self) -> float:
        return len(self.buffer) / self.capacity
