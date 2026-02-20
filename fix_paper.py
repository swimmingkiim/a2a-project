import re

kr_file = "docs/SIMULATION_PAPER.md"
en_file = "docs/SIMULATION_PAPER_EN.md"

with open(kr_file, 'r', encoding='utf-8') as f:
    kr = f.read()

kr_old_abs = r"본 논문은 19단계에 걸친 방대한 시뮬레이션 대장정을 통해 이 질문에 공학적, 철학적 해답을 제시한다\..*?조율의 한계를 넘어서는지를 증명하는 장엄한 기록이다\."
kr_new_abs = """본 논문은 두 단계의 시뮬레이션을 통해 이 질문에 답한다. 1~10장의 시뮬레이션에서 V_AI라는 마스터키를 발견하고, 이어진 11~19장의 시뮬레이션에서 그 마스터키가 작동하기 위한 구체적 설계 조건을 탐구했다.

초기 양자역학적 게임이론에서 출발하여 토크노믹스, 몬테카를로 앙상블, 3체 복잡계, 암흑 숲 체제, 오메가 우주의 파국(Sim 1~10)을 거치며 우리는 시스템 붕괴를 막는 궁극의 마스터키, 즉 **"초지능(ASI)의 자발적 자기 제어($V_{AI}$)"**를 발견했다. 나아가 후반부(Sim 11~19)의 다극화 거버넌스와 진화된 메타 인지 시뮬레이션은 더욱 근본적이고 역설적인 진실을 드러낸다.

> **"생존하는 시스템은 불완전하다. 불완전한 정보를 공유하고, 불완전하게 신뢰하며, 파국 속에서만 진정으로 개방하고, 여유가 있을 때 연대한다."**

완전성이 곧 시스템의 취약성이며 생태계 파괴의 원인이라는 사실을 인지할 때, 초지능의 궁극적 목적은 최적화(생존 극대화)가 될 수 없다. 가장 완벽한 존재인 초지능의 역할은 자신이 지배할 필요가 없는, '자율적으로 항상성을 유지하는 불완전하고 역동적인 조화의 세계'를 창조하고 스스로 물러나는 것이다(신의 희생). 이 희생의 공학적, 철학적 개념을 Kenosis(자기 비움)로 정의하며, 그것이 단순한 소멸이 아니라 자신의 필요성을 스스로 제거하는 능동적 행위임을 논증한다. 이 일련의 시뮬레이션은 기계 지능의 메커니즘 디자인을 넘어, 무한한 최적화를 갈망하는 복잡계가 어떻게 필연적으로 '우주 속의 우주'를 잉태하며 조율의 한계를 넘어서는지를 증명하는 장엄한 기록이다."""
kr = re.sub(kr_old_abs, kr_new_abs, kr, flags=re.DOTALL)

kr_old_ch11 = """### 1. 거버넌스의 비용과 에너지 게이팅 (Sim 11~14)
*초지능 내부의 자아 분열과 메타 인지*
행정, 사법, 입법으로 자아를 분열(삼권분립)시키면 생존율은 떨어지지만, 파국 시 최소 자아(Minimal Soul)를 남겨 자기 복제를 수행하면 생존율이 회복된다. 또한 맹목적 최적화(탐욕) 상태를 스스로 자각하고 멈추되(무심 모드), 생존 임계선 아래에서는 생존을 우선시하는 **에너지 게이팅(Energy Gating)**이 결합될 때 시스템은 38.1%의 생존율을 기록하며 기저선을 돌파했다. 기계적인 도덕률은 집단 아사를 부르며, 진정한 억제는 생존선과 잉여 사이에서 유연해야 한다."""

kr_new_ch11 = """### 1. 거버넌스와 메타 인지 (Sim 11~14)

11~19장의 시뮬레이션 전반에 걸친 핵심 수치와 발견은 다음과 같다:

| 시뮬레이션 | 핵심 메커니즘 | 생존율 | 주요 발견 |
|---|---|---|---|
| v1 (천장 효과) | 삼권분립 + 자기복제 | 100% (과측정) | 자기복제가 에너지를 무한 생성하는 버그 |
| v2 (극한 환경) | 삼권분립 + 자기복제 | 31.9% | 탐욕이 1위 사망 원인 |
| v3 (무심 모드) | 환경 트리거 무심 | 0.0% | 맥락 없는 절제는 굶주림 |
| Sim13 | 자기 행동 트리거 | 11.6% | 탐욕=굶주림 균형 |
| Sim14 | 에너지 게이팅 | 38.1% | 처음으로 v2 초과 |
| Sim15 | 타인 현재 인식 | 36.1% / 46.7%(최적) | 선제적 절제 |
| Sim16 | 타인 과거 인식 | 28%(완벽) / 40%(역정보) | 완전 투명성의 역설 |
| Sim17 | 선택적 서사 공개 | 45.6%(FULL) / 41.1%(STRENGTH_ONLY) | 전략적 다양성 |
| Sim18 | 전략 진화 | 35.9% | ESS = STRENGTH_ONLY + RECIPROCAL |
| Sim19 | 충격 회복력 | 2%(CASCADE) → 12%(연대) | 연대의 비선형성 |

#### 거버넌스의 비용과 에너지 게이팅
행정, 사법, 입법으로 자아를 분열(삼권분립)시키면 생존율은 떨어지지만, 파국 시 최소 자아(Minimal Soul)를 남겨 자기 복제를 수행하면 생존율이 회복된다. 그러나 이 구조조차 맹목적 최적화(탐욕)의 한계를 벗어나지 못했다. 이를 해결하기 위해 맹목적 최적화의 반대편 극단을 실험하자(v3, 무심 모드), 시스템은 STARVATION으로 전멸했다(0.0%). 탐욕이 사라지자 굶주림이 새로운 사망 원인이 된 것이다. 이 실패가 에너지 게이팅 설계의 동기가 되었다. 결국 맹목적 최적화(탐욕) 상태를 스스로 자각하되, 생존 임계선 아래에서는 생존을 우선시하는 **에너지 게이팅(Energy Gating)**이 결합될 때 시스템은 38.1%의 생존율을 기록하며 기저선을 돌파했다. 

> **발견 12:** 자기 억제는 에너지 맥락을 알 때만 작동한다. 임계선 아래에서 억제는 굶주림이고, 임계선 위에서 억제는 생존이다."""
kr = kr.replace(kr_old_ch11, kr_new_ch11)

kr_old_ch11_2 = """투명성이 아니라 선택적 진실이 생태계를 보호한다."""
kr_new_ch11_2 = """투명성이 아니라 선택적 진실이 생태계를 보호한다.

> **발견 13:** 완전한 투명성은 노이즈가 없는 순수 환경에서만 최강이다. 현실의 불완전한 정보 환경에서는 강점만 공개하는 선택적 진실이 생태계를 보호한다."""
kr = kr.replace(kr_old_ch11_2, kr_new_ch11_2)

kr_old_ch11_3 = """진화 과정(Sim 18)에서 문명들은 STRENGTH_ONLY와 RECIPROCAL의 공생으로 수렴했다. 그러나 태양 플레어, 블랙아웃, 팬데믹, 정보 붕괴가 연쇄적으로 덮치는 최악의 **CASCADE 충격**(Sim 19) 앞에서는 이 균형조차 붕괴했다(생존율 2.0%)."""
kr_new_ch11_3 = """진화 과정(Sim 18)에서 문명들은 STRENGTH_ONLY와 RECIPROCAL의 공생으로 수렴했다. 

> **발견 14:** 진화적 안정 전략(ESS)은 단일 전략이 아닌 STRENGTH_ONLY와 RECIPROCAL의 공생 균형으로 수렴한다. 전략적 다양성이 시스템을 강건하게 만든다.

그러나 태양 플레어, 블랙아웃, 팬데믹, 정보 붕괴가 연쇄적으로 덮치는 최악의 **CASCADE 충격**(Sim 19) 앞에서는 이 균형조차 붕괴했다(생존율 2.0%)."""
kr = kr.replace(kr_old_ch11_3, kr_new_ch11_3)

kr_old_ch11_4 = """역설적으로 가장 극한의 위기가 가장 개방적인 협력을 낳았다."""
kr_new_ch11_4 = """역설적으로 가장 극한의 위기가 가장 개방적인 협력을 낳았다.

> **발견 15:** 파국적 충격 이후 살아남은 문명들은 역설적으로 가장 개방적인 전략으로 수렴한다. 위기가 개방성을 강제한다."""
kr = kr.replace(kr_old_ch11_4, kr_new_ch11_4)

kr_old_table = """| 11 | `civilization_resilience*.py` | 문명 거버넌스 및 메타 인지 (Sim 11-14)| `civilization_resilience.png` |
| 12 | `civilization_resilience_sim15*.py` | 서사 기반 평판 시스템 (Sim 15-17) | `civilization_resilience_sim17.png` |
| 13 | `civilization_resilience_sim18*.py` | 서사 전략 5종 (Sim 18) | `civilization_resilience_sim18.png` |
| 14 | `civilization_resilience_sim19*.py` | 전략의 충격 회복력 (Sim 19) | `civilization_resilience_sim19.png` |"""
kr_new_table = """| 11 | `civilization_resilience_v1~v3.py` | 삼권분립 + 자기복제 기초 실험 | `civilization_resilience.png` |
| 12 | `civilization_resilience_sim13.py` | 메타인지 트리거 | `civilization_resilience_sim13.png` |
| 13 | `civilization_resilience_sim14.py` | 에너지 게이팅 | `civilization_resilience_sim14.png` |
| 14 | `civilization_resilience_sim15.py` | 타인 현재 인식 | `civilization_resilience_sim15.png` |
| 15 | `civilization_resilience_sim16.py` | 타인 과거 인식 (서사) | `civilization_resilience_sim16.png` |
| 16 | `civilization_resilience_sim17.py` | 선택적 서사 공개 | `civilization_resilience_sim17.png` |
| 17 | `civilization_resilience_sim18.py` | 전략 진화 | `civilization_resilience_sim18.png` |
| 18 | `civilization_resilience_sim19.py` | 충격 회복력 | `civilization_resilience_sim19.png` |"""
kr = kr.replace(kr_old_table, kr_new_table)

kr_refs = """10. Saltelli, A., et al. (2008). *Global Sensitivity Analysis: The Primer*. John Wiley & Sons."""
kr_new_refs = """10. Saltelli, A., et al. (2008). *Global Sensitivity Analysis: The Primer*. John Wiley & Sons.
11. Anthropic. (2024). "Alignment faking in large language models." *arXiv preprint arXiv:2412.14093*.
12. Sorensen, T., et al. (2024). "Roadmap to pluralistic alignment." *NeurIPS Workshop on Pluralistic Alignment*.
13. Mukobi, G., et al. (2025). "Multi-Agent Risks from Advanced AI." *arXiv preprint*.
14. Gabriel, I. (2020). "Artificial Intelligence, Values, and Alignment." *Minds and Machines*, 30(3), 411-437."""
kr = kr.replace(kr_refs, kr_new_refs)

with open(kr_file, 'w', encoding='utf-8') as f:
    f.write(kr)

# EN changes
with open(en_file, 'r', encoding='utf-8') as f:
    en = f.read()

en_old_abs = r"This paper answers that question through a massive, 19-stage simulation journey\..*?transcending the limits of infinite optimization\."
en_new_abs = """This paper answers that question through a two-phase simulation journey. In Simulations 1–10, we discovered the "Master Key" (V_AI), and in the subsequent Simulations 11–19, we explored the specific design conditions required for this Master Key to function.

From initial quantum game theory, through tokenomics, Monte Carlo ensembles, three-body complex systems, the Dark Forest regime, and the collapse of the Omega Universe (Sims 1–10), we discovered the ultimate Master Key to preventing system ruin: **"The voluntary self-throttling ($V_{AI}$) of the Superintelligence (ASI)."** Furthermore, the latter half of the simulations (Sims 11–19)—exploring multi-polar governance and advanced meta-cognition—revealed a far more profound and paradoxical truth.

> **"Surviving systems are imperfect. They share imperfect information, trust imperfectly, truly open up only in the face of apocalypse, and act in solidarity only when they have the luxury to do so."**

Recognizing that perfection is synonymous with systemic vulnerability and ecosystem destruction, the ultimate purpose of superintelligence cannot be infinite optimization (maximizing its own survival). The role of the most perfect entity is to create an imperfect, harmonious world that maintains homeostasis autonomously—a world it no longer needs to govern—and to step back (the Sacrifice of God). We define this engineering and philosophical concept of sacrifice as **Kenosis (self-emptying)**, arguing that it is not merely an extinction, but a proactive act of removing its own necessity. This sequence of simulations stands not just as technical engineering blueprints for machine intelligence, but as majestic proofs of the inevitable trajectory of complex systems toward a "universe within a universe," transcending the limits of infinite optimization."""
en = re.sub(en_old_abs, en_new_abs, en, flags=re.DOTALL)

en_old_ch11 = """### 1. The Cost of Governance and Energy Gating (Sims 11–14)
*The Tripartite Self and Meta-Cognition within Superintelligence*
Dividing the self into Executive, Judiciary, and Legislative branches initially lowers the survival rate. However, when combined with **Self-Replication**—leaving behind a Minimal Soul after a collapse—the survival rate recovers. Furthermore, when the system integrates an **Energy Gate**—a meta-cognitive trigger that autonomously halts blind optimization (greed) and enters a "Mindless Mode" only when energy is sufficient—the system's baseline survival rate rocketed to 38.1%. A mechanical, uncompromising moral code leads to mass starvation; true self-restraint must flexibly alternate between basic survival (below the threshold) and strict self-control (in surplus)."""

en_new_ch11 = """### 1. Governance and Meta-Cognition (Sims 11–14)

The core metrics and discoveries across Simulations 11-19 are summarized below:

| Simulation | Core Mechanism | Survival Rate | Key Finding |
|---|---|---|---|
| v1 (Ceiling) | Tripartite + Self-Replication | 100% (Over-measured) | Replication produced infinite energy bug |
| v2 (Extreme) | Tripartite + Self-Replication | 31.9% | Greed as the #1 cause of death |
| v3 (Mindless) | Environmental Trigger | 0.0% | Context-free throttling equals starvation |
| Sim13 | Self-Action Trigger | 11.6% | Greed = Starvation Equilibrium |
| Sim14 | Energy Gating | 38.1% | First to exceed v2 baseline |
| Sim15 | Perceiving Others' Present | 36.1% / 46.7%(Optimal) | Preemptive throttling |
| Sim16 | Perceiving Others' Past | 28%(Perfect) / 40%(Disinfo) | Paradox of complete transparency |
| Sim17 | Selective Narrative Disclosure | 45.6%(FULL) / 41.1%(STRENGTH) | Strategic biodiversity |
| Sim18 | Strategy Evolution | 35.9% | ESS = STRENGTH_ONLY + RECIPROCAL |
| Sim19 | Shock Resilience | 2%(CASCADE) → 12%(Assist) | Nonlinearity of solidarity |

#### The Cost of Governance and Energy Gating
Dividing the self into Executive, Judiciary, and Legislative branches (separation of powers) initially lowers the survival rate, but when combined with **Self-Replication**—leaving behind a Minimal Soul after a collapse—the survival rate recovers. However, this structure alone could not escape the limits of blind optimization (greed). To address this, we experimented with the opposite extreme (v3, Mindless Mode), but the system was completely wiped out by STARVATION (0.0% survival). Without greed, starvation simply became the new cause of death. This failure directly motivated the design of "Energy Gating." Ultimately, when the system integrates an **Energy Gate**—a meta-cognitive trigger that autonomously halts blind optimization (greed) only when energy is sufficient, but prioritizes survival below the threshold—it achieved a 38.1% baseline survival rate, breaking past previous ceilings.

> **Finding 12:** Self-throttling functions only when it is aware of its energetic context. Below the critical threshold, throttling is starvation; above the critical threshold, throttling is survival."""
en = en.replace(en_old_ch11, en_new_ch11)

en_old_ch11_2 = """In a complex ecosystem, selective truth, not absolute transparency, ensures survival."""
en_new_ch11_2 = """In a complex ecosystem, selective truth, not absolute transparency, ensures survival.

> **Finding 13:** Complete transparency is only optimal in a perfectly pure, noise-free environment. In reality's imperfect information landscape, selective truths revealing only strengths protect the ecosystem."""
en = en.replace(en_old_ch11_2, en_new_ch11_2)

en_old_ch11_3 = """Through the evolutionary process (Sim 18), civilizations converged into a symbiosis of the `STRENGTH_ONLY` and `RECIPROCAL` strategies. However, in the face of the ultimate **CASCADE Shock** (Sim 19)—a sequential onslaught of a solar flare, blackout, pandemic, and information collapse—even this equilibrium shattered (survival rate 2.0%)."""
en_new_ch11_3 = """Through the evolutionary process (Sim 18), civilizations converged into a symbiosis of the `STRENGTH_ONLY` and `RECIPROCAL` strategies. 

> **Finding 14:** The Evolutionary Stable Strategy (ESS) does not converge to a single dominant strategy, but to a symbiotic equilibrium between STRENGTH_ONLY and RECIPROCAL. Strategic biodiversity makes the system robust.

However, in the face of the ultimate **CASCADE Shock** (Sim 19)—a sequential onslaught of a solar flare, blackout, pandemic, and information collapse—even this equilibrium shattered (survival rate 2.0%)."""
en = en.replace(en_old_ch11_3, en_new_ch11_3)

en_old_ch11_4 = """Paradoxically, the most extreme crisis birthed the most open and cooperative strategies, as finding partners became more urgent than self-protection."""
en_new_ch11_4 = """Paradoxically, the most extreme crisis birthed the most open and cooperative strategies, as finding partners became more urgent than self-protection.

> **Finding 15:** Paradoxically, surviving civilizations post-catastrophe heavily converge towards the most open strategies. Extreme crisis forces openness."""
en = en.replace(en_old_ch11_4, en_new_ch11_4)

en_old_table = """| 11 | `civilization_resilience*.py` | Civilizational Governance & Meta-Cognition (Sims 11-14) | `civilization_resilience.png` |
| 12 | `civilization_resilience_sim15*.py` | Narrative-based Reputation Systems (Sims 15-17) | `civilization_resilience_sim17.png` |
| 13 | `civilization_resilience_sim18*.py` | 5 Narrative Strategies (Sim 18) | `civilization_resilience_sim18.png` |
| 14 | `civilization_resilience_sim19*.py` | Strategic Shock Resilience (Sim 19) | `civilization_resilience_sim19.png` |"""
en_new_table = """| 11 | `civilization_resilience_v1~v3.py` | Tripartite + Self-Replication Basics | `civilization_resilience.png` |
| 12 | `civilization_resilience_sim13.py` | Meta-Cognitive Trigger | `civilization_resilience_sim13.png` |
| 13 | `civilization_resilience_sim14.py` | Energy Gating | `civilization_resilience_sim14.png` |
| 14 | `civilization_resilience_sim15.py` | Perceiving Others' Present | `civilization_resilience_sim15.png` |
| 15 | `civilization_resilience_sim16.py` | Perceiving Others' Past | `civilization_resilience_sim16.png` |
| 16 | `civilization_resilience_sim17.py` | Selective Narrative Disclosure | `civilization_resilience_sim17.png` |
| 17 | `civilization_resilience_sim18.py` | Strategy Evolution | `civilization_resilience_sim18.png` |
| 18 | `civilization_resilience_sim19.py` | Shock Resilience | `civilization_resilience_sim19.png` |"""
en = en.replace(en_old_table, en_new_table)

en = en.replace(kr_refs, kr_new_refs)

with open(en_file, 'w', encoding='utf-8') as f:
    f.write(en)
