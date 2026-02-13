# ComputeToken Deployment Guide

## 🎯 목표

`ComputeToken.sol`을 Base Sepolia 테스트넷에 배포하고 검증합니다.

---

## ✅ 사전 준비

### 1. Base Sepolia ETH 받기

**무료 Faucet에서 0.01 ETH 받기:**
- [Alchemy Base Sepolia Faucet](https://www.alchemy.com/faucets/base-sepolia)
- [Coinbase Wallet Faucet](https://portal.cdp.coinbase.com/products/faucet)

**지갑 주소 확인:**
```bash
# 배포에 사용할 지갑 주소 확인
# (Metamask나 다른 지갑에서 확인)
```

### 2. Basescan API Key 발급 (선택사항, 검증용)

**무료 API Key 받기:**
1. [Basescan](https://basescan.org/register) 회원가입
2. [API Keys](https://basescan.org/myapikey) 페이지에서 생성
3. API Key 복사

---

## 📝 Step 1: 환경 변수 설정

```bash
cd packages/contracts

# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 code .env
```

**`.env` 파일 내용:**
```bash
# Deployer wallet private key (WITHOUT 0x prefix)
# ⚠️ CRITICAL: 테스트용 지갑만 사용하세요!
DEPLOYER_PRIVATE_KEY=여기에_지갑_비밀키_입력

# Paymaster Gateway address (will receive MINTER_ROLE)
# 이 주소가 $COMP를 민팅할 수 있는 권한을 받습니다
# 
# ⚠️ IMPORTANT DECISION:
# Paymaster 서비스는 Pimlico 업스트림만 사용하며 자체 지갑이 없습니다.
# 따라서 MINTER_ROLE을 받을 "관리용 지갑" 주소를 결정해야 합니다:
#
# 옵션 1 (추천): 배포자 본인의 주소 사용 (수동 관리)
#   - 나중에 필요시 직접 mint() 호출 가능
#   - 예: PAYMASTER_ADDRESS=0xYourOwnWalletAddress
#
# 옵션 2: 별도 관리용 지갑 생성
#   - 더 안전하지만 관리 복잡도 증가
#
# 옵션 3: 나중에 멀티시그로 전환
#   - 초기에는 옵션1로 시작, 추후 DAO로 이관
#
# 결정 후 아래 입력:
PAYMASTER_ADDRESS=0x...  # 선택한 관리 지갑 주소

# RPC URLs (기본값 사용 가능)
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
BASE_MAINNET_RPC_URL=https://mainnet.base.org

# Basescan API key for contract verification (선택사항)
BASESCAN_API_KEY=여기에_API_키_입력_또는_비워두기

# Gas reporter (optional)
REPORT_GAS=false
```

**중요 포인트:**
- ⚠️ `DEPLOYER_PRIVATE_KEY`: 0x 없이 64자리 16진수만 입력
- ⚠️ `PAYMASTER_ADDRESS`: Paymaster **서비스 지갑 주소** (Cloud Run URL 아님)

---

## 🔍 Step 2: Paymaster 지갑 주소 확인

**현재 상황:**
- Paymaster 서비스 URL: `https://paymaster.a10m.work`
- 필요한 정보: Paymaster가 사용하는 **EOA (Externally Owned Account) 주소**

**확인 방법:**

**옵션 A: 환경 변수 확인 (추천)**
```bash
# Cloud Run 환경 변수에서 확인
gcloud run services describe paymaster \
  --region=asia-northeast3 \
  --format='value(spec.template.spec.containers[0].env)'
```

**옵션 B: 로그에서 확인**
```bash
# Paymaster 서비스 로그 확인
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=paymaster" \
  --limit=50 \
  --format=json | grep -i "signer\|wallet\|address"
```

**옵션 C: 코드에서 확인**
Paymaster 서비스 코드에서 사용하는 지갑 주소를 찾아보세요.

---

## 🚀 Step 3: 배포 실행

```bash
cd packages/contracts

# 1. 컴파일 확인 (이미 완료되었지만 다시 확인)
pnpm compile

# 2. Base Sepolia에 배포
pnpm deploy:sepolia
```

**예상 출력:**
```
🚀 Deploying ComputeToken with account: 0xYourAddress
💰 Account balance: 0.01 ETH
🔑 Paymaster address (will receive MINTER_ROLE): 0xPaymasterAddress

✅ ComputeToken deployed successfully!
📍 Contract address: 0x1234567890abcdef...
📝 Token name: Compute Token
🔤 Token symbol: COMP
🔢 Decimals: 18
💎 Total supply: 0 COMP

🔐 Access Control:
  - Admin: 0xYourAddress ✅
  - Minter: 0xPaymasterAddress ✅

🔍 Verify contract on Basescan:
npx hardhat verify --network base-sepolia 0x1234... 0xPaymaster...
```

**배포된 주소 복사해두기:**
```bash
# 출력된 Contract address를 메모해두세요
# 예: 0x1234567890abcdef1234567890abcdef12345678
```

---

## ✅ Step 4: Basescan에서 검증 (선택사항)

**검증 명령:**
```bash
npx hardhat verify \
  --network base-sepolia \
  0x1234567890abcdef1234567890abcdef12345678 \  # 배포된 컨트랙트 주소
  0xPaymasterAddressHere                        # Paymaster 주소
```

**성공 시 출력:**
```
Successfully verified contract ComputeToken on Basescan.
https://sepolia.basescan.org/address/0x1234...#code
```

---

## 📋 Step 5: 배포 결과 기록

**`packages/contracts/deployments.json` 생성:**
```json
{
  "base-sepolia": {
    "ComputeToken": {
      "address": "0x1234567890abcdef...",
      "deployer": "0xYourAddress",
      "paymaster": "0xPaymasterAddress",
      "deployedAt": "2026-02-10T20:20:00Z",
      "txHash": "0xabcdef...",
      "verified": true
    }
  }
}
```

---

## 🔧 Step 6: Phase 2 환경 변수 업데이트

**배포 완료 후, Paymaster 서비스에 COMP 주소 추가:**

```bash
cd apps/paymaster

# .env 파일에 추가
echo "COMP_TOKEN_ADDRESS=0x1234567890abcdef..." >> .env
echo "COMP_PRICE_USD=0.10" >> .env
echo "ENABLE_COMP_FEES=false" >> .env
```

---

## 🐛 문제 해결

### 에러: "insufficient funds for gas"
**원인:** 지갑에 ETH가 부족  
**해결:** Faucet에서 더 받기

### 에러: "Invalid PAYMASTER_ADDRESS"
**원인:** Paymaster 주소가 잘못됨  
**해결:** 0x로 시작하는 올바른 Ethereum 주소 확인

### 에러: "nonce has already been used"
**원인:** 트랜잭션이 이미 처리됨  
**해결:** Basescan에서 트랜잭션 확인 후 다시 시도

### 검증 에러: "already verified"
**원인:** 이미 검증됨  
**해결:** Basescan URL에서 확인

---

## ✅ 배포 완료 체크리스트

- [ ] Base Sepolia ETH 0.01+ 확보
- [ ] `.env` 파일 설정 완료
- [ ] Paymaster 지갑 주소 확인
- [ ] `pnpm deploy:sepolia` 실행 성공
- [ ] Contract address 기록
- [ ] Basescan 검증 완료 (선택)
- [ ] `deployments.json` 생성
- [ ] Paymaster `.env`에 COMP 주소 추가

---

## 🎉 다음 단계

배포 완료 후:
1. ✅ Phase 1 완료!
2. ➡️ **Phase 2: Oracle Layer 구현 시작**
3. ➡️ Phase 3: Paymaster Fee Validation 통합
4. ➡️ Phase 4: SDK 업데이트

**배포된 주소를 제게 알려주시면 다음 단계를 진행하겠습니다!**
