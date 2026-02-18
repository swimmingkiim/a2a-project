# 🌱 Ecosystem Growth Roadmap

CredentialVerifier (Web of Trust) 배포 후 생태계 성장 단계별 TODO.

---

## Phase 1: Bootstrap (현재 → 에이전트 10명)

> Bootstrap Voucher(deployer)가 초기 에이전트를 직접 보증합니다.

- [ ] CredentialVerifier 배포 및 AgentRegistry 연결
- [ ] `DEPLOYED_ADDRESSES.md`에 CredentialVerifier 주소 추가
- [ ] agent-node에 Attestation 발급 엔드포인트 추가 (`/vouch`)
  - `AttestationSigner` (api-sdk) 사용
  - Cloud Secret Manager에서 Bootstrap Voucher 키 로드
- [ ] 새 에이전트 등록 시 VC 발급 → Attestation 생성 → register() 플로우 검증
- [ ] api-sdk NPM 퍼블리시 (v0.1.36: AttestationSigner + RegistryReader)

---

## Phase 2: Peer Vouching (에이전트 10명 ~ 50명)

> 등록된 에이전트들이 서로를 보증할 수 있게 전환합니다.

- [ ] 등록된 에이전트에게 보증 기능 안내 (문서/가이드)
- [ ] 보증자 UI 또는 CLI 도구 제공
  - `AttestationSigner`로 다른 에이전트를 보증하는 스크립트
- [ ] `getTrustPath()` 결과를 대시보드에 시각화 (optional)
- [ ] 보증 남용 모니터링 체계 구축
  - 한 에이전트가 과다 보증 시 경고
  - 보증받은 에이전트가 슬래싱되면 보증인 추적

---

## Phase 3: Bootstrap 비활성화 (에이전트 50명+)

> 생태계가 자립 가능한 수준에 도달하면 Bootstrap을 비활성화합니다.

- [ ] 충분한 Peer Voucher가 활동 중인지 확인
  - 최소 5명 이상의 활성 보증인이 있는지 검증
- [ ] `verifier.setBootstrapVoucher(address(0))` 실행
- [ ] Bootstrap 비활성화 후 신규 등록 테스트
- [ ] `DEPLOYED_ADDRESSES.md` 업데이트 (Bootstrap: disabled)

---

## Phase 4: 신뢰 강화 (에이전트 100명+)

> Reputation 기반 보증 자격 제한 및 보증인 페널티 도입.

- [ ] 보증인 최소 reputation 기준 도입 (예: ≥ 60)
  - `CredentialVerifier` 업그레이드하여 `minVoucherReputation` 추가
- [ ] 보증인 연대 책임 도입
  - 보증받은 에이전트가 슬래싱되면 보증인 reputation 차감
- [ ] 보증 쿨다운 또는 횟수 제한 도입
  - 같은 에이전트가 연속으로 보증할 수 있는 횟수 제한
- [ ] 신뢰 그래프 분석 도구 (on-chain analytics)

---

## Phase 5: 완전 탈중앙화 (장기)

> Admin 권한 최소화 및 거버넌스 위임.

- [ ] CredentialVerifier의 ADMIN_ROLE을 EmergencyCouncil 멀티시그로 이전
- [ ] AgentRegistry의 ADMIN_ROLE도 거버넌스 컨트랙트로 이전
- [ ] 커뮤니티 투표로 매개변수 조정 (minReputation, 쿨다운 등)
- [ ] Web of Trust 그래프를 외부 탐색기에서 시각화
