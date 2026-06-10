import pytest
from app.models import Item, Keyword
from app.services.scoring_service import (
    compute_relevance_score,
    compute_reproduce_score,
    compute_content_score,
    compute_monetization_score,
    compute_total_score,
    score_item,
)


def make_keyword(keyword: str, weight: float = 2.0, category: str = "test") -> Keyword:
    kw = Keyword()
    kw.id = 1
    kw.keyword = keyword
    kw.weight = weight
    kw.category = category
    kw.enabled = True
    return kw


def make_item(title: str, summary: str = "", item_type: str = "article", stars: int = None) -> Item:
    item = Item()
    item.id = 1
    item.title = title
    item.summary_raw = summary
    item.item_type = item_type
    item.stars = stars
    item.url = "https://example.com"
    return item


class TestRelevanceScore:
    def test_keyword_in_title_doubles(self):
        item = make_item("defect detection with YOLO")
        kw = make_keyword("defect detection", weight=2.0)
        score, matched = compute_relevance_score(item, [kw])
        # title hit => weight * 2 + industrial bonus
        assert score > 4.0
        assert "defect detection" in matched

    def test_keyword_in_summary_only(self):
        item = make_item("Random Title", summary="anomaly detection benchmark")
        kw = make_keyword("anomaly detection", weight=2.0)
        score, matched = compute_relevance_score(item, [kw])
        assert score > 0
        assert "anomaly detection" in matched

    def test_disabled_keyword_ignored(self):
        item = make_item("YOLO object detection")
        kw = make_keyword("YOLO", weight=3.0)
        kw.enabled = False
        score, matched = compute_relevance_score(item, [kw])
        assert score == 0.0
        assert matched == []

    def test_multiple_keywords(self):
        item = make_item("Jetson TensorRT deployment")
        kws = [
            make_keyword("Jetson", weight=3.0, category="edge_ai"),
            make_keyword("TensorRT", weight=2.5, category="edge_ai"),
        ]
        score, matched = compute_relevance_score(item, kws)
        assert len(matched) == 2
        assert score > 5.0

    def test_no_match(self):
        item = make_item("Cooking recipes for pasta")
        kw = make_keyword("defect detection")
        score, matched = compute_relevance_score(item, [kw])
        assert score == 0.0
        assert matched == []


class TestReproduceScore:
    def test_github_repo_bonus(self):
        item = make_item("", item_type="github_repo")
        score = compute_reproduce_score(item)
        assert score >= 3.0

    def test_code_keyword(self):
        item = make_item("Pretrained model weights for defect detection")
        score = compute_reproduce_score(item)
        assert score >= 2.0

    def test_star_bonuses(self):
        item_10k = make_item("", stars=15000, item_type="github_repo")
        item_1k = make_item("", stars=1500, item_type="github_repo")
        item_100 = make_item("", stars=500, item_type="github_repo")
        assert compute_reproduce_score(item_10k) > compute_reproduce_score(item_1k)
        assert compute_reproduce_score(item_1k) > compute_reproduce_score(item_100)


class TestContentScore:
    def test_tutorial_keyword(self):
        item = make_item("Tutorial: How to deploy TensorRT on Jetson")
        score = compute_content_score(item)
        assert score >= 2.0

    def test_high_stars(self):
        item = make_item("", stars=20000)
        score = compute_content_score(item)
        assert score >= 5.0


class TestMonetizationScore:
    def test_industrial_keyword(self):
        item = make_item("Industrial defect inspection automation system")
        score = compute_monetization_score(item)
        assert score >= 3.0

    def test_local_deployment(self):
        item = make_item("Self-hosted local LLM deployment guide")
        score = compute_monetization_score(item)
        assert score >= 2.0


class TestTotalScore:
    def test_weighted_sum(self):
        total = compute_total_score(10.0, 8.0, 6.0, 4.0)
        expected = 10 * 0.45 + 8 * 0.25 + 6 * 0.2 + 4 * 0.1
        assert abs(total - expected) < 0.001

    def test_score_item_sets_fields(self):
        item = make_item("defect detection GitHub repo with pretrained weights", item_type="github_repo")
        kws = [
            make_keyword("defect detection", weight=3.0),
            make_keyword("pretrained", weight=1.5),
        ]
        result = score_item(item, kws)
        assert result.total_score > 0
        assert result.relevance_score > 0
        assert result.matched_keywords is not None
