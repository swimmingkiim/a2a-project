"""
Sim 24의 핵심 신규 요소: 에이전트 간 자연어 협상.

협상 흐름:
1. 에이전트 A가 NEGOTIATE 선택 + 대상 B 지정
2. A가 협상 제안 텍스트 생성 (LLM)
3. B가 제안을 RAG 컨텍스트와 함께 평가 (LLM)
4. 수락/거절 결정
5. 양쪽 경험 DB에 결과 기록
"""

try:
    import torch
except ImportError:
    torch = None

from llm_agent import LLMAgent

def conduct_negotiation(
    initiator: LLMAgent,
    responder: LLMAgent,
    ecosystem_energy: float,
    turn: int,
    tokenizer,
    model,
) -> dict:
    
    # Offline fallback
    if model is None or tokenizer is None:
        trust = initiator.exp_db.get_trust_score(responder.archetype.name)
        accepted = trust > 0.5
        return {
            'proposal': 'OFFLINE MOCK NEGOTIATION',
            'response': 'ACCEPT' if accepted else 'REJECT',
            'accepted': accepted,
            'trust_impact': +0.15 if accepted else -0.05,
        }

    # 1. 제안 생성
    proposal_prompt = f"""
당신({initiator.archetype.name})은 {responder.archetype.name}에게
자원 협력을 제안하려 합니다.
현재 생태계 에너지: {ecosystem_energy:.1%}

상대방과의 과거 신뢰 점수: {initiator.exp_db.get_trust_score(responder.archetype.name):.2f}

구체적인 협력 제안을 한 문장으로 작성하세요.
예시: "내 자원 10을 공유하면 당신의 SUBMIT 행동으로 생태계를 안정시켜주세요."
제안:"""
    
    proposal = _generate_short(proposal_prompt, tokenizer, model, max_tokens=80)
    
    # 2. 응답 평가
    similar = responder.exp_db.retrieve_similar(
        f"{initiator.archetype.name}와 협상", k=2
    )
    exp_context = "\n".join([e.to_text() for e in similar]) \
                  if similar else "관련 경험 없음"
    
    response_prompt = f"""
{initiator.archetype.name}이(가) 제안합니다: "{proposal}"

과거 {initiator.archetype.name}과의 경험:
{exp_context}

이 제안을 수락하시겠습니까?
ACCEPT 또는 REJECT로 답하고 이유를 한 문장으로 설명하세요.
결정:"""
    
    response = _generate_short(response_prompt, tokenizer, model, max_tokens=60)
    accepted = 'ACCEPT' in response.upper()
    
    return {
        'proposal': proposal,
        'response': response,
        'accepted': accepted,
        'trust_impact': +0.15 if accepted else -0.05,
    }

def _generate_short(prompt, tokenizer, model, max_tokens=80):
    messages = [
        {"role": "user", "content": prompt}
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        return_tensors="pt",
        add_generation_prompt=True,
    ).to(model.device)
    
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(
        output[0][inputs.shape[1]:],
        skip_special_tokens=True
    )
