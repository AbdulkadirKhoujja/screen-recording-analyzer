"""Regression tests for provider SDK schema routing. No external calls."""
from pydantic import ValidationError
import pytest
from screen_analyzer.models import Analysis


def test_json_schema_preserves_strictness_and_nested_defs():
    schema = Analysis.model_json_schema()
    assert schema['additionalProperties'] is False
    assert schema['properties']['workflow_steps']['items']['$ref'] == '#/$defs/WorkflowStep'
    for name in ('Finding','MarketingMoment','Segment','WorkflowStep'):
        assert schema['$defs'][name]['additionalProperties'] is False


def test_local_pydantic_validation_catches_unexpected_output():
    good = {'app_summary':'Synthetic demo','workflow_steps':[], 'segments':[],
            'marketing_moments':[], 'findings':[]}
    assert Analysis.model_validate(good).app_summary == 'Synthetic demo'
    with pytest.raises(ValidationError):
        Analysis.model_validate({**good,'unrecognised_model_field':'bad'})
