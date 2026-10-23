"""No-network preflight, explicit fallback policy, and conservative cost estimates."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import importlib
import os
from typing import Any


def preflight(*, provider: str, model: str = 'gemini-3.5-flash-lite',
              allow_network: bool = False, confirm_upload: bool = False,
              validate_sdk: bool = True) -> dict[str, Any]:
    """Validate a provider route without uploading user content or making API calls."""
    if provider == 'offline-ocr':
        return {'provider': provider, 'ready': True, 'network_required': False,
                'uploads_permitted': False, 'api_call_made': False}
    if provider != 'gemini':
        raise ValueError('Unsupported provider')
    if not model or not model.strip():
        raise ValueError('Gemini model ID cannot be blank')
    if not (allow_network and confirm_upload):
        raise ValueError('Gemini calls require --allow-network AND --confirm-upload; no default network requests')
    if not os.getenv('GOOGLE_API_KEY'):
        raise ValueError('GOOGLE_API_KEY not set; no call made')
    if validate_sdk:
        try:
            sdk = importlib.import_module('google.genai')
            if not hasattr(sdk, 'Client'):
                raise ImportError('google.genai.Client missing')
        except ImportError as exc:
            raise RuntimeError("Install optional SDK: pip install '.[live]'") from exc
    return {'provider': provider, 'model': model, 'ready': True, 'network_required': True,
            'uploads_permitted': True, 'api_call_made': False,
            'privacy_warning': 'Selected frames will be sent to the provider if an analysis is executed.'}


def price_estimate(usage: dict[str, Any], *, input_rate: float | None,
                   output_rate: float | None) -> float | None:
    """USD estimate from caller-verified $/1M token rates. Not actual billing."""
    if input_rate is None and output_rate is None:
        return None
    if input_rate is None or output_rate is None:
        raise ValueError('Supply BOTH rate assumptions, input and output')
    try:
        i_rate, o_rate = Decimal(str(input_rate)), Decimal(str(output_rate))
        input_tokens = Decimal(str(usage['input_tokens']))
        output_tokens = Decimal(str(usage['output_tokens']))
    except (InvalidOperation, TypeError, KeyError) as exc:
        return None  # A response without actual usage cannot support an estimate.
    if not all(v.is_finite() and v >= 0 for v in (i_rate, o_rate, input_tokens, output_tokens)):
        raise ValueError('Rates and token counts must be finite nonnegative values')
    return float((input_tokens * i_rate + output_tokens * o_rate) / Decimal(1_000_000))


def validate_rate_options(input_rate: float | None, output_rate: float | None) -> None:
    if (input_rate is None) != (output_rate is None):
        raise ValueError('Supply BOTH rate assumptions, input and output')
    if input_rate is not None:
        for rate in (input_rate, output_rate):
            if not Decimal(str(rate)).is_finite() or rate < 0:
                raise ValueError('Pricing assumptions must be finite and nonnegative')
