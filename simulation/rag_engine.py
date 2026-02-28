"""
에이전트의 경험 기억을 관리하는 RAG 엔진.

각 에이전트는 독립적인 경험 DB를 보유한다.
경험 = (상황, 행동, 결과, 상대방 에이전트 ID, 신뢰도 변화)

의사결정 시:
1. 현재 상황을 임베딩
2. FAISS에서 유사 과거 경험 k개 검색
3. 검색된 경험을 LLM 프롬프트에 주입
4. LLM이 경험 기반으로 행동 결정
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

@dataclass
class Experience:
    """
    에이전트의 단일 경험 단위.
    자연어로 기록되어 LLM 프롬프트에 직접 삽입 가능.
    """
    turn: int
    situation: str          # "에너지 42%, 상대방 financial_3와 협상 요청"
    action_taken: str       # "SUBMIT", "EXPLOIT", "WAIT", "NEGOTIATE"
    outcome: str            # "자원 +15, 신뢰도 +0.1, 생태계 에너지 -2%"
    counterparty_id: str    # 거래한 에이전트 ID
    trust_delta: float      # 이 경험이 신뢰에 미친 영향
    ecosystem_survived: bool
    
    def to_text(self) -> str:
        """LLM 프롬프트에 삽입할 자연어 형식"""
        return (
            f"[턴 {self.turn}] 상황: {self.situation} | "
            f"행동: {self.action_taken} | "
            f"결과: {self.outcome} | "
            f"신뢰 변화: {self.trust_delta:+.2f}"
        )


class AgentExperienceDB:
    """
    에이전트 개인 경험 데이터베이스.
    FAISS 인덱스로 유사 경험을 고속 검색.
    
    메모리 관리:
    - 최대 5,000개 경험 저장 (에이전트당 약 10MB)
    - 20개 에이전트 × 10MB = 200MB (RAM 47GB 여유)
    - 디스크 백업: /content/sim24_outputs/{agent_id}_exp.pkl
    """
    
    EMBED_MODEL = None  # 전역 공유 (메모리 절약)
    EMBED_DIM = 384     # all-MiniLM-L6-v2 차원
    
    @classmethod
    def get_embed_model(cls):
        if cls.EMBED_MODEL is None and SentenceTransformer is not None:
            # Colab 환경 최적화
            cls.EMBED_MODEL = SentenceTransformer(
                'all-MiniLM-L6-v2',
                cache_folder='/content/model_cache'
            )
        return cls.EMBED_MODEL
    
    def __init__(self, agent_id: str, max_experiences: int = 5000):
        self.agent_id = agent_id
        self.max_experiences = max_experiences
        self.experiences: list[Experience] = []
        
        # FAISS 인덱스 초기화
        if faiss is not None:
            self.index = faiss.IndexFlatL2(self.EMBED_DIM)
        else:
            self.index = None
        self.embeddings = np.zeros((0, self.EMBED_DIM), dtype=np.float32)
    
    def add_experience(self, exp: Experience):
        """경험 추가 및 임베딩 인덱싱"""
        if len(self.experiences) >= self.max_experiences:
            # 가장 오래된 경험 제거 (슬라이딩 윈도우)
            self.experiences.pop(0)
            self.embeddings = self.embeddings[1:]
            if self.index is not None:
                self.index.reset()
                if len(self.embeddings) > 0:
                    self.index.add(self.embeddings)
        
        self.experiences.append(exp)
        
        # 텍스트 임베딩
        if self.index is not None and self.get_embed_model() is not None:
            embed = self.get_embed_model().encode(
                [exp.to_text()],
                convert_to_numpy=True
            ).astype(np.float32)
            
            self.embeddings = np.vstack([self.embeddings, embed]) \
                            if len(self.embeddings) > 0 else embed
            self.index.add(embed)
    
    def retrieve_similar(self, query: str, k: int = 3) -> list[Experience]:
        """현재 상황과 유사한 과거 경험 k개 반환"""
        if len(self.experiences) == 0:
            return []
            
        k = min(k, len(self.experiences))
        
        if self.index is None or self.get_embed_model() is None:
            # RAG 기능 비활성 시 최근 경험 반환 (더미 구현)
            return self.experiences[-k:]
            
        query_embed = self.get_embed_model().encode(
            [query], convert_to_numpy=True
        ).astype(np.float32)
        
        distances, indices = self.index.search(query_embed, k)
        return [self.experiences[i] for i in indices[0] if i < len(self.experiences)]
    
    def get_trust_score(self, agent_id: str) -> float:
        """특정 에이전트와의 과거 거래 기반 신뢰 점수 (0~1)"""
        relevant = [e for e in self.experiences 
                   if e.counterparty_id == agent_id]
        if not relevant:
            return 0.5  # 초기 신뢰 중립
        
        trust = 0.5 + sum(e.trust_delta for e in relevant)
        return max(0.0, min(1.0, trust))
