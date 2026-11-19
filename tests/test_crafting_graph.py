import pytest
from gameplay import crafting_graph as mod

CASES = [
    ("cycle", 'm.has_cycle({"a": ["b"], "b": ["a"]}) is True'),
    ("topo", 'm.topo_order({"a": ["b"], "b": []}) == ["b", "a"]'),
    ("rollback", 'm.rollback_materials((1, 2), (3, 4)) == (4, 6)'),
    ("batch", 'm.batch_deduct(10, 2, 3) == 4'),
    ("reserve", 'm.reserve(5, 2) == 3'),
    ("round", 'm.round_qty(0.5) == 1'),
    ("byproduct", 'm.byproduct(1, 2) == 3'),
    ("cache", 'm.cache_valid(1, 1) is True'),
    ("tier", 'm.station_tier(2, 3) is True'),
    ("async", 'm.async_order([3, 1]) == [1, 3]'),
    ("recursion", 'm.recursion_limit(2, 3) is True'),
    ("same", 'm.same_table(1, 1) is True'),
    ("refund", 'm.refund_all((1, 2), (3, 4)) == (4, 6)'),
    ("recipe", 'm.recipe_valid({"a": 1}, {"a": 1, "b": 2}) is True'),
    ("depth", 'm.depth_limit(1, 2) is True')
]

@pytest.mark.parametrize("name,expr", CASES, ids=[c[0] for c in CASES])
def test_contract(name, expr):
    assert eval(expr, {"m": mod, "approx": pytest.approx})
