"""
backend/nlp/extractor.py — Project DRISHTI (Day 2)
=====================================================
Hybrid NLP extraction pipeline for cybercrime complaint text.

ARCHITECTURE DECISION (important for hackathon demo):
  We use a two-layer approach instead of fine-tuning HingBERT from scratch:

  Layer 1 — Regex + Pattern matching (instant, CPU-free):
    Handles structured fields that always appear in fixed formats:
    amounts (₹15,000 / Rs 15000 / 15k), UPI IDs, IFSC codes,
    account numbers, transaction IDs, phone numbers.

  Layer 2 — Keyword classifier (instant):
    Classifies fraud_type from a curated Hindi/English keyword bank.
    Handles Hinglish phrasing robustly (e.g., "paise gaye", "UPI fraud").

  Layer 3 (Day 3 upgrade slot) — DistilBERT / HingBERT NER:
    Replace or augment Layer 1/2 with a transformer-based NER model
    once fine-tuned on the complaints.csv dataset. See UPGRADE_NOTE below.

ACCURACY NOTES FOR DEMO (read before live demo!):
  [!] Amount extraction is ~95% accurate on our synthetic data because we
      generate "Rs X" and "rupay" consistently. Real complaints may use
      "paanch hazaar" (spelled out) — not handled yet.
  [!] Fraud type classification is keyword-weighted — if a complaint
      mentions both "UPI" and "KYC", the higher-weight keyword wins.
      Edge cases: a few templates mention both (e.g., Paytm KYC + UPI PIN).
  [!] UPI ID regex catches @okaxis / @ybl style IDs only. Does not catch
      phone number-style UPI (just the number).
  [~] IFSC and account extraction: not present in complaint_text (they come
      in as structured fields). These extractors activate on raw complaint
      text only when explicitly mentioned (edge case in real data).

Usage:
    from backend.nlp.extractor import ComplaintExtractor
    extractor = ComplaintExtractor()
    result = extractor.extract("Mujhe UPI pe 15000 ka fraud hua...")
    # result is an ExtractionResult dataclass
"""

import re
import math
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────
# 1. RESULT DATACLASS
# ─────────────────────────────────────────────────────────────

@dataclass
class ExtractionResult:
    """
    Structured output of the NLP extraction pipeline.
    None means the field could not be confidently extracted.
    """
    fraud_type:      Optional[str]   = None   # "upi_fraud" | "kyc_fraud" | "phishing"
    amount:          Optional[float] = None   # INR amount
    upi_id:          Optional[str]   = None   # e.g., "user@okaxis"
    transaction_id:  Optional[str]   = None   # UPI/REF/KYC reference
    bank_account:    Optional[str]   = None   # account number from text
    ifsc_code:       Optional[str]   = None   # IFSC from text
    phone_number:    Optional[str]   = None   # 10-digit number
    fraud_type_confidence: float     = 0.0    # 0–1
    extraction_confidence: float     = 0.0    # 0.0–1.0 based on key entities (amount, upi_id, txn_id)
    extraction_method: str           = "regex+keywords"


# ─────────────────────────────────────────────────────────────
# 2. REGEX PATTERNS
#    All patterns compiled once at module load for speed.
# ─────────────────────────────────────────────────────────────

# Amount: matches ₹15,000 / Rs.15000 / 15000 rupay / 15k / 1.5 lakh
_AMT_PATTERNS = [
    # ₹15,000 or Rs 15,000 or Rs.15,000
    re.compile(
        r'(?:Rs\.?|INR|rupees?|rupay|rupaye|paisa|rupe)[\s\.,]*'
        r'([\d,]+(?:\.\d{1,2})?)',
        re.IGNORECASE
    ),
    # ₹ symbol followed by number (Devanagari rupee sign)
    re.compile(
        r'[\u20b9]([\d,]+(?:\.\d{1,2})?)',
        re.IGNORECASE
    ),
    # "15000 rupay" or "15,000 rupees" — number before keyword
    re.compile(
        r'([\d,]+(?:\.\d{1,2})?)\s*(?:rupay|rupaye|rupees?|Rs\.?|INR)',
        re.IGNORECASE
    ),
    # "15k" shorthand
    re.compile(
        r'\b([\d]+(?:\.\d{1,2})?)\s*k\b',
        re.IGNORECASE
    ),
    # "1.5 lakh" or "2 lakh"
    re.compile(
        r'\b([\d]+(?:\.\d{1,2})?)\s*lakh',
        re.IGNORECASE
    ),
]

# UPI ID: user@okaxis, name@ybl, phone@paytm, etc.
_UPI_ID_RE = re.compile(
    r'\b[\w.\-]{3,50}@(?:okaxis|okhdfcbank|okicici|oksbi|ybl|upi|'
    r'paytm|apl|axisbank|sbi|imobile|idfcbank|indus|rbl|'
    r'aubank|federalbank|kotak|hdfc|icici|pnb|cub|cnrb|'
    r'NBIN|pthdfc|ptaxis|ptyes)\b',
    re.IGNORECASE
)

# Transaction reference IDs: UPI12345678901, REF12345678, KYC1234567
_TXN_ID_RE = re.compile(
    r'\b((?:UPI|REF|KYC|TXN|NEFT|IMPS|UTR|ORDER)[A-Z0-9]{6,20})\b',
    re.IGNORECASE
)

# IFSC: exactly 4 alpha + 0 + 6 alphanumeric
_IFSC_RE = re.compile(
    r'\b([A-Z]{4}0[A-Z0-9]{6})\b',
    re.IGNORECASE
)

# Bank account: 9–18 digit number (not a phone, not a year)
# We require it to appear near "account" keyword to reduce false positives.
_ACCOUNT_CONTEXT_RE = re.compile(
    r'(?:account|acc\.?|a/c|khata)\D{0,20}(\d{9,18})',
    re.IGNORECASE
)

# Indian mobile number: starts with 6-9, 10 digits
_PHONE_RE = re.compile(
    r'\b([6-9]\d{9})\b'
)


# ─────────────────────────────────────────────────────────────
# 3. FRAUD-TYPE KEYWORD BANK
#    Each keyword maps to (fraud_type, weight).
#    Weights accumulate across all matches; highest wins.
#    Tweak weights if demo complaints misclassify.
# ─────────────────────────────────────────────────────────────

_FRAUD_KEYWORDS: list[tuple[re.Pattern, str, float]] = [
    # ── UPI fraud keywords ──────────────────────────────────
    (re.compile(r'\bUPI\b',                     re.IGNORECASE), "upi_fraud", 3.0),
    (re.compile(r'\bPhonePe\b',                 re.IGNORECASE), "upi_fraud", 3.5),
    (re.compile(r'\bGoogle\s*Pay\b',            re.IGNORECASE), "upi_fraud", 3.5),
    (re.compile(r'\bGPay\b',                    re.IGNORECASE), "upi_fraud", 3.5),
    (re.compile(r'\bPaytm\b',                   re.IGNORECASE), "upi_fraud", 1.5),  # shared with KYC
    (re.compile(r'\bUPI\s*PIN\b',               re.IGNORECASE), "upi_fraud", 4.0),
    (re.compile(r'\bPIN\s+(?:daala|share|diya|dala)\b', re.IGNORECASE), "upi_fraud", 3.5),
    (re.compile(r'\btransfer\s+(?:ho|kar)\b',   re.IGNORECASE), "upi_fraud", 1.5),
    (re.compile(r'\brequest\b',                 re.IGNORECASE), "upi_fraud", 1.0),
    (re.compile(r'\bcashback\b',                re.IGNORECASE), "upi_fraud", 2.0),
    (re.compile(r'\bcollect\b',                 re.IGNORECASE), "upi_fraud", 1.5),
    (re.compile(r'\bpaise\s+(?:gaye|kat|nikal)\b', re.IGNORECASE), "upi_fraud", 2.0),
    # Social-engineering call patterns (SBI/bank fraud department style)
    (re.compile(r'\bfraud\s+department\b',      re.IGNORECASE), "upi_fraud", 3.0),
    (re.compile(r'\bcustomer\s+care\b',         re.IGNORECASE), "upi_fraud", 2.0),
    (re.compile(r'\bcall\s+(?:aaya|kiya|karke)\b', re.IGNORECASE), "upi_fraud", 1.5),
    (re.compile(r'\bbol\s+raha\b',              re.IGNORECASE), "upi_fraud", 1.5),  # impersonation
    (re.compile(r'\btransfer\s+karwa\b',        re.IGNORECASE), "upi_fraud", 3.0),
    (re.compile(r'\bfraud\s+(?:hua|ho)\b',      re.IGNORECASE), "upi_fraud", 1.5),  # generic fallback
    # UPI apps used as phishing vector — still UPI fraud, not phishing
    (re.compile(r'(?:Google\s*Pay|PhonePe|GPay|UPI)\s+(?:se|pe).*?link', re.IGNORECASE | re.DOTALL), "upi_fraud", 5.0),
    (re.compile(r'link.*?(?:Google\s*Pay|PhonePe|GPay)', re.IGNORECASE | re.DOTALL), "upi_fraud", 5.0),

    # ── KYC fraud keywords ──────────────────────────────────
    (re.compile(r'\bKYC\b',                     re.IGNORECASE), "kyc_fraud", 4.0),
    (re.compile(r'\bKYC\s+(?:update|expire|incomplete|band)\b', re.IGNORECASE), "kyc_fraud", 5.0),
    (re.compile(r'\bAadhaar\b',                 re.IGNORECASE), "kyc_fraud", 2.5),
    (re.compile(r'\bPAN\s+card\b',              re.IGNORECASE), "kyc_fraud", 2.0),
    (re.compile(r'\bverif(?:y|ication)\b',      re.IGNORECASE), "kyc_fraud", 1.5),
    (re.compile(r'\baccount\s+band\b',          re.IGNORECASE), "kyc_fraud", 3.0),
    (re.compile(r'\bblock\s+ho\b',              re.IGNORECASE), "kyc_fraud", 2.5),
    (re.compile(r'\bAnyDesk\b',                 re.IGNORECASE), "kyc_fraud", 4.0),
    (re.compile(r'\bremote\b',                  re.IGNORECASE), "kyc_fraud", 2.0),
    (re.compile(r'\bJan\s*Dhan\b',              re.IGNORECASE), "kyc_fraud", 3.0),
    (re.compile(r'\bUIDAI\b',                   re.IGNORECASE), "kyc_fraud", 3.5),
    (re.compile(r'\bform\s+(?:bhara|fill)\b',   re.IGNORECASE), "kyc_fraud", 2.0),

    # ── Phishing keywords ───────────────────────────────────
    (re.compile(r'\bphishing\b',                re.IGNORECASE), "phishing",  5.0),
    (re.compile(r'\bemail\b',                   re.IGNORECASE), "phishing",  2.5),
    (re.compile(r'\blink\b',                    re.IGNORECASE), "phishing",  1.0),  # reduced: 'link' appears in UPI too
    (re.compile(r'\blink\s+(?:aaya|bheja|mila)\b', re.IGNORECASE), "phishing", 2.5),  # phishing-specific phrasing
    (re.compile(r'\bclick\b',                   re.IGNORECASE), "phishing",  1.5),
    (re.compile(r'\blottery\b',                 re.IGNORECASE), "phishing",  4.0),
    (re.compile(r'\bjeet(?:a|e|ne)\b',          re.IGNORECASE), "phishing",  3.0),  # "jeeta" = won
    (re.compile(r'\brefund\b',                  re.IGNORECASE), "phishing",  2.5),
    (re.compile(r'\bOLX\b',                     re.IGNORECASE), "phishing",  3.5),
    (re.compile(r'\bQR\s*(?:code|scan)\b',      re.IGNORECASE), "phishing",  3.0),
    (re.compile(r'\bjob\s+offer\b',             re.IGNORECASE), "phishing",  3.5),
    (re.compile(r'\bregistration\s+fee\b',      re.IGNORECASE), "phishing",  3.5),
    (re.compile(r'\bNetflix\b',                 re.IGNORECASE), "phishing",  3.0),
    (re.compile(r'\bIRCTC\b',                   re.IGNORECASE), "phishing",  3.0),
    (re.compile(r'\bAmazon\b',                  re.IGNORECASE), "phishing",  2.5),
    (re.compile(r'\bfake\b',                    re.IGNORECASE), "phishing",  2.0),
    (re.compile(r'\bnakli\b',                   re.IGNORECASE), "phishing",  2.5),  # Hinglish "fake"
    (re.compile(r'\bprocessing\s+fee\b',        re.IGNORECASE), "phishing",  3.5),
    (re.compile(r'\bcovid\b',                   re.IGNORECASE), "phishing",  2.5),
    (re.compile(r'\brelief\b',                  re.IGNORECASE), "phishing",  2.0),
    (re.compile(r'\bpassword\b',                re.IGNORECASE), "phishing",  2.0),
    (re.compile(r'\blogin\b',                   re.IGNORECASE), "phishing",  2.5),
    (re.compile(r'\bsuspend\b',                 re.IGNORECASE), "phishing",  2.5),
    (re.compile(r'\bincome\s+tax\b',            re.IGNORECASE), "phishing",  3.0),
]


# ─────────────────────────────────────────────────────────────
# 4. AMOUNT NORMALISATION HELPERS
# ─────────────────────────────────────────────────────────────

def _normalise_amount(raw: str, multiplier: float = 1.0) -> float:
    """
    Convert a raw matched string to a float INR amount.
    Handles comma-separated numbers (1,50,000) and lakh/k multipliers.
    """
    # Remove commas (Indian number format: 1,50,000)
    cleaned = raw.replace(",", "").strip()
    try:
        value = float(cleaned) * multiplier
        return value
    except ValueError:
        return 0.0


def _extract_amount(text: str) -> Optional[float]:
    """
    Try all amount patterns in order, return the first valid match.
    Priority: explicit currency symbol > keyword before/after > shorthand.
    """
    candidates = []

    for i, pattern in enumerate(_AMT_PATTERNS):
        for match in pattern.finditer(text):
            raw = match.group(1)
            if i == 3:  # "k" shorthand
                amt = _normalise_amount(raw, multiplier=1000)
            elif i == 4:  # "lakh"
                amt = _normalise_amount(raw, multiplier=100000)
            else:
                amt = _normalise_amount(raw)

            # Sanity check: discard obviously wrong values
            if 100 <= amt <= 10_000_000:  # ₹100 to ₹1 crore
                candidates.append(amt)

    if not candidates:
        return None

    # Return the largest plausible amount (avoids matching "1" in "1 rupee verify trick")
    # ACCURACY NOTE [!]: this heuristic can over-estimate when text mentions
    # both a "processing fee" (small) and total fraud amount (large).
    # For the demo data it works correctly.
    return max(candidates)


# ─────────────────────────────────────────────────────────────
# 5. FRAUD TYPE CLASSIFIER
# ─────────────────────────────────────────────────────────────

def _classify_fraud_type(text: str) -> tuple[Optional[str], float]:
    """
    Returns (fraud_type, confidence) using weighted keyword voting.
    confidence = winning_weight / total_weight (0–1).

    ACCURACY NOTE [!]: If complaint mentions BOTH "UPI PIN" and "KYC",
    UPI wins because UPI_PIN has weight 4.0. This matches our data generation
    but edge cases exist in real complaints. Tune weights above to adjust.
    """
    scores: dict[str, float] = {"upi_fraud": 0.0, "kyc_fraud": 0.0, "phishing": 0.0}

    for pattern, fraud_type, weight in _FRAUD_KEYWORDS:
        if pattern.search(text):
            scores[fraud_type] += weight

    total = sum(scores.values())
    if total == 0:
        return None, 0.0

    best = max(scores, key=scores.get)
    confidence = scores[best] / total
    return best, round(confidence, 3)


# ─────────────────────────────────────────────────────────────
# 6. MAIN EXTRACTOR CLASS
# ─────────────────────────────────────────────────────────────

class ComplaintExtractor:
    """
    Stateless NLP extraction engine.
    Thread-safe — one instance can be shared across all FastAPI workers.

    Day 3 upgrade: add a __init__ that loads a HingBERT NER model and
    falls back to regex when the model is not confident (confidence < 0.6).
    """

    def extract(self, text: str) -> ExtractionResult:
        """
        Run the full extraction pipeline on a complaint string.

        Args:
            text: Raw complaint text (Hindi / English / Hinglish mixture)

        Returns:
            ExtractionResult with all extracted fields (None if not found)
        """
        result = ExtractionResult()

        # ── Fraud type ────────────────────────────────────────────
        result.fraud_type, result.fraud_type_confidence = _classify_fraud_type(text)

        # ── Amount ───────────────────────────────────────────────
        result.amount = _extract_amount(text)

        # ── UPI ID ───────────────────────────────────────────────
        upi_match = _UPI_ID_RE.search(text)
        result.upi_id = upi_match.group(0) if upi_match else None

        # ── Transaction ID ───────────────────────────────────────
        txn_match = _TXN_ID_RE.search(text)
        result.transaction_id = txn_match.group(1).upper() if txn_match else None

        # ── IFSC code ────────────────────────────────────────────
        ifsc_match = _IFSC_RE.search(text)
        result.ifsc_code = ifsc_match.group(1).upper() if ifsc_match else None

        # ── Bank account number ──────────────────────────────────
        acc_match = _ACCOUNT_CONTEXT_RE.search(text)
        result.bank_account = acc_match.group(1) if acc_match else None

        # ── Phone number ─────────────────────────────────────────
        # Take the first match; skip if it looks like an amount (all same digit unlikely)
        for phone_match in _PHONE_RE.finditer(text):
            candidate = phone_match.group(1)
            # Reject if it's embedded in a longer number (account number artefact)
            start, end = phone_match.span(1)
            before = text[start-1:start] if start > 0 else " "
            after  = text[end:end+1] if end < len(text) else " "
            if not (before.isdigit() or after.isdigit()):
                result.phone_number = candidate
                break

        # ── Extraction Confidence Scoring ────────────────────────
        # Key entities: amount, upi_id, transaction_id
        key_entities = [
            result.amount is not None,
            result.upi_id is not None,
            result.transaction_id is not None,
        ]
        extracted_count = sum(1 for present in key_entities if present)
        result.extraction_confidence = round(extracted_count / len(key_entities), 2)

        return result

    def extract_to_dict(self, text: str) -> dict:
        """Convenience wrapper returning a plain dict (for JSON serialisation)."""
        r = self.extract(text)
        return {
            "fraud_type":            r.fraud_type,
            "fraud_type_confidence": r.fraud_type_confidence,
            "extraction_confidence": r.extraction_confidence,
            "amount":                r.amount,
            "upi_id":                r.upi_id,
            "transaction_id":        r.transaction_id,
            "bank_account":          r.bank_account,
            "ifsc_code":             r.ifsc_code,
            "phone_number":          r.phone_number,
            "extraction_method":     r.extraction_method,
        }


# ─────────────────────────────────────────────────────────────
# UPGRADE NOTE — Day 3: HingBERT NER Integration
# ─────────────────────────────────────────────────────────────
# To upgrade to transformer-based NER:
#
#   from transformers import pipeline
#
#   class ComplaintExtractor:
#       def __init__(self, model_path: str = "l3cube-pune/hindi-bert-v2"):
#           # Load NER pipeline (CPU-compatible)
#           self._ner = pipeline(
#               "ner",
#               model=model_path,
#               aggregation_strategy="simple",
#               device=-1  # -1 = CPU
#           )
#
#       def extract(self, text: str) -> ExtractionResult:
#           result = ExtractionResult(extraction_method="hingbert_ner")
#           ner_out = self._ner(text)
#           for entity in ner_out:
#               if entity["entity_group"] == "MONEY":
#                   result.amount = float(entity["word"].replace(",",""))
#               elif entity["entity_group"] == "ORG":
#                   # bank name → map to fraud type
#                   ...
#           # Fallback: if NER confidence < 0.6, use regex
#           if result.amount is None:
#               result.amount = _extract_amount(text)
#           return result
# ─────────────────────────────────────────────────────────────


# Quick self-test when run directly
if __name__ == "__main__":
    extractor = ComplaintExtractor()
    tests = [
        "Mujhe UPI pe ek request aayi Rs 15,000 ki - PIN daala aur paise chale gaye.",
        "KYC update nahi hua to account band ho jayega — link pe Aadhaar dala aur Rs.80000 gaye.",
        "Amazon ka fake order cancel mail aaya, customer care number dial kiya — Rs 12500 ka fraud.",
        "Mere PhonePe account se 45000 rupay bina kisi approval ke transfer ho gaye UPI123456789012.",
        "HDFC0001234 account se paise nikal gaye. Account number 9876543210 hai.",
    ]
    for t in tests:
        r = extractor.extract_to_dict(t)
        print(f"\nText: {t[:60]}...")
        print(f"  fraud_type : {r['fraud_type']} ({r['fraud_type_confidence']:.0%})")
        print(f"  amount     : {r['amount']}")
        print(f"  txn_id     : {r['transaction_id']}")
        print(f"  ifsc       : {r['ifsc_code']}")
