"""
V324 - test_v324_item_node_extension.py
ItemNodeExtension + DRSEGraphAdapter 테스트 (12개)
"""
import pytest
from literary_system.graph.item_node_extension import (
    ExtendedItemNode, ItemNodeExtension,
)
from literary_system.drse.drse_graph_adapter import DRSEGraphAdapter


# ════════════════════════════════════════════════════════════════════
# 1. ExtendedItemNode DTO
# ════════════════════════════════════════════════════════════════════

class TestExtendedItemNode:
    def test_defaults(self):
        item = ExtendedItemNode(item_id="item_1", name="검")
        assert item.owner_id is None
        assert item.location_id is None
        assert item.is_consumable is False
        assert item.quantity == 1

    def test_custom_fields(self):
        item = ExtendedItemNode(
            item_id="potion_1", name="물약",
            owner_id="char_a", location_id="loc_b",
            is_consumable=True, quantity=3,
        )
        assert item.owner_id == "char_a"
        assert item.is_consumable is True
        assert item.quantity == 3

    def test_to_dict(self):
        item = ExtendedItemNode(item_id="x", name="X")
        d = item.to_dict()
        assert "item_id" in d and "name" in d


# ════════════════════════════════════════════════════════════════════
# 2. ItemNodeExtension
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def ext():
    return ItemNodeExtension()

class TestItemNodeExtension:
    def test_register_item(self, ext):
        item = ExtendedItemNode(item_id="sword_1", name="장검")
        ext.register(item)
        assert ext.get_item("sword_1") is not None

    def test_transfer_ownership(self, ext):
        item = ExtendedItemNode(item_id="key_1", name="열쇠", owner_id="char_a")
        ext.register(item)
        result = ext.transfer_ownership("key_1", from_id="char_a", to_id="char_b")
        assert result is True
        assert ext.get_item("key_1").owner_id == "char_b"

    def test_transfer_wrong_owner_fails(self, ext):
        item = ExtendedItemNode(item_id="ring_1", name="반지", owner_id="char_a")
        ext.register(item)
        result = ext.transfer_ownership("ring_1", from_id="char_x", to_id="char_b")
        assert result is False

    def test_validate_acquire_same_location(self, ext):
        """캐릭터와 아이템이 같은 위치면 획득 가능."""
        item = ExtendedItemNode(item_id="map_1", name="지도", location_id="loc_forest")
        ext.register(item)
        result = ext.validate_acquire(char_location_id="loc_forest", item_id="map_1")
        assert result is True

    def test_validate_acquire_different_location_fails(self, ext):
        item = ExtendedItemNode(item_id="gem_1", name="보석", location_id="loc_castle")
        ext.register(item)
        result = ext.validate_acquire(char_location_id="loc_market", item_id="gem_1")
        assert result is False

    def test_get_item_unknown_returns_none(self, ext):
        assert ext.get_item("nonexistent") is None


# ════════════════════════════════════════════════════════════════════
# 3. DRSEGraphAdapter
# ════════════════════════════════════════════════════════════════════

class TestDRSEGraphAdapter:
    def test_no_rgs_returns_default_density(self):
        adapter = DRSEGraphAdapter()
        density = adapter.compute_relational_density(rgs=None, char_ids=["a", "b"])
        assert 0.0 <= density <= 1.0

    def test_no_rgs_returns_default_arc_pressure(self):
        adapter = DRSEGraphAdapter()
        pressure = adapter.compute_arc_pressure(rgs=None, arc_id="arc_1")
        assert 0.0 <= pressure <= 1.0

    def test_extract_drse_inputs_no_rgs(self):
        adapter = DRSEGraphAdapter()
        bundle = adapter.extract_drse_inputs(rgs=None, scene_id="s1")
        assert bundle is not None
        assert hasattr(bundle, "relational_density")
        assert hasattr(bundle, "arc_pressure")
