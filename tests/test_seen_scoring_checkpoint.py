"""Tests for seen checkpointing behavior and vocabulary change preservation."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.aggregator import aggregate
from src.config import ObservatoryConfig, PathsConfig, ScoringConfig
from src.feeds import hash_url

FIXTURES = Path(__file__).parent / "fixtures"


def _create_test_config(tmp_path: Path, bib_tag: str = "governance") -> ObservatoryConfig:
    bib_dir = tmp_path / "bibliographies"
    bib_dir.mkdir(parents=True, exist_ok=True)
    (bib_dir / "test.yaml").write_text(
        '- title: "Test"\n  author: "Author"\n  year: 2020\n'
        '  relevance: "' + "A" * 50 + '"\n'
        f'  tags: ["{bib_tag}"]\n  collections: ["systems-thinking"]\n'
    )

    feeds_dir = tmp_path / "feeds"
    feeds_dir.mkdir(parents=True, exist_ok=True)

    opml = tmp_path / "subscriptions.opml"
    opml.write_text(
        '<?xml version="1.0"?><opml version="2.0"><head/><body>'
        '<outline text="systems-thinking">'
        '<outline type="rss" title="Feed" '
        'xmlUrl="https://example.com/feed.xml" htmlUrl="https://example.com/"/>'
        "</outline></body></opml>"
    )

    return ObservatoryConfig(
        scoring=ScoringConfig(min_score=0.01),
        paths=PathsConfig(
            bibliographies_dir=str(bib_dir),
            feeds_dir=str(feeds_dir),
            opml_path=str(opml),
            seen_path=str(feeds_dir / "seen.json"),
            surfaced_path=str(feeds_dir / "surfaced.json"),
            archive_dir=str(feeds_dir / "archive"),
            essays_index_path=str(tmp_path / "nonexistent-essays.json"),
        ),
    )


class TestSeenScoringCheckpoint:
    @patch("src.aggregator.fetch_all_feeds")
    def test_rejected_item_preserved_for_vocabulary_change(self, mock_fetch, tmp_path):
        """Verify that an item rejected due to vocabulary mismatch is not checkpointed in seen.json,

        and can surface on a later run after the vocabulary changes.
        """
        config = _create_test_config(tmp_path, bib_tag="governance")
        seen_path = Path(config.paths.seen_path)
        surfaced_path = Path(config.paths.surfaced_path)

        epistemology_item = {
            "title": "Epistemology methods",
            "url": "https://example.com/epistemology-methods",
            "summary": "Epistemology methods in practice",
            "author": "Author",
            "published": "2026-04-01",
            "collection": "systems-thinking",
            "feed_title": "Feed",
        }
        mock_fetch.return_value = {"systems-thinking": [epistemology_item]}

        # Run 1: Vocabulary is {"governance"}. Item title/summary is "Epistemology methods".
        summary1 = aggregate(config)
        assert summary1["items_fetched"] == 1
        assert summary1["items_new"] == 1
        assert summary1["items_scored"] == 0

        # Checkpoint assertion: seen.json must NOT contain the item's URL hash
        seen1 = json.loads(seen_path.read_text()) if seen_path.exists() else {}
        url_hash = hash_url("https://example.com/epistemology-methods")
        assert url_hash not in seen1

        surfaced1 = json.loads(surfaced_path.read_text()) if surfaced_path.exists() else []
        assert len(surfaced1) == 0

        # Run 2: Change bibliography tag to "epistemology"
        (Path(config.paths.bibliographies_dir) / "test.yaml").write_text(
            '- title: "Test"\n  author: "Author"\n  year: 2020\n'
            '  relevance: "' + "A" * 50 + '"\n'
            '  tags: ["epistemology"]\n  collections: ["systems-thinking"]\n'
        )

        summary2 = aggregate(config)
        assert summary2["items_fetched"] == 1
        assert summary2["items_new"] == 1
        assert summary2["items_scored"] == 1

        surfaced2 = json.loads(surfaced_path.read_text())
        assert len(surfaced2) == 1
        assert surfaced2[0]["title"] == "Epistemology methods"

        # Now the URL hash should be saved in seen.json
        seen2 = json.loads(seen_path.read_text())
        assert url_hash in seen2

    @patch("src.aggregator.fetch_all_feeds")
    def test_intra_batch_duplicates_filtered_within_run(self, mock_fetch, tmp_path):
        """Verify duplicate URLs within a single fetched batch are processed only once."""
        config = _create_test_config(tmp_path, bib_tag="governance")
        item = {
            "title": "Governance systems overview",
            "url": "https://example.com/gov-overview",
            "summary": "About governance in complex systems.",
            "author": "Author",
            "published": "2026-04-01",
            "collection": "systems-thinking",
            "feed_title": "Feed",
        }
        # Provide two identical items in the same batch
        mock_fetch.return_value = {"systems-thinking": [item, item.copy()]}

        summary = aggregate(config)
        assert summary["items_fetched"] == 2
        assert summary["items_new"] == 1
        assert summary["items_scored"] == 1

        surfaced = json.loads(Path(config.paths.surfaced_path).read_text())
        assert len(surfaced) == 1

    @patch("src.aggregator.fetch_all_feeds")
    def test_pre_existing_seen_entries_remain_authoritative(self, mock_fetch, tmp_path):
        """Verify pre-existing entries in seen.json remain authoritative and filter items."""
        config = _create_test_config(tmp_path, bib_tag="governance")
        seen_path = Path(config.paths.seen_path)

        url = "https://example.com/already-seen"
        existing_hash = hash_url(url)
        seen_path.write_text(json.dumps({existing_hash: "2026-01-01"}))

        mock_fetch.return_value = {
            "systems-thinking": [
                {
                    "title": "Governance systems overview",
                    "url": url,
                    "summary": "About governance systems.",
                    "author": "Author",
                    "published": "2026-04-01",
                    "collection": "systems-thinking",
                    "feed_title": "Feed",
                }
            ]
        }

        summary = aggregate(config)
        assert summary["items_fetched"] == 1
        assert summary["items_new"] == 0
        assert summary["items_scored"] == 0

        # Existing timestamp remains unchanged
        seen_data = json.loads(seen_path.read_text())
        assert seen_data[existing_hash] == "2026-01-01"

    @patch("src.aggregator.fetch_all_feeds")
    def test_surfaced_item_not_duplicated_on_later_run(self, mock_fetch, tmp_path):
        """Verify an item that surfaced on run 1 is recorded in seen.json and filtered on run 2."""
        config = _create_test_config(tmp_path, bib_tag="governance")
        item = {
            "title": "Governance in action",
            "url": "https://example.com/gov-action",
            "summary": "About governance methods.",
            "author": "Author",
            "published": "2026-04-01",
            "collection": "systems-thinking",
            "feed_title": "Feed",
        }
        mock_fetch.return_value = {"systems-thinking": [item]}

        # Run 1
        summary1 = aggregate(config)
        assert summary1["items_scored"] == 1
        assert summary1["items_surfaced"] == 1

        # Run 2 with same item
        summary2 = aggregate(config)
        assert summary2["items_new"] == 0
        assert summary2["items_scored"] == 0

        surfaced = json.loads(Path(config.paths.surfaced_path).read_text())
        assert len(surfaced) == 1

    @patch("src.aggregator.fetch_all_feeds")
    def test_corrupt_surfaced_json_prevents_seen_update(self, mock_fetch, tmp_path):
        """Verify corrupt surfaced.json fails closed and seen.json is not updated."""
        config = _create_test_config(tmp_path, bib_tag="governance")
        surfaced_path = Path(config.paths.surfaced_path)
        seen_path = Path(config.paths.seen_path)

        surfaced_path.write_text("corrupt json [[[")
        seen_path.write_text(json.dumps({"initial": "2026-01-01"}))

        item = {
            "title": "Governance item",
            "url": "https://example.com/gov-item",
            "summary": "About governance.",
            "author": "Author",
            "published": "2026-04-01",
        }
        mock_fetch.return_value = {"systems-thinking": [item]}

        with pytest.raises(ValueError, match="Corrupt JSON in surfaced file"):
            aggregate(config)

        # seen.json must remain unchanged
        seen_content = seen_path.read_text()
        assert json.loads(seen_content) == {"initial": "2026-01-01"}
