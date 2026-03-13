"""Tests for Polymarket tag-based category and region extraction."""

from app.ingestion.polymarket import (
    _extract_category_from_tags,
    _extract_region_from_tags,
)


class TestExtractCategoryFromTags:
    def test_finance_tag(self):
        tags = [{"label": "Finance", "slug": "finance"}]
        assert _extract_category_from_tags(tags) == "economic"

    def test_politics_tag(self):
        tags = [{"label": "Politics", "slug": "politics"}]
        assert _extract_category_from_tags(tags) == "geopolitical"

    def test_geopolitics_tag(self):
        tags = [{"label": "Geopolitics", "slug": "geopolitics"}]
        assert _extract_category_from_tags(tags) == "geopolitical"

    def test_world_tag(self):
        tags = [{"label": "World", "slug": "world"}]
        assert _extract_category_from_tags(tags) == "geopolitical"

    def test_crypto_tag(self):
        tags = [{"label": "Crypto", "slug": "crypto"}]
        assert _extract_category_from_tags(tags) == "economic"

    def test_climate_tag(self):
        tags = [{"label": "Climate", "slug": "climate"}]
        assert _extract_category_from_tags(tags) == "climate"

    def test_first_matching_tag_wins(self):
        tags = [
            {"label": "MicroStrategy", "slug": "microstrategy"},
            {"label": "Finance", "slug": "finance"},
            {"label": "Politics", "slug": "politics"},
        ]
        # MicroStrategy doesn't match, Finance matches first → economic
        assert _extract_category_from_tags(tags) == "economic"

    def test_no_matching_tags_returns_geopolitical(self):
        tags = [
            {"label": "MicroStrategy", "slug": "microstrategy"},
            {"label": "2025 Predictions", "slug": "2025-predictions"},
        ]
        assert _extract_category_from_tags(tags) == "geopolitical"

    def test_empty_tags(self):
        assert _extract_category_from_tags([]) == "geopolitical"

    def test_real_fixture_tags(self):
        """Test with real tags from MicroStrategy event fixture."""
        tags = [
            {"id": "120", "label": "Finance", "slug": "finance"},
            {"id": "100328", "label": "Economy", "slug": "economy"},
            {"id": "107", "label": "Business", "slug": "business"},
            {"id": "21", "label": "Crypto", "slug": "crypto"},
        ]
        assert _extract_category_from_tags(tags) == "economic"


class TestExtractRegionFromTags:
    def test_france_tag(self):
        tags = [{"label": "France", "slug": "france"}]
        assert _extract_region_from_tags(tags) == "Europe"

    def test_china_tag(self):
        tags = [{"label": "China", "slug": "china"}]
        assert _extract_region_from_tags(tags) == "Asia-Pacific"

    def test_india_tag(self):
        tags = [{"label": "India", "slug": "india"}]
        assert _extract_region_from_tags(tags) == "Asia-Pacific"

    def test_uk_tag(self):
        tags = [{"label": "uk", "slug": "uk"}]
        assert _extract_region_from_tags(tags) == "Europe"

    def test_nato_tag(self):
        tags = [{"label": "nato", "slug": "nato"}]
        assert _extract_region_from_tags(tags) == "Europe"

    def test_no_region_tag(self):
        tags = [{"label": "Finance", "slug": "finance"}]
        assert _extract_region_from_tags(tags) == "Global"

    def test_empty_tags(self):
        assert _extract_region_from_tags([]) == "Global"
