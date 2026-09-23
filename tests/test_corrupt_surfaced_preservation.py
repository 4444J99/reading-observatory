"""Tests for preserving surfaced-feed and archive data when stored JSON is corrupt or malformed."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.aggregator import aggregate, archive_expired
from src.config import ObservatoryConfig, PathsConfig, ScoringConfig

FIXTURES = Path(__file__).parent / "fixtures"


def _create_test_config(tmp_path: Path) -> ObservatoryConfig:
    bib_dir = tmp_path / "bibliographies"
    bib_dir.mkdir(exist_ok=True)
    (bib_dir / "test.yaml").write_text(
        '- title: "Test"\n  author: "Author"\n  year: 2020\n'
        '  relevance: "' + "A" * 50 + '"\n'
        '  tags: ["governance"]\n  collections: ["systems-thinking"]\n'
    )

    feeds_dir = tmp_path / "feeds"
    feeds_dir.mkdir(exist_ok=True)

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
            essays_index_path=str(FIXTURES / "essays-index-sample.json"),
        ),
    )


class TestCorruptSurfacedPreservation:
    @patch("src.aggregator.fetch_all_feeds")
    def test_malformed_surfaced_json_rejected(self, mock_fetch, tmp_path):
        config = _create_test_config(tmp_path)
        surfaced_path = Path(config.paths.surfaced_path)
        archive_dir = Path(config.paths.archive_dir)
        seen_path = Path(config.paths.seen_path)

        corrupt_content = "{\n  \"incomplete\": [json data...\n"
        surfaced_path.write_text(corrupt_content)
        seen_content = json.dumps({"existing_hash": "2026-01-01"})
        seen_path.write_text(seen_content)

        mock_fetch.return_value = {
            "systems-thinking": [
                {
                    "title": "Governance Systems",
                    "url": "https://example.com/gov-1",
                    "summary": "About governance systems thinking.",
                    "author": "Author",
                    "published": "2026-04-01",
                }
            ]
        }

        with pytest.raises(ValueError, match="Corrupt JSON in surfaced file"):
            aggregate(config)

        # Verify bytes on disk remain completely unchanged
        assert surfaced_path.read_text() == corrupt_content
        assert seen_path.read_text() == seen_content
        assert not archive_dir.exists() or list(archive_dir.glob("*.json")) == []

    @patch("src.aggregator.fetch_all_feeds")
    def test_valid_json_wrong_root_type_rejected(self, mock_fetch, tmp_path):
        config = _create_test_config(tmp_path)
        surfaced_path = Path(config.paths.surfaced_path)
        seen_path = Path(config.paths.seen_path)

        wrong_root_content = json.dumps({"title": "not a list"})
        surfaced_path.write_text(wrong_root_content)
        seen_content = json.dumps({"existing_hash": "2026-01-01"})
        seen_path.write_text(seen_content)

        mock_fetch.return_value = {
            "systems-thinking": [
                {
                    "title": "Governance Systems",
                    "url": "https://example.com/gov-1",
                    "summary": "About governance systems thinking.",
                    "author": "Author",
                    "published": "2026-04-01",
                }
            ]
        }

        with pytest.raises(ValueError, match="Invalid container shape in surfaced file"):
            aggregate(config)

        assert surfaced_path.read_text() == wrong_root_content
        assert seen_path.read_text() == seen_content

    @patch("src.aggregator.fetch_all_feeds")
    def test_invalid_record_shape_rejected(self, mock_fetch, tmp_path):
        config = _create_test_config(tmp_path)
        surfaced_path = Path(config.paths.surfaced_path)
        seen_path = Path(config.paths.seen_path)

        invalid_record_content = json.dumps([{"title": "Valid"}, "string record instead of dict"])
        surfaced_path.write_text(invalid_record_content)
        seen_content = json.dumps({"existing_hash": "2026-01-01"})
        seen_path.write_text(seen_content)

        mock_fetch.return_value = {
            "systems-thinking": [
                {
                    "title": "Governance Systems",
                    "url": "https://example.com/gov-1",
                    "summary": "About governance systems thinking.",
                    "author": "Author",
                    "published": "2026-04-01",
                }
            ]
        }

        with pytest.raises(ValueError, match="Invalid record shape in surfaced file"):
            aggregate(config)

        assert surfaced_path.read_text() == invalid_record_content
        assert seen_path.read_text() == seen_content

    @patch("src.aggregator.fetch_all_feeds")
    def test_corrupt_existing_daily_archive_rejected(self, mock_fetch, tmp_path):
        config = _create_test_config(tmp_path)
        surfaced_path = Path(config.paths.surfaced_path)
        archive_dir = Path(config.paths.archive_dir)
        seen_path = Path(config.paths.seen_path)
        archive_dir.mkdir(parents=True, exist_ok=True)

        old_date = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d")
        surfaced_data = [{"title": "Old Governance", "surfaced_date": old_date, "url": "https://example.com/old"}]
        surfaced_content = json.dumps(surfaced_data)
        surfaced_path.write_text(surfaced_content)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        corrupt_archive_path = archive_dir / f"archived-{today}.json"
        corrupt_archive_content = "corrupt archive json {{{"
        corrupt_archive_path.write_text(corrupt_archive_content)

        seen_content = json.dumps({"existing_hash": "2026-01-01"})
        seen_path.write_text(seen_content)

        mock_fetch.return_value = {
            "systems-thinking": [
                {
                    "title": "Governance Systems",
                    "url": "https://example.com/gov-1",
                    "summary": "About governance systems thinking.",
                    "author": "Author",
                    "published": "2026-04-01",
                }
            ]
        }

        with pytest.raises(ValueError, match="Corrupt JSON in archive file"):
            aggregate(config)

        # Verify disk bytes remain unchanged
        assert surfaced_path.read_text() == surfaced_content
        assert corrupt_archive_path.read_text() == corrupt_archive_content
        assert seen_path.read_text() == seen_content

    @patch("src.aggregator.fetch_all_feeds")
    def test_missing_surfaced_file_first_run_behavior(self, mock_fetch, tmp_path):
        config = _create_test_config(tmp_path)
        surfaced_path = Path(config.paths.surfaced_path)
        assert not surfaced_path.exists()

        mock_fetch.return_value = {
            "systems-thinking": [
                {
                    "title": "Governance Systems",
                    "url": "https://example.com/gov-1",
                    "summary": "About governance systems thinking.",
                    "author": "Author",
                    "published": "2026-04-01",
                }
            ]
        }

        summary = aggregate(config)
        assert summary["items_surfaced"] == 1
        assert surfaced_path.exists()
        data = json.loads(surfaced_path.read_text())
        assert len(data) == 1
        assert data[0]["title"] == "Governance Systems"

    def test_valid_expired_item_archival(self, tmp_path):
        surfaced_path = tmp_path / "surfaced.json"
        archive_dir = tmp_path / "archive"
        old_date = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d")
        recent_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        surfaced_items = [
            {"title": "Old Item", "surfaced_date": old_date, "url": "https://example.com/old"},
            {"title": "Recent Item", "surfaced_date": recent_date, "url": "https://example.com/recent"},
        ]
        surfaced_path.write_text(json.dumps(surfaced_items))

        archived_count = archive_expired(surfaced_path, archive_dir, expiry_days=30)
        assert archived_count == 1

        remaining = json.loads(surfaced_path.read_text())
        assert len(remaining) == 1
        assert remaining[0]["title"] == "Recent Item"

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        archive_file = archive_dir / f"archived-{today}.json"
        assert archive_file.exists()
        archived_items = json.loads(archive_file.read_text())
        assert len(archived_items) == 1
        assert archived_items[0]["title"] == "Old Item"

    @patch("src.aggregator.fetch_all_feeds")
    def test_valid_aggregation_with_existing_surfaced(self, mock_fetch, tmp_path):
        config = _create_test_config(tmp_path)
        surfaced_path = Path(config.paths.surfaced_path)
        recent_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        existing_items = [
            {
                "title": "Existing Governance",
                "url": "https://example.com/existing",
                "relevance_score": 0.8,
                "surfaced_date": recent_date,
            }
        ]
        surfaced_path.write_text(json.dumps(existing_items))

        mock_fetch.return_value = {
            "systems-thinking": [
                {
                    "title": "New Governance Systems",
                    "url": "https://example.com/new-gov",
                    "summary": "About governance systems thinking.",
                    "author": "Author",
                    "published": "2026-04-01",
                }
            ]
        }

        summary = aggregate(config)
        assert summary["items_surfaced"] == 2

        surfaced_data = json.loads(surfaced_path.read_text())
        assert len(surfaced_data) == 2
        titles = [item["title"] for item in surfaced_data]
        assert "Existing Governance" in titles
        assert "New Governance Systems" in titles
