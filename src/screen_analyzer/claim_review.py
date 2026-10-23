"""Conservative lexical review of generated analysis: flags, not fact checking.

A citation to a sampled frame is never by itself proof of a capability claim.
This module must not silently change or remove user/model output.
"""
from __future__ import annotations

import re
from typing import Any
from .models import Analysis

# Possible overclaims: these require a person to check actual frame content.
# Small, deliberately interpretable vocabulary; no pretend AI fact-check score.
PATTERNS = (
    ('unverified_payment_action', r'\b(?:process(?:es|ing|ed)? payments?|payments? processed|payment successful)\b'),
    ('unverified_multi_payer_feature', r'\b(?:bill splitting|split(?:ting)? bills?|split the bill)\b'),
    ('unverified_speed', r'\b(?:instant(?:ly)?|in one second|real.time)\b'),
    ('unverified_breakdown', r'\b(?:total breakdown|itemi[sz]ed breakdown)\b'),
    ('unverified_tap_count', r'\b(?:single tap|one tap|one click|single click)\b'),
    ('unverified_automation', r'\b(?:automatically|fully automated)\b'),
)


def review_claims(analysis: Analysis) -> dict[str, Any]:
    """Flag language for human review without claiming true/false accuracy."""
    text_fields: list[tuple[str, str, list[int]]] = [
        ('app_summary', analysis.app_summary, []),
    ]
    for i, step in enumerate(analysis.workflow_steps):
        text_fields.append((f'workflow_steps[{i}].action',step.action,step.evidence_frames))
    for i, segment in enumerate(analysis.segments):
        text_fields.append((f'segments[{i}].title',segment.title,segment.evidence_frames))
    for i, moment in enumerate(analysis.marketing_moments):
        text_fields.append((f'marketing_moments[{i}].hook',moment.hook,moment.evidence_frames))
    for i, finding in enumerate(analysis.findings):
        text_fields.append((f'findings[{i}].text',finding.text,finding.evidence_frames))

    flags=[]
    for field, value, evidence in text_fields:
        for category, pattern in PATTERNS:
            for match in re.finditer(pattern, value, re.IGNORECASE):
                flags.append({'category':category,'field':field,
                              'excerpt':match.group(0),'evidence_frames':list(evidence),
                              'explanation':'Potential capability/speed claim: verify against sampled video before publication.'})
    return {
        'schema':'screen-recording-analyzer.claim-review.v1',
        'status':'REVIEW_REQUIRED' if flags else 'NO_LEXICAL_FLAGS',
        'flags':flags,
        'limitations':[
            'Rule-based phrases are review prompts, not evidence a claim is false.',
            'Absence of flags does not establish semantic accuracy or publication approval.',
            'Frames and full video require independent human review.',
        ],
    }
