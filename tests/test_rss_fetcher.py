from unittest.mock import MagicMock, patch

from app.models import Source


def make_source(name="Test RSS", url="https://example.com/feed", type="rss") -> Source:
    s = Source()
    s.id = 1
    s.name = name
    s.url = url
    s.type = type
    s.enabled = True
    return s


MOCK_FEED_XML = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Defect Detection with Vision Transformer</title>
      <link>https://example.com/article/1</link>
      <description>A new approach to industrial defect detection using ViT.</description>
      <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
    </item>
    <item>
      <title>TensorRT Optimization Guide for Jetson Orin</title>
      <link>https://example.com/article/2</link>
      <description>How to optimize models with TensorRT on Jetson Orin platform.</description>
      <pubDate>Tue, 02 Jan 2024 00:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""


class TestRSSFetcher:
    def test_parse_feed_entries(self):
        import feedparser
        feed = feedparser.parse(MOCK_FEED_XML)
        assert len(feed.entries) == 2
        assert feed.entries[0].title == "Defect Detection with Vision Transformer"
        assert feed.entries[1].link == "https://example.com/article/2"

    def test_fetch_rss_inserts_items(self):
        from app.services.fetchers.rss_fetcher import fetch_rss

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        source = make_source()

        with patch("feedparser.parse") as mock_parse:
            mock_feed = MagicMock()
            mock_feed.bozo = False
            mock_feed.entries = [
                MagicMock(
                    title="Test Article",
                    link="https://example.com/test",
                    id="https://example.com/test",
                    summary="A test article about defect detection.",
                    published_parsed=(2024, 1, 1, 0, 0, 0, 0, 1, 0),
                    author="Test Author",
                )
            ]
            mock_parse.return_value = mock_feed

            count = fetch_rss(db, source)

        assert count == 1
        db.add.assert_called_once()

    def test_fetch_rss_skips_existing(self):
        from app.services.fetchers.rss_fetcher import fetch_rss

        existing_item = MagicMock()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing_item

        source = make_source()

        with patch("feedparser.parse") as mock_parse:
            mock_feed = MagicMock()
            mock_feed.bozo = False
            mock_feed.entries = [
                MagicMock(
                    title="Existing Article",
                    link="https://example.com/existing",
                    id="https://example.com/existing",
                    summary="Already in DB",
                    published_parsed=None,
                    author=None,
                )
            ]
            mock_parse.return_value = mock_feed

            count = fetch_rss(db, source)

        assert count == 0
        db.add.assert_not_called()

    def test_fetch_rss_handles_error(self):
        from app.services.fetchers.rss_fetcher import fetch_rss

        db = MagicMock()
        source = make_source()

        with patch("feedparser.parse", side_effect=Exception("Network error")):
            count = fetch_rss(db, source)

        assert count == 0
