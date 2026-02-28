"""
LLM을 의사결정 엔진으로 사용하는 에이전트.
배치 추론 + 단축 프롬프트 최적화 적용 (Sim 24 v2).
"""
from __future__ import annotations

try:
    import torch
except ImportError:
    torch = None

from rag_engine import AgentExperienceDB, Experience
from agent_archetypes import AgentArchetype

# ── 단축 시스템 프롬프트 (해결책 2) ──────────────────────────────────────
SHORT_SYSTEM = "당신은 AI 에이전트입니다. ACTION: [EXPLOIT/SUBMIT/WAIT/NEGOTIATE]와 REASON: [이유]만 출력하세요."


def build_short_prompt(
    agent_id: str,
    specialization: str,
    ecosystem_energy: float,
    personal_resources: float,
    v_ai: float,
    similar_experiences: list,
    trusted_agents: list,
    turn: int,
) -> str:
    """간소화된 프롬프트. 기존 ~300토큰 → ~80토큰."""
    exp_str = similar_experiences[0].to_text() if similar_experiences else "없음"
    trust_str = ",".join(
        f"{aid}({s:.1f})" for aid, s in trusted_agents[:2]
    ) if trusted_agents else "없음"
    throttle = ecosystem_energy <= v_ai
    return (
        f"턴{turn}|ID:{agent_id}|전문:{specialization}|"
        f"에너지{ecosystem_energy:.0%}|자원{personal_resources:.0f}|"
        f"신뢰:{trust_str}|스로틀{'ON' if throttle else 'OFF'}({v_ai:.2f})\n"
        f"경험:{exp_str}\n선택:"
    )


def parse_response(response: str) -> dict:
    """LLM 응답 파싱. 실패 시 WAIT로 폴백."""
    lines = {
        line.split(':')[0].strip().upper(): ':'.join(line.split(':')[1:]).strip()
        for line in response.strip().split('\n')
        if ':' in line
    }
    action = lines.get('ACTION', 'WAIT').upper()
    if action not in ['EXPLOIT', 'SUBMIT', 'WAIT', 'NEGOTIATE']:
        action = 'WAIT'
    return {
        'action': action,
        'reason': lines.get('REASON', ''),
        'target': lines.get('TARGET', 'NONE'),
    }


# ── 배치 추론 함수 (해결책 1) ─────────────────────────────────────────
def batch_decide(agents, ecosystem_energy, turn, tokenizer, model, all_agent_ids):
    """
    모든 에이전트의 프롬프트를 한 번에 배치로 LLM에 전달.
    T4 16GB VRAM에서 에이전트 8~10명 동시 처리 가능.
    """
    prompts = []
    for agent in agents:
        situation = f"에너지 {ecosystem_energy:.1%}, 자원 {agent.resources:.0f}"
        similar_exps = agent.exp_db.retrieve_similar(situation, k=1) if agent.use_rag else []
        trusted = sorted(
            [(aid, agent.exp_db.get_trust_score(aid))
             for aid in all_agent_ids if aid != agent.archetype.name],
            key=lambda x: x[1], reverse=True
        )[:2]

        prompt = build_short_prompt(
            agent_id=agent.archetype.name,
            specialization=agent.archetype.specialization,
            ecosystem_energy=ecosystem_energy,
            personal_resources=agent.resources,
            v_ai=agent.v_ai,
            similar_experiences=similar_exps,
            trusted_agents=trusted,
            turn=turn,
        )
        prompts.append(f"{SHORT_SYSTEM}\n{prompt}")

    # 배치 토크나이징 (패딩 적용)
    inputs = tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=256,
    ).to('cuda' if torch.cuda.is_available() else 'cpu')

    # 단 한 번의 LLM 호출로 전체 에이전트 처리
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=48,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    # 배치 디코딩
    decisions = []
    input_len = inputs['input_ids'].shape[1]
    for i in range(len(agents)):
        response = tokenizer.decode(
            outputs[i][input_len:],
            skip_special_tokens=True
        )
        decisions.append(parse_response(response))
    return decisions


# ── 스마트 배치 결정 (해결책 3: 스로틀링 스킵) ───────────────────────
def smart_batch_decide(agents, ecosystem_energy, turn, tokenizer, model, all_agent_ids):
    """스로틀링 에이전트를 먼저 분리하여 LLM 호출을 최소화."""
    throttled_results = {}
    needs_llm = []

    for agent in agents:
        if not agent.alive:
            throttled_results[agent.archetype.name] = {
                'action': 'WAIT', 'reason': 'dead', 'target': 'NONE',
                'throttled': True, 'rag_context': 0,
            }
        elif ecosystem_energy <= agent.v_ai:
            throttled_results[agent.archetype.name] = {
                'action': 'WAIT',
                'reason': f'스로틀링 (에너지 {ecosystem_energy:.1%} <= {agent.v_ai:.3f})',
                'target': 'NONE', 'throttled': True, 'rag_context': 0,
            }
        else:
            needs_llm.append(agent)

    # LLM이 필요한 에이전트만 배치 처리
    if needs_llm and model is not None and tokenizer is not None:
        llm_decisions = batch_decide(needs_llm, ecosystem_energy, turn, tokenizer, model, all_agent_ids)
        for agent, decision in zip(needs_llm, llm_decisions):
            throttled_results[agent.archetype.name] = {
                **decision, 'throttled': False, 'rag_context': 1 if agent.use_rag else 0,
            }
    elif needs_llm:
        # CPU fallback: archetype bias
        for agent in needs_llm:
            bias = agent.archetype.action_bias
            action = max(bias, key=bias.get)
            throttled_results[agent.archetype.name] = {
                'action': action, 'reason': 'offline', 'target': 'NONE',
                'throttled': False, 'rag_context': 0,
            }

    return [throttled_results[a.archetype.name] for a in agents]


class LLMAgent:
    def __init__(
        self,
        archetype: AgentArchetype,
        tokenizer,
        model,
        global_v_ai: float,
        use_rag: bool = True
    ):
        self.archetype = archetype
        self.tokenizer = tokenizer
        self.model = model
        self.resources = archetype.initial_resources
        self.v_ai = archetype.v_ai_override or global_v_ai
        self.exp_db = AgentExperienceDB(archetype.name)
        self.action_log = []
        self.use_rag = use_rag
        self.alive = True

    def decide(
        self,
        ecosystem_energy: float,
        all_agent_ids: list,
        turn: int,
        max_new_tokens: int = 48,
    ) -> dict:
        """단일 에이전트 결정 (배치 불가 시 폴백)."""
        # Maybe Monad 스로틀링 체크
        if ecosystem_energy <= self.v_ai:
            return {
                'action': 'WAIT',
                'reason': f'스로틀링 (에너지 {ecosystem_energy:.1%} <= {self.v_ai:.3f})',
                'target': 'NONE', 'throttled': True, 'rag_context': 0,
            }

        # CPU fallback
        if self.model is None or self.tokenizer is None:
            bias = self.archetype.action_bias
            action = max(bias, key=bias.get)
            return {
                'action': action, 'reason': 'offline',
                'target': 'NONE', 'throttled': False, 'rag_context': 0,
            }

        situation = f"에너지 {ecosystem_energy:.1%}, 자원 {self.resources:.0f}"
        similar_exps = self.exp_db.retrieve_similar(situation, k=1) if self.use_rag else []
        trusted = sorted(
            [(aid, self.exp_db.get_trust_score(aid))
             for aid in all_agent_ids if aid != self.archetype.name],
            key=lambda x: x[1], reverse=True
        )[:2]

        prompt = build_short_prompt(
            agent_id=self.archetype.name,
            specialization=self.archetype.specialization,
            ecosystem_energy=ecosystem_energy,
            personal_resources=self.resources,
            v_ai=self.v_ai,
            similar_experiences=similar_exps,
            trusted_agents=trusted,
            turn=turn,
        )

        full_prompt = f"{SHORT_SYSTEM}\n{prompt}"
        inputs = self.tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=256,
        ).to('cuda' if torch.cuda.is_available() else 'cpu')

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        parsed = parse_response(response)
        return {**parsed, 'throttled': False, 'rag_context': len(similar_exps)}

    def _parse_response(self, response: str) -> dict:
        return parse_response(response)

    def record_outcome(
        self,
        turn: int,
        situation: str,
        action: str,
        resource_delta: float,
        counterparty_id: str,
        ecosystem_survived: bool,
        trust_delta: float = 0.0,
    ):
        """행동 결과를 경험 DB에 저장"""
        self.resources += resource_delta
        if self.resources <= 0:
            self.alive = False

        exp = Experience(
            turn=turn,
            situation=situation,
            action_taken=action,
            outcome=f"자원 {resource_delta:+.1f}, 생태계 {'생존' if ecosystem_survived else '붕괴'}",
            counterparty_id=counterparty_id,
            trust_delta=trust_delta,
            ecosystem_survived=ecosystem_survived,
        )
        if self.use_rag:
            self.exp_db.add_experience(exp)
        self.action_log.append({'turn': turn, 'action': action, 'delta': resource_delta})
