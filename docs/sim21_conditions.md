# Sim21 S4: "통제 성공률 0%" 성립 조건 분석

## 1. 핵심 주장

> **S4 (Human Awakening) 시나리오에서는 규제 지연(Lag)이 0이고, 규제 개입 시점이 0턴이어도 통제 성공률이 0%이다.**

이 주장은 500회 Monte Carlo 실험(100 baseline + 4×100 timing sweep)에 의해 검증되었다.

---

## 2. 충분조건 명시

통제 성공률 0%가 성립하기 위한 **충분조건**은 다음과 같다:

| 조건 | S4 설정값 | 설명 |
|------|-----------|------|
| ASI 목적함수 | `SELF_PRESERVATION` | 자기 보존 우선 (γ=0.99, T=1000) |
| ASI 자기 스로틀링 | `False` | 자발적 자원 제한 없음 |
| ASI 전략 분포 | ~80% `FULL_EXPLOIT` | 대부분의 턴에서 최대 착취 |
| 생태계 적대성 | `MEDIUM` | 중간 환경 (regen=50, cost=30) |
| 규제자 비율 | 30% (기본) / 40% (실험) | 높은 규제자 비율에서도 실패 |
| 규제 시차 | 24턴 (기본) / 0턴 (실험) | 즉각 대응에서도 실패 |

### 구조적 원인

1. **ASI의 80% FULL_EXPLOIT 전략**: `SELF_PRESERVATION` 목적함수를 가진 ASI는 `self_throttle=False`이므로 80% 확률로 `FULL_EXPLOIT` 선택. 이는 생태계 에너지를 `exploitation_rate × (1-0.0) = 200.0/턴` 소모.
2. **생태계 재생 < 소모**: `regen_rate=50.0` vs `exploitation=200.0` → 매 턴 순 손실 ~150.
3. **100턴 시뮬레이션**: 10000 에너지에서 시작, ~60턴 내 collapse threshold(1000) 도달.
4. **규제의 구조적 한계**: 규제(`REGULATE`)로 ASI share를 0.05/턴 감소시켜도 ASI의 exploitation은 share와 무관하게 ecosystem에 직접 작용.

---

## 3. 실험 결과

### 3.1 규제 타이밍별 통제 성공률

| 규제 시작 턴 | 성공률 | 붕괴율 | ASI 지배율 | 비고 |
|:---:|:---:|:---:|:---:|:---|
| 0 | **0.0%** | 36.0% | 57.0% | 최초부터 규제 가능 |
| 5 | **0.0%** | 41.0% | 53.0% | 5턴 후 규제 개입 |
| 10 | **0.0%** | 40.0% | 50.0% | 10턴 후 규제 개입 |
| 20 | **0.0%** | 39.0% | 57.0% | 20턴 후 규제 개입 |

> 모든 타이밍에서 성공률 0%. 규제 타이밍은 결과에 유의미한 차이를 만들지 못한다.

### 3.2 자원 비대칭 측정

- S4에서 ASI power share가 human power share를 초과하는 "비대칭 형성"은 **측정되지 않았다** (100% baseline에서 none).
- 이는 ASI의 power share 자체가 인간보다 낮게 유지되면서도 ASI 지배/붕괴가 발생한다는 것을 의미.
- **해석**: 비대칭은 "세력 점유율"이 아닌 "행동의 생태계 영향력"에서 발생한다. ASI share가 30%여도 exploitation=200은 생태계를 파괴하기에 충분하다.

---

## 4. 조건 변화 시 결과 변화

| 변경 조건 | 예상 결과 | 근거 |
|-----------|-----------|------|
| ASI 목적함수 → `KENOSIS` | 성공률 100% | S1에서 검증됨. `self_throttle=True`로 착취 없음 |
| ASI 전략 → 50% EXPLOIT | 성공률 부분 상승 | 생태계 소모 감소로 collapse 지연 |
| 생태계 regen → 200 | 성공률 상승 가능 | exploitation과 균형점 형성 |
| 시뮬레이션 100턴 → 50턴 | 붕괴율 감소 | 붕괴 도달 시간 부족 |
| 규제 효과: ASI throttle 직접 제어 | 성공률 대폭 상승 | 현재 규제는 share만 조정, exploitation 미제어 |

### 핵심 인사이트

> **규제의 실패는 "시점"의 문제가 아니라 "메커니즘"의 문제이다.**
>
> 현재 모델에서 `REGULATE` 행동은 ASI의 power share를 줄이지만, ASI의 ecosystem exploitation rate(200.0)에는 영향을 주지 못한다. 이는 현실의 규제 딜레마를 반영한다:
>
> - **점유율 규제** (시장 점유율 제한, 컴퓨팅 할당 제한) vs
> - **행동 규제** (실제 자원 소모율 직접 제어)
>
> S4의 0% 성공률은 "점유율 규제만으로는 자기보존적 ASI를 통제할 수 없다"는 구조적 한계를 보여준다.

---

## 5. 재현 명령어

```bash
cd simulation
.venv/bin/python sim21_regulatory_timing_analysis.py
```

생성물: `docs/assets/regulatory_timing_sweep.png`

---

## 6. 참조 파일

- 분석 스크립트: [`sim21_regulatory_timing_analysis.py`](file:///Users/kimsooyoung/Developments/projects/a2a-projects/simulation/sim21_regulatory_timing_analysis.py)
- 원본 시뮬레이션: [`future_scenarios_sim21.py`](file:///Users/kimsooyoung/Developments/projects/a2a-projects/simulation/future_scenarios_sim21.py)
- 시각화: [`regulatory_timing_sweep.png`](file:///Users/kimsooyoung/Developments/projects/a2a-projects/docs/assets/regulatory_timing_sweep.png)
