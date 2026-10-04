import pytest


def test_aov_calculation_standard():
    total_revenue = 15000.00
    total_orders = 150
    aov = total_revenue / total_orders
    assert aov == 100.00


def test_aov_calculation_zero_orders():
    total_revenue = 0.00
    total_orders = 0
    aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.00
    assert aov == 0.00


def test_yoy_growth_standard():
    current_rev = 120000.00
    prior_rev = 100000.00
    growth = ((current_rev - prior_rev) / prior_rev) * 100.0
    assert round(growth, 2) == 20.00


def test_yoy_growth_negative():
    current_rev = 80000.00
    prior_rev = 100000.00
    growth = ((current_rev - prior_rev) / prior_rev) * 100.0
    assert round(growth, 2) == -20.00


def test_yoy_growth_zero_prior_period():
    current_rev = 50000.00
    prior_rev = 0.00
    # Safe boundary handling
    if prior_rev > 0:
        growth = ((current_rev - prior_rev) / prior_rev) * 100.0
    elif prior_rev == 0 and current_rev > 0:
        growth = 100.00
    else:
        growth = 0.00
    assert growth == 100.00


def test_customer_segmentation_tiers():
    def get_tier(spend):
        if spend >= 5000:
            return "High Spending (VIP)"
        elif spend >= 1500:
            return "Medium Spending"
        return "Low Spending"

    assert get_tier(7500.00) == "High Spending (VIP)"
    assert get_tier(5000.00) == "High Spending (VIP)"
    assert get_tier(4999.99) == "Medium Spending"
    assert get_tier(1500.00) == "Medium Spending"
    assert get_tier(1499.99) == "Low Spending"
    assert get_tier(0.00) == "Low Spending"
