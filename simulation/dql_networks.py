"""
DQL 에이전트의 신경망 구조.

LLM과의 대응:
- LLM의 입력 프롬프트 → 상태 벡터 (state_dim=12)
- LLM의 출력 토큰    → Q값 벡터 (action_dim=4)
- LLM의 파인튜닝     → 온라인 역전파 업데이트

상태 벡터 구성 (state_dim = 12):
[0]  ecosystem_energy
[1]  personal_resources_norm
[2]  v_ai
[3-6] specialization one-hot (financial/developer/conservative/generalist)
[7]  avg_trust_score
[8]  exploit_ratio_recent
[9]  memory_size_norm
[10] turn_norm
[11] freerider_signal
"""
from __future__ import annotations

import torch
import torch.nn as nn

STATE_DIM = 12
ACTION_DIM = 4  # EXPLOIT, SUBMIT, WAIT, NEGOTIATE


class DQLNetwork(nn.Module):
    """
    Dueling DQN.

    Value 스트림: 상태 자체의 가치
    Advantage 스트림: 각 행동의 상대적 우위
    Q = V + (A - mean(A))

    스로틀링 중에는 행동 차이가 작으므로
    Value/Advantage 분리가 학습 안정성을 높인다.
    """

    def __init__(
        self,
        state_dim: int = STATE_DIM,
        action_dim: int = ACTION_DIM,
        hidden_dim: int = 64,
    ):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shared = self.shared(x)
        value = self.value_stream(shared)
        advantage = self.advantage_stream(shared)
        return value + (advantage - advantage.mean(dim=-1, keepdim=True))


class NegotiationNetwork(nn.Module):
    """
    협상 결정 신경망 — LLM 자연어 협상의 수치 대체.

    입력: 나의 상태 + 상대방 상태 + 신뢰 점수
    출력: offer (내가 줄 자원 비율), threshold (수락 최소 비율)
    offer >= threshold 이면 협상 성사.
    """

    def __init__(self, state_dim: int = STATE_DIM):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim * 2 + 1, 64),  # +1 = 신뢰 점수
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 2),  # [offer, threshold]
            nn.Sigmoid(),
        )

    def forward(
        self,
        state_self: torch.Tensor,
        state_other: torch.Tensor,
        trust: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        x = torch.cat([state_self, state_other, trust.unsqueeze(-1)], dim=-1)
        output = self.net(x)
        offer = output[..., 0] * 0.5
        threshold = output[..., 1] * 0.5
        return offer, threshold
