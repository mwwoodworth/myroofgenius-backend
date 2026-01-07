import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from routes.ai_vision import _aggregate_frame_analyses, generate_estimate_from_analysis


def test_aggregate_frame_analyses():
    aggregated = _aggregate_frame_analyses(
        [
            {"damage_severity": 6, "estimated_sq_ft": 1800, "material_type": "metal", "complexity": "simple"},
            {"damage_severity": 4, "estimated_sq_ft": 2200, "material_type": "metal", "complexity": "moderate"},
        ]
    )

    assert aggregated["damage_severity"] == 5.0
    assert aggregated["estimated_sq_ft"] == 2000.0
    assert aggregated["material_type"] == "metal"
    assert aggregated["frame_count"] == 2


@pytest.mark.asyncio
async def test_generate_estimate_from_analysis_handles_strings():
    estimate = await generate_estimate_from_analysis(
        {"damage_severity": "8", "estimated_sq_ft": "1500", "material_type": "tile", "complexity": "simple"},
        customer_id="cust",
        job_id="job",
    )

    assert estimate["estimated_total"] > 0
    assert estimate["square_footage"] == 1500.0
