from __future__ import annotations
from typing import Literal
from pydantic import BaseModel


class Claim(BaseModel):
    id: str
    text: str
    modality: Literal["text", "visual", "metadata", "cross_modal"]
    source: str


class CrossModalCheck(BaseModel):
    match: bool
    reason: str


class ClaimSet(BaseModel):
    claims: list[Claim]
    formula: str
    cross_modal_check: CrossModalCheck | None = None
    input_risk_hint: Literal["low", "medium", "high"] = "low"


class Evidence(BaseModel):
    url: str
    title: str
    snippet: str
    relevance_score: float
    source_type: str


class ImageIntegritySignals(BaseModel):
    fft_ai_score: float
    ela_manipulation_score: float
    noise_consistency: float
    has_exif: bool


class RawSignals(BaseModel):
    claim_id: str
    web_results: list[Evidence]
    exif_data: dict | None = None
    image_integrity: ImageIntegritySignals | None = None
    provenance: list[Evidence] | None = None


class ClaimVerdict(BaseModel):
    claim_id: str
    status: Literal["supported", "refuted", "uncertain"]
    confidence: float
    key_evidence: list[Evidence]
    reasoning: str


class TrustProfile(BaseModel):
    claims: list[Claim]
    formula: str
    per_claim: list[ClaimVerdict]
    overall_confidence: float
    verdict: Literal["likely_authentic", "likely_manipulated", "uncertain", "insufficient_data"]
    red_flags: list[str]
    evidence_summary: str
    depth: Literal["quick", "deep"]
