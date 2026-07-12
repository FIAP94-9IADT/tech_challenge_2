import pytest

from hospital_routes.models import Delivery, haversine_km


def test_haversine_is_symmetric_and_zero_on_same_point():
    a, b = (-12.9714, -38.5014), (-13.0014, -38.5068)
    assert haversine_km(a, a) == pytest.approx(0)
    assert haversine_km(a, b) == pytest.approx(haversine_km(b, a))
    assert haversine_km(a, b) > 0


def test_delivery_rejects_invalid_priority():
    with pytest.raises(ValueError):
        Delivery("x", "local", 0, 0, 1, priority=4)
