from pathlib import Path

import pytest

from hospital_routes.io import load_problem


@pytest.fixture
def problem():
    return load_problem(Path(__file__).parents[1] / "data" / "deliveries.json")
