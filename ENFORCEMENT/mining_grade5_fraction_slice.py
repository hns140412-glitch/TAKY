#!/usr/bin/env python3
"""A source-anchored Grade-5 *candidate* exercise, not an adopted Learning policy.

Derived from the independently fetched 2026-09-01 Incheon publisher's math
guide, physical PDF pp. 113, 117-118. The exercise is independently authored:
the source supplies the reasoning/rubric principle, not copied question text.
This module never assigns canonical SourceID, learner mastery or Planner date.
"""
from __future__ import annotations

from fractions import Fraction

MATH_PDF_SHA256="d14a34c1e9ab005727ab84bf563be3c3b2906578956890994ce9945bd981261e"
RAW_DRIVE_ID="1gulsvxZkbS4PkEr2AjXS4-TxMqegi6Us"
SOURCE_POST="https://www.ice.go.kr/ice/na/ntt/selectNttInfo.do?mi=11633&nttSn=3383177"
SOURCE_PDF="https://www.ice.go.kr/upload/ice/na/bbs_1630/2026/09/611131ca7e3b4a759d63b64bdc81e2e3.pdf"
BASE=(6,9)
MAX_COMPONENT=10000
MAX_FACTOR=20

ACTIVITY={
    "schema":"TAKY_MINING_GRADE5_FRACTION_ACTIVITY_CANDIDATE_V1",
    "activity_id":"ICE3383177-G5-MATH-EQUIVALENT-FRACTIONS-CANDIDATE",
    "state":"REFERENCE_ONLY_NOT_INDEXED",
    "subject":"MATH","grade":5,"unit":"약분과 통분",
    "source":{
        "publisher_post":SOURCE_POST,"official_pdf_url":SOURCE_PDF,
        "drive_raw_file_id":RAW_DRIVE_ID,"sha256":MATH_PDF_SHA256,
        "physical_pdf_pages":[113,117,118],
        "claim":"An equivalent fraction must use the same nonzero factor on numerator and denominator; the stated operation must agree with the produced fraction.",
        "index_identity_state":"INDEX_OWNER_REVIEW_PENDING",
        "publisher_original_bytes_previously_verified":True,
    },
    "original_prompt":"6/9와 같은 크기의 분수를 나누기로 하나, 곱하기로 하나 만드세요. 각각 분자와 분모에 사용한 수를 표시하고, 왜 같은 크기인지 설명해 보세요.",
    "base_fraction":{"numerator":6,"denominator":9},
    "response_contract":{"steps":[
        {"operation":"DIVIDE","factor":3,"fraction":{"numerator":2,"denominator":3},"reason":"분자와 분모를 모두 같은 수로 나눈다."},
        {"operation":"MULTIPLY","factor":2,"fraction":{"numerator":12,"denominator":18},"reason":"분자와 분모를 모두 같은 수로 곱한다."},
    ],"hint_used":False},
    "signals":["EQUIVALENCE","OPERATION_CONSISTENCY","REASONING_EXPLANATION","ASSISTANCE"],
    "planner_allocation_allowed":False,
    "mastery_observation_allowed":False,
}


def _number(value):
    if type(value) is not int or value < 1 or value > MAX_COMPONENT:
        return None
    return value


def check_response(payload:dict)->dict:
    """Deterministically check arithmetic and the declared operation only.

    Natural-language explanation remains UNREVIEWED: nonempty text is NOT
    proof of coherent reasoning. No child identity is stored or inferred.
    """
    steps=payload.get("steps") if isinstance(payload,dict) else None
    if not isinstance(steps,list) or len(steps)!=2:
        return _hold("TWO_DISTINCT_OPERATION_STEPS_REQUIRED")
    assessments=[]
    for item in steps:
        if not isinstance(item,dict):
            return _hold("STRUCTURED_STEP_REQUIRED")
        method=str(item.get("operation") or "").upper()
        factor=_number(item.get("factor"))
        if factor is not None and factor > MAX_FACTOR:
            factor=None
        val=item.get("fraction") or {}
        n=_number(val.get("numerator")) if isinstance(val,dict) else None
        d=_number(val.get("denominator")) if isinstance(val,dict) else None
        reason=item.get("reason")
        reason_present=isinstance(reason,str) and bool(reason.strip())
        method_valid=method in {"DIVIDE","MULTIPLY"} and factor is not None and factor>1
        if method_valid and method=="DIVIDE":
            exact=BASE[0]%factor==0 and BASE[1]%factor==0
            expected=(BASE[0]//factor,BASE[1]//factor) if exact else None
        elif method_valid:
            expected=(BASE[0]*factor,BASE[1]*factor)
        else:
            expected=None
        fraction_equivalent=(n is not None and d is not None
                            and Fraction(n,d)==Fraction(*BASE))
        operation_consistent=(expected is not None and (n,d)==expected)
        assessments.append({
            "operation":method,
            "fraction_equivalent":fraction_equivalent,
            "operation_consistent":operation_consistent,
            "reason_present":reason_present,
            "reason_review_state":"PENDING_AUTHORIZED_LANGUAGE_REVIEW" if reason_present
                                  else "MISSING",
            "arithmetic_signal":"CHECKED" if fraction_equivalent and operation_consistent
                                else "REMEDIATION_CANDIDATE",
        })
    methods={a["operation"] for a in assessments}
    arithmetic_complete=(methods=={"DIVIDE","MULTIPLY"}
                         and all(a["fraction_equivalent"] and a["operation_consistent"]
                                 for a in assessments))
    reasoning_ready=arithmetic_complete and all(a["reason_present"] for a in assessments)
    return {
        "schema":"TAKY_MINING_GRADE5_FRACTION_RESPONSE_CANDIDATE_V1",
        "state":"REASONING_REVIEW_PENDING" if reasoning_ready else
                "GUIDED_RETRY_CANDIDATE",
        "step_assessments":assessments,
        "arithmetic_consistent":arithmetic_complete,
        "hint_used":payload.get("hint_used") is True,
        "reasoning_verified":False,
        "learning_observation":{"skill_id":"G5-MATH-EQUIVALENT-FRACTION-REASONING",
                                "correct":None,
                                "assisted":payload.get("hint_used") is True,
                                "status":"CANDIDATE_NOT_LEARNER_MASTERY"},
        "next_feedback_focus":("REVIEW_EXPLANATION" if reasoning_ready else
                               "NUMERATOR_DENOMINATOR_SAME_FACTOR_AND_METHOD"),
        "planner_allocation_allowed":False,
        "source_index_owner_review_required":True,
        "guards":{"free_text_not_autoscored":True,
                  "original_source_is_reference_not_automatic_authority":True,
                  "no_personal_learner_data":True,
                  "no_mastery_or_schedule_promotion":True},
    }


def _hold(reason:str)->dict:
    return {
        "schema":"TAKY_MINING_GRADE5_FRACTION_RESPONSE_CANDIDATE_V1",
        "state":"HOLD_INPUT","reason":reason,
        "arithmetic_consistent":False,"reasoning_verified":False,
        "learning_observation":None,"planner_allocation_allowed":False,
    }
