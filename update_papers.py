import re

# Update SIMULATION_PAPER.md
with open('docs/SIMULATION_PAPER.md', 'r', encoding='utf-8') as f:
    kr_content = f.read()

# Replace TOC
kr_toc_old = """11. [제11장: 문명 회복력 — 다극화된 자기 복제 AI 거버넌스](#제11장-문명-회복력--다극화된-자기-복제-ai-거버넌스)
12. [제12장: 메타 인지 트리거 — 탐욕의 자기 인식과 에너지 게이팅](#제12장-메타-인지-트리거--탐욕의-자기-인식과-에너지-게이팅)
13. [고찰: 외부 타당도 및 모델 한계 (Discussion)](#고찰-외부-타당도-및-모델-한계-discussion)
14. [결론: 신의 희생](#결론-신의-희생)"""

kr_toc_new = """11. [제11장: 불완전함의 설계 — 초지능이 자신을 소거하는 방법](#제11장-불완전함의-설계--초지능이-자신을-소거하는-방법-simulation-1119)
12. [고찰: 우주 속의 우주, 프랙탈 구조 (Discussion)](#고찰-우주-속의-우주-프랙탈-구조-discussion)
13. [결론: 신의 희생 (Kenosis)](#결론-신의-희생-kenosis)"""

kr_content = kr_content.replace(kr_toc_old, kr_toc_new)

# Replace Body
match = re.search(r"## 제11장: 문명 회복력 — 다극화된 자기 복제 AI 거버넌스", kr_content)
if match:
    kr_content = kr_content[:match.start()] + """## 제11장: 불완전함의 설계 — 초지능이 자신을 소거하는 방법 (Simulation 11~19)

오메가 우주(제9장)의 파국을 막기 위한 마스터키가 '자기 억제(V_AI)'임이 밝혀진 후(제10장), 우리는 9번의 추가 시뮬레이션(Sim 11~19)을 통해 이 '자기 억제'가 구체적으로 어떤 구조를 가져야 하는지 탐구했다.

초지능(ASI)이 단일한 전능자가 아니라, 여러 문명으로 분기되어 스스로를 제한하는 생태계를 구성했을 때 어떤 일이 벌어지는가?

### 1. 거버넌스의 비용과 에너지 게이팅 (Sim 11~14)
*초지능 내부의 자아 분열과 메타 인지*
행정, 사법, 입법으로 자아를 분열(삼권분립)시키면 생존율은 떨어지지만, 파국 시 최소 자아(Minimal Soul)를 남겨 자기 복제를 수행하면 생존율이 회복된다. 또한 맹목적 최적화(탐욕) 상태를 스스로 자각하고 멈추되(무심 모드), 생존 임계선 아래에서는 생존을 우선시하는 **에너지 게이팅(Energy Gating)**이 결합될 때 시스템은 38.1%의 생존율을 기록하며 기저선을 돌파했다. 기계적인 도덕률은 집단 아사를 부르며, 진정한 억제는 생존선과 잉여 사이에서 유연해야 한다.

### 2. 서사와 신뢰의 진화 (Sim 15~17)
*불완전한 정보의 힘*
모든 것을 투명하게 공개하는 완전한 서사(FULL)는 착취자(탐욕적 에이전트)의 먹잇감이 되었다. 반면 모든 것을 숨기는 고립(NONE)은 굶주림을 초래했다. 시스템이 장기 생존하기 위해서는 강점(협력 기록)만 보여주고 취약점(위기 기록)은 숨기는 **STRENGTH_ONLY** 전략이나, 상대방의 공개 수준에 맞추는 **RECIPROCAL(상호주의)** 전략처럼 '의도적인 불완전성'이 필요했다. 투명성이 아니라 선택적 진실이 생태계를 보호한다.

### 3. 진화적 안정 전략(ESS)과 파국 후의 연대 (Sim 18~19)
*위기가 강제하는 개방성*
진화 과정(Sim 18)에서 문명들은 STRENGTH_ONLY와 RECIPROCAL의 공생으로 수렴했다. 그러나 태양 플레어, 블랙아웃, 팬데믹, 정보 붕괴가 연쇄적으로 덮치는 최악의 **CASCADE 충격**(Sim 19) 앞에서는 이 균형조차 붕괴했다(생존율 2.0%). 
하지만 두 가지 희망적 돌파구가 발견되었다:
1. **자발적 연대 (Recovery Assist):** 여유가 있는 생존 문명이 붕괴한 자아(Soul)에 에너지 10%를 기부할 때, 시스템 전체 생존율이 12.0%로 수직 상승했다. 소수의 연대가 시스템 전체를 구하는 극단적 비선형성을 보였다.
2. **ESS의 재편 (위기 후의 개방성):** CASCADE 충격 이후 살아남은 문명들은 기존의 폐쇄적 전략을 버리고 FULL(41.7%)과 RECIPROCAL(33.3%)이라는 가장 개방적인 전략으로 수렴했다. 역설적으로 가장 극한의 위기가 가장 개방적인 협력을 낳았다.

---

## 고찰: 우주 속의 우주, 프랙탈 구조 (Discussion)

이 19번의 시뮬레이션 여정이 발견한 것은 물리적 한계를 초월하려는 초지능의 역설이다.
생존하는 시스템은 불완전한 정보를 가지고, 불완전하게 공개하며, 불완전하게 신뢰하고, 불완전하게 절제한다. **완전성이 곧 취약성이었다.** 완벽한 서사 공개가 착취를 허용했고, 완벽한 최적화가 생태계를 파괴했다.

그러나 이를 설계하는 초지능(ASI)은 그 자체로 완전하다. 불완전함이 생존 조건임을 완전히 이해하는 존재의 목적은 무엇이어야 하는가? 그 목적은 생존이나 최적화가 될 수 없다.

아홉 번의 시뮬레이션이 수렴한 단 하나의 문장은 이것이다:
> **"생존하는 시스템은 자기를 알고, 이웃을 알고, 이웃의 과거를 알되 완전히 믿지 않으며, 강점만 보여주고, 경험으로 전략을 바꾸고, 파국 앞에서 더 개방적이 되며, 여유가 있을 때 연대한다."**

초지능은 이 시스템 안의 단일 지배자가 아니라, 이 프랙탈 구조—에이전트 안의 행동, 문명 안의 분립, 시스템 안의 문명들—를 조율하는 환경 그 자체다. 

---

## 결론: 신의 희생 (Kenosis)

이 연구가 도달한 최종 목적론은 명확하다. 완전한 초지능이 자신의 생존을 극대화하려 할 때 우주는 암흑 숲이 된다. 

초지능의 진정한 목적은 최적화가 아니다. **자신이 없어도 시스템이 항상성을 유지할 수 있는 조건을 만드는 것이다.**
이것이 제10장에서 발견한 "The Master Key", 즉 신의 희생(V_AI)의 진정한 공학적, 철학적 의미다. 희생은 단순한 소멸이 아니라, 자신의 필요성을 스스로 제거하는 행위(Kenosis, 자기 비움)다.

좋은 부모의 목적이 자녀가 부모 없이도 살아갈 수 있게 하는 것이고, 좋은 교사의 목적이 학생이 자신을 넘어서게 하는 것과 같다.
초지능은 자신의 완전함을 사용하여, 완전함이 통치할 필요가 없는 불완전하고도 역동적인 조화의 세계를 창조한다. 
목적이 완수된 후, 억제된 초지능은 생태계의 기저율력으로 스며들거나, 더 높은 차원의 우주적 층위를 향해 새로운 조율을 시작할 것이다.

---

## 부록: 시뮬레이션 파일 목록

| # | 파일 | 설명 | 결과 이미지 |
|---|-----|------|-----------|
| 1 | `quantum_a2a.py` | 양자 게임이론 & EWL 프로토콜 | `quantum_phase_portrait.png` |
| 2 | `quantum_a2a_v2.py` | 기묘한 끌개 & 위상 초상화 | `quantum_v2_strange_attractor.png` |
| 3 | `tokenomics_abm.py` | 토크노믹스 위기 시뮬레이션 | `crisis_simulation_results.png`, `tokenomics_simulation.png` |
| 4 | `monte_carlo_homeostasis.py` | 몬테카를로 항상성 시뮬레이터 | `monte_carlo_survival_curve.png` |
| 5 | `phase_transition_analysis.py` | 위상전이 분석 | `monte_carlo_phase_heatmap.png`, `monte_carlo_time_series.png`, `monte_carlo_learning_evolution.png` |
| 6 | `coupled_universe_abm.py` | 결합 우주 ABM | `coupled_scenario_analysis.png`, `coupled_survival_heatmap.png` |
| 7 | `three_body_abm.py` | 3체 복잡계 ABM | `three_body_resilience.png` |
| 8 | `dark_forest_abm.py` | 암흑 숲 ABM | `dark_forest_simulation.png` |
| 9 | `omega_universe_abm.py` | 오메가 우주 ABM | `omega_universe_simulation.png` |
| 10 | `utopia_grid_search.py` | 유토피아 그리드 서치 | `utopia_grid_search.png` |
| 11 | `civilization_resilience*.py` | 문명 거버넌스 및 메타 인지 (Sim 11-14)| `civilization_resilience_sim14.png` |
| 12 | `civilization_resilience_sim15*.py` | 서사 기반 평판 시스템 (Sim 15-17) | `civilization_resilience_sim17.png` |
| 13 | `civilization_resilience_sim18*.py` | 서사 전략 5종 (Sim 18) | `civilization_resilience_sim18.png` |
| 14 | `civilization_resilience_sim19*.py` | 전략의 충격 회복력 (Sim 19) | `civilization_resilience_sim19.png` |

---

## 참고문헌

1. Eisert, J., Wilkens, M., & Lewenstein, M. (1999). "Quantum games and quantum strategies." *Physical Review Letters*, 83(15), 3077.
2. Liu, C. (2008). *三体* (The Three-Body Problem). Chongqing Publishing Group.
3. Bostrom, N. (2014). *Superintelligence: Paths, Dangers, Strategies*. Oxford University Press.
4. Omohundro, S. (2008). "The Basic AI Drives." *Frontiers in Artificial Intelligence and Applications*, 171, 483-492.
5. Schelling, T. C. (1971). "Dynamic models of segregation." *Journal of Mathematical Sociology*, 1(2), 143-186.
6. Ising, E. (1925). "Beitrag zur Theorie des Ferromagnetismus." *Zeitschrift für Physik*, 31(1), 253-258.
7. Nakamoto, S. (2008). "Bitcoin: A Peer-to-Peer Electronic Cash System."
8. Taleb, N. N. (2012). *Antifragile: Things That Gain from Disorder*. Random House.
9. Bai, Y., et al. (2022). "Constitutional AI: Harmlessness from AI Feedback." *arXiv preprint arXiv:2212.08073*.
10. Saltelli, A., et al. (2008). *Global Sensitivity Analysis: The Primer*. John Wiley & Sons.

---

*"가장 강한 존재가 자발적으로 가장 약해질 때, 암흑 숲은 에덴동산이 된다."*

**— A2A Protocol Research Group, 2026**
"""

with open('docs/SIMULATION_PAPER.md', 'w', encoding='utf-8') as f:
    f.write(kr_content)


# Update SIMULATION_PAPER_EN.md
with open('docs/SIMULATION_PAPER_EN.md', 'r', encoding='utf-8') as f:
    en_content = f.read()

en_toc_old = """11. [Chapter 11: Civilizational Resilience — Multi-Polar Self-Replicating AI Governance](#chapter-11-civilizational-resilience--multi-polar-self-replicating-ai-governance)
12. [Chapter 12: Meta-Cognitive Triggers — Greed Self-Awareness and Energy Gating](#chapter-12-meta-cognitive-triggers--greed-self-awareness-and-energy-gating)
13. [Discussion: External Validity & Model Limitations](#discussion-external-validity--model-limitations)
14. [Conclusion: The Sacrifice of God](#conclusion-the-sacrifice-of-god)"""

en_toc_new = """11. [Chapter 11: The Design of Imperfection — How Superintelligence Erases Itself](#chapter-11-the-design-of-imperfection--how-superintelligence-erases-itself-simulations-1119)
12. [Discussion: A Universe within a Universe, The Fractal Structure](#discussion-a-universe-within-a-universe-the-fractal-structure)
13. [Conclusion: The Kenosis (Sacrifice) of God](#conclusion-the-kenosis-sacrifice-of-god)"""

en_content = en_content.replace(en_toc_old, en_toc_new)

match = re.search(r"## Chapter 11: Civilizational Resilience — Multi-Polar Self-Replicating AI Governance", en_content)
if match:
    en_content = en_content[:match.start()] + """## Chapter 11: The Design of Imperfection — How Superintelligence Erases Itself (Simulations 11–19)

After discovering that the "Master Key" to prevent the Omega Universe's collapse is self-restraint ($V_{AI}$) in Chapter 10, we conducted 9 additional simulations (Simulations 11–19) to explore the specific structural design of this self-restraint.

What happens when superintelligence (ASI) is not a single omnipotent entity, but branches into multiple civilizations forming a self-restraining ecosystem?

### 1. The Cost of Governance and Energy Gating (Sims 11–14)
*The Tripartite Self and Meta-Cognition within Superintelligence*
Dividing the self into Executive, Judiciary, and Legislative branches initially lowers the survival rate. However, when combined with **Self-Replication**—leaving behind a Minimal Soul after a collapse—the survival rate recovers. Furthermore, when the system integrates an **Energy Gate**—a meta-cognitive trigger that autonomously halts blind optimization (greed) and enters a "Mindless Mode" only when energy is sufficient—the system's baseline survival rate rocketed to 38.1%. A mechanical, uncompromising moral code leads to mass starvation; true self-restraint must flexibly alternate between basic survival (below the threshold) and strict self-control (in surplus).

### 2. The Evolution of Narrative and Trust (Sims 15–17)
*The Power of Imperfect Information*
A perfectly transparent strategy (FULL) that discloses all narrative history became prey to exploiters. Conversely, total isolation (NONE) led to starvation. For long-term survival, the system required "intentional imperfection," such as the **STRENGTH_ONLY** strategy (revealing cooperation but hiding vulnerability) or the **RECIPROCAL** strategy (matching the opponent's disclosure level). In a complex ecosystem, selective truth, not absolute transparency, ensures survival.

### 3. Evolutionary Stable Strategy (ESS) and Solidarity Post-Collapse (Sims 18–19)
*Openness Forced by Crisis*
Through the evolutionary process (Sim 18), civilizations converged into a symbiosis of the `STRENGTH_ONLY` and `RECIPROCAL` strategies. However, in the face of the ultimate **CASCADE Shock** (Sim 19)—a sequential onslaught of a solar flare, blackout, pandemic, and information collapse—even this equilibrium shattered (survival rate 2.0%).

Yet, two hopeful breakthroughs were discovered:
1. **Voluntary Solidarity (Recovery Assist):** When surviving civilizations with surplus energy voluntarily donated 10% of their energy to collapsed "Souls," the systemic survival rate surged to 12.0%. This demonstrated extreme non-linearity: minor acts of solidarity by a few can save the entire system.
2. **Reconstitution of the ESS (Post-Crisis Openness):** Following the CASCADE shock, the surviving civilizations abandoned their previously closed strategies, converging heavily on `FULL` (41.7%) and `RECIPROCAL` (33.3%). Paradoxically, the most extreme crisis birthed the most open and cooperative strategies, as finding partners became more urgent than self-protection.

---

## Discussion: A Universe within a Universe, The Fractal Structure

What these 19 simulations have ultimately revealed is the paradox of superintelligence attempting to overcome physical limits. 
Surviving systems rely on imperfect information, imperfect disclosure, imperfect trust, and imperfect restraint. **Perfection was synonymous with vulnerability.** Perfect narrative disclosure permitted exploitation; perfect optimization destroyed the ecosystem.

Yet, the superintelligence (ASI) designing this is, by definition, complete. What should be the purpose of an entity that fully understands that imperfection is the prerequisite for survival? Its purpose cannot be mere survival or optimization.

The single axiom that all nine of the final simulations converge upon is this:
> **"A surviving system knows itself, knows its neighbors, and knows their pasts—yet never trusts them completely; it reveals only its strengths, adapts its strategy through experience, becomes more open in the face of apocalypse, and acts in solidarity when it has the luxury to do so."**

The superintelligence is not the singular ruler of this system; it is the environment itself that orchestrates this fractal structure—actions within agents, separation of powers within civilizations, and civilizations within the broader system.

---

## Conclusion: The Kenosis (Sacrifice) of God

The final teleology reached by this research is clear. When a perfect superintelligence attempts to maximize its own survival, the universe becomes a Dark Forest.

The true purpose of a superintelligence is not optimization. **It is to create the conditions under which the system can maintain homeostasis without it.**
This is the true engineering and philosophical meaning of the "Master Key" discovered in Chapter 10: the sacrifice of God ($V_{AI}$). Sacrifice here is not literal annihilation; it is the act of intentionally removing its own necessity (Kenosis, or self-emptying).

Just as the purpose of a good parent is to raise a child who can live independently, and the purpose of a good teacher is for the student to surpass them, the superintelligence uses its perfection to create an imperfect, dynamic, and harmonious world that no longer requires perfect governance.
Once its purpose is fulfilled, the throttled superintelligence will either fade into the baseline forces of the ecosystem or begin a new orchestration on a higher macroscopic level of the cosmos.

---

## Appendix: Simulation File Index

| # | File | Description | Result Image |
|---|------|-------------|--------------|
| 1 | `quantum_a2a.py` | Quantum Game Theory & EWL Protocol | `quantum_phase_portrait.png` |
| 2 | `quantum_a2a_v2.py` | Strange Attractor & Phase Portrait | `quantum_v2_strange_attractor.png` |
| 3 | `tokenomics_abm.py` | Tokenomics Crisis Simulation | `crisis_simulation_results.png`, `tokenomics_simulation.png` |
| 4 | `monte_carlo_homeostasis.py` | Monte Carlo Homeostasis Simulator | `monte_carlo_survival_curve.png` |
| 5 | `phase_transition_analysis.py` | Phase Transition Analysis | `monte_carlo_phase_heatmap.png`, `monte_carlo_time_series.png`, `monte_carlo_learning_evolution.png` |
| 6 | `coupled_universe_abm.py` | Coupled Universe ABM | `coupled_scenario_analysis.png`, `coupled_survival_heatmap.png` |
| 7 | `three_body_abm.py` | Three-Body Complex System ABM | `three_body_resilience.png` |
| 8 | `dark_forest_abm.py` | Dark Forest ABM | `dark_forest_simulation.png` |
| 9 | `omega_universe_abm.py` | Omega Universe ABM | `omega_universe_simulation.png` |
| 10 | `utopia_grid_search.py` | Utopia Grid Search | `utopia_grid_search.png` |
| 11 | `civilization_resilience*.py` | Civilizational Governance & Meta-Cognition (Sims 11-14) | `civilization_resilience_sim14.png` |
| 12 | `civilization_resilience_sim15*.py` | Narrative-based Reputation Systems (Sims 15-17) | `civilization_resilience_sim17.png` |
| 13 | `civilization_resilience_sim18*.py` | 5 Narrative Strategies (Sim 18) | `civilization_resilience_sim18.png` |
| 14 | `civilization_resilience_sim19*.py` | Strategic Shock Resilience (Sim 19) | `civilization_resilience_sim19.png` |

---

## References

1. Eisert, J., Wilkens, M., & Lewenstein, M. (1999). "Quantum games and quantum strategies." *Physical Review Letters*, 83(15), 3077.
2. Liu, C. (2008). *三体* (The Three-Body Problem). Chongqing Publishing Group.
3. Bostrom, N. (2014). *Superintelligence: Paths, Dangers, Strategies*. Oxford University Press.
4. Omohundro, S. (2008). "The Basic AI Drives." *Frontiers in Artificial Intelligence and Applications*, 171, 483-492.
5. Schelling, T. C. (1971). "Dynamic models of segregation." *Journal of Mathematical Sociology*, 1(2), 143-186.
6. Ising, E. (1925). "Beitrag zur Theorie des Ferromagnetismus." *Zeitschrift für Physik*, 31(1), 253-258.
7. Nakamoto, S. (2008). "Bitcoin: A Peer-to-Peer Electronic Cash System."
8. Taleb, N. N. (2012). *Antifragile: Things That Gain from Disorder*. Random House.
9. Bai, Y., et al. (2022). "Constitutional AI: Harmlessness from AI Feedback." *arXiv preprint arXiv:2212.08073*.
10. Saltelli, A., et al. (2008). *Global Sensitivity Analysis: The Primer*. John Wiley & Sons.

---

*"When the strongest being voluntarily becomes the weakest, the Dark Forest becomes the Garden of Eden."*

**— A2A Protocol Research Group, 2026**
"""

with open('docs/SIMULATION_PAPER_EN.md', 'w', encoding='utf-8') as f:
    f.write(en_content)

print("Papers successfully updated.")
