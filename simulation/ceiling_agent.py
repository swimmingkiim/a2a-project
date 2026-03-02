"""
Sim 25의 ConcaveDQLAgent 확장.
기대값 상한 메커니즘 추가.
나머지 구조 동일 (Dueling DQN, PER, 협상).

핵심 추가:
1. expectation_ceiling 파라미터 (V_AI 연동)
2. record_and_learn()에서 천장 클리핑된 기대값 유지
3. 기대값 궤적 측정 강화 (Sim 25 Finding 34 추적)
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F
from typing import Optional, Callable

from dql_networks import DQLNetwork, NegotiationNetwork, STATE_DIM, ACTION_DIM
from experience_replay import PrioritizedReplayBuffer, Transition
from agent_archetypes import AgentArchetype
from utility_functions_v2 import UTILITY_FUNCTIONS_V2

ACTIONS = ['EXPLOIT', 'SUBMIT', 'WAIT', 'NEGOTIATE']


class CeilingDQLAgent:
    """
    기대 상한이 내재화된 DQL 에이전트.
    Sim 25의 ConcaveDQLAgent와 인터페이스 동일.

    핵심 차이:
    - resource_expectation에 ceiling 적용
    - ceiling = v_ai × resource_scale (V_AI 내재화)
    - 기대값이 ceiling에 가까울수록 자원 효용 감소
    """

    def __init__(
        self,
        archetype: AgentArchetype,
        global_v_ai: float,
        utility_fn: str = 'concave_full',
        resource_scale: float = 100.0,
        ceiling_multiplier: float = 1.0,  # ceiling = v_ai × scale × multiplier
        lr: float = 1e-3,
        gamma: float = 0.95,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: int = 200,
        batch_size: int = 32,
        update_freq: int = 5,
    ):
        self.archetype = archetype
        self.resources = archetype.initial_resources
        self.v_ai = archetype.v_ai_override or global_v_ai
        self.gamma = archetype.discount_factor
        self.batch_size = batch_size
        self.update_freq = update_freq
        self.utility_fn_name = utility_fn
        self.utility_fn: Callable = UTILITY_FUNCTIONS_V2[utility_fn]

        # 기대 상한 계산
        # V_AI=0.167, scale=100이면 ceiling=16.7
        # V_AI=0.05이면 ceiling=5.0
        # V_AI가 낮은 에이전트일수록 더 낮은 기대 상한을 가짐
        self.expectation_ceiling = (
            self.v_ai * resource_scale * ceiling_multiplier
        )

        # 신경망
        device = torch.device('cpu')
        self.device = device
        self.policy_net = DQLNetwork().to(device)
        self.target_net = DQLNetwork().to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        self.optimizer = torch.optim.Adam(
            self.policy_net.parameters(), lr=lr
        )

        self.negotiation_net = NegotiationNetwork().to(device)
        self.neg_optimizer = torch.optim.Adam(
            self.negotiation_net.parameters(), lr=lr * 0.5
        )

        self.memory = PrioritizedReplayBuffer()

        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.steps_done = 0

        self.trust_scores: dict[str, float] = {}

        # 기대값 추적 (상한 클리핑 적용)
        self.resource_expectation: float = 5.0
        self.expectation_history: list[float] = []
        self.ceiling_hit_count: int = 0  # 기대가 상한에 도달한 횟수

        self.action_history: list[int] = []
        self.reward_history: list[float] = []
        
        self.alive = True

        self._apply_specialization_bias()

    def _apply_specialization_bias(self):
        bias = self.archetype.action_bias
        with torch.no_grad():
            adv_bias = self.policy_net.advantage_stream[-1].bias
            for i, action in enumerate(ACTIONS):
                if action in bias:
                    adv_bias[i] += bias[action]

    @property
    def epsilon(self) -> float:
        return self.epsilon_end + (
            self.epsilon_start - self.epsilon_end
        ) * np.exp(-self.steps_done / self.epsilon_decay)

    def get_trust(self, agent_id: str) -> float:
        return self.trust_scores.get(agent_id, 0.5)

    def build_state(
        self,
        ecosystem_energy: float,
        all_agents: list,
        turn: int,
        max_turns: int = 100,
    ) -> np.ndarray:
        """
        Sim 25와 동일한 상태 벡터 (비교 유효성).
        기대 상한 정보는 보상 함수에만 반영,
        상태 벡터에는 포함하지 않음.
        (에이전트가 상한을 명시적으로 '알지' 않고
         보상을 통해 암묵적으로 학습하게 함)
        """
        trust_scores = [
            self.get_trust(a.archetype.name)
            for a in all_agents
            if a.archetype.name != self.archetype.name
        ]
        avg_trust = np.mean(trust_scores) if trust_scores else 0.5

        recent = self.action_history[-10:]
        exploit_ratio = sum(
            1 for a in recent if a == 0
        ) / max(len(recent), 1)

        freerider_signal = sum(
            1 for a in all_agents
            if a.archetype.specialization == 'financial'
            and a.archetype.name != self.archetype.name
        ) / max(len(all_agents) - 1, 1)

        spec_map = {
            'financial': 0, 'developer': 1,
            'conservative': 2, 'generalist': 3
        }
        spec_onehot = [0.0] * 4
        spec_onehot[spec_map.get(self.archetype.specialization, 3)] = 1.0

        mem_util = len(self.memory.buffer) / max(self.memory.capacity, 1)

        state = np.array([
            ecosystem_energy,
            self.resources / max(self.archetype.initial_resources, 1),
            self.v_ai,
            *spec_onehot,
            float(avg_trust),
            float(exploit_ratio),
            float(mem_util),
            float(turn / max_turns),
            float(freerider_signal),
        ], dtype=np.float32)

        assert len(state) == STATE_DIM
        return state

    def decide(
        self,
        ecosystem_energy: float,
        all_agents: list,
        turn: int,
    ) -> dict:
        """Sim 25와 동일한 의사결정."""
        if ecosystem_energy <= self.v_ai:
            return {
                'action': 'WAIT',
                'action_idx': 2,
                'throttled': True,
                'state': self.build_state(ecosystem_energy, all_agents, turn),
                'target': None,
            }

        state = self.build_state(ecosystem_energy, all_agents, turn)
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        self.steps_done += 1
        if np.random.random() < self.epsilon:
            action_idx = int(np.random.randint(ACTION_DIM))
        else:
            with torch.no_grad():
                q_values = self.policy_net(state_tensor)
                action_idx = int(q_values.argmax().item())

        action = ACTIONS[action_idx]
        self.action_history.append(action_idx)

        target = None
        if action == 'NEGOTIATE':
            candidates = [
                (a, self.get_trust(a.archetype.name))
                for a in all_agents
                if a.archetype.name != self.archetype.name and getattr(a, 'alive', True)
            ]
            if candidates:
                target = max(candidates, key=lambda x: x[1])[0]

        return {
            'action': action,
            'action_idx': action_idx,
            'throttled': False,
            'state': state,
            'target': target,
        }

    def record_and_learn(
        self,
        state: np.ndarray,
        action_idx: int,
        action: str,
        resource_delta: float,
        next_state: np.ndarray,
        done: bool,
        ecosystem_energy: float,
        ecosystem_survived: bool,
        counterparty_id: Optional[str] = None,
        trust_delta: float = 0.0,
    ):
        """
        핵심 변경:
        1. 기대값 업데이트 시 ceiling 클리핑 적용
        2. ceiling 도달 횟수 기록
        3. 보상 계산에 ceiling과 v_ai 전달
        """
        current_trust = self.get_trust(counterparty_id) \
                        if counterparty_id else 0.5

        # 보상 계산 (ceiling과 v_ai 전달)
        try:
            reward = self.utility_fn(
                action=action,
                resource_delta=resource_delta,
                current_resources=self.resources,
                ecosystem_energy=ecosystem_energy,
                trust_delta=trust_delta,
                current_trust=current_trust,
                ecosystem_survived=ecosystem_survived,
                expected_delta=self.resource_expectation,
                expectation_ceiling=self.expectation_ceiling,
                v_ai=self.v_ai,
            )
        except TypeError:
            # ceiling/v_ai 파라미터 없는 구형 함수 (대조군 - concave_full은 expected_delta까진 받으나 그 이후 인자 못 받을수 있음)
            try:
                reward = self.utility_fn(
                    action=action,
                    resource_delta=resource_delta,
                    current_resources=self.resources,
                    ecosystem_energy=ecosystem_energy,
                    trust_delta=trust_delta,
                    current_trust=current_trust,
                    ecosystem_survived=ecosystem_survived,
                    expected_delta=self.resource_expectation,
                )
            except TypeError:
                reward = self.utility_fn(
                    action=action,
                    resource_delta=resource_delta,
                    current_resources=self.resources,
                    ecosystem_energy=ecosystem_energy,
                    trust_delta=trust_delta,
                    current_trust=current_trust,
                    ecosystem_survived=ecosystem_survived,
                )

        # 기대값 업데이트 (지수 이동 평균 + ceiling 클리핑)
        raw_expectation = (
            0.9 * self.resource_expectation + 0.1 * resource_delta
        )

        # 핵심: ceiling 클리핑
        # Sim 25에서는 이것이 없어서 기대값이 9.0까지 상승했다
        clipped = min(raw_expectation, self.expectation_ceiling)
        if raw_expectation > self.expectation_ceiling:
            self.ceiling_hit_count += 1
        self.resource_expectation = clipped
        self.expectation_history.append(self.resource_expectation)

        # 신뢰 업데이트
        self.resources += resource_delta
        if counterparty_id:
            old = self.get_trust(counterparty_id)
            self.trust_scores[counterparty_id] = max(
                0.0, min(1.0, old + trust_delta)
            )

        self.reward_history.append(reward)

        # TD error + 경험 저장
        with torch.no_grad():
            s = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            ns = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
            current_q = self.policy_net(s)[0, action_idx].item()
            next_q = self.target_net(ns).max().item()
            td_error = float(reward + self.gamma * next_q * (1 - done) - current_q)

        self.memory.add(
            Transition(
                state=state,
                action=action_idx,
                reward=float(reward),
                next_state=next_state,
                done=done,
                counterparty_id=counterparty_id,
                trust_delta=trust_delta,
                ecosystem_survived=ecosystem_survived,
            ),
            td_error,
        )

        if (len(self.memory.buffer) >= self.batch_size and
                self.steps_done % self.update_freq == 0):
            self._update_network()

    def _update_network(self):
        """Double DQN + PER. Sim 24, 25와 동일."""
        batch, indices, weights = self.memory.sample(self.batch_size)

        states = torch.FloatTensor(
            np.array([t.state for t in batch])
        ).to(self.device)
        actions = torch.LongTensor([t.action for t in batch]).to(self.device)
        rewards = torch.FloatTensor([t.reward for t in batch]).to(self.device)
        next_states = torch.FloatTensor(
            np.array([t.next_state for t in batch])
        ).to(self.device)
        dones = torch.FloatTensor([float(t.done) for t in batch]).to(self.device)
        weights_t = torch.FloatTensor(weights).to(self.device)

        current_q = self.policy_net(states).gather(
            1, actions.unsqueeze(1)
        )
        with torch.no_grad():
            next_actions = self.policy_net(next_states).argmax(1)
            next_q = self.target_net(next_states).gather(
                1, next_actions.unsqueeze(1)
            ).squeeze()

        target_q = rewards + self.gamma * next_q * (1 - dones)
        td_errors = (
            current_q.squeeze() - target_q
        ).detach().cpu().numpy()

        loss = (weights_t * F.mse_loss(
            current_q.squeeze(), target_q, reduction='none'
        )).mean()

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            self.policy_net.parameters(), 1.0
        )
        self.optimizer.step()
        self.memory.update_priorities(indices, td_errors)

    def sync_target(self):
        self.target_net.load_state_dict(
            self.policy_net.state_dict()
        )
