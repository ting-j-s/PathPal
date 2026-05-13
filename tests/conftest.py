"""
pytest fixtures for PathPal tests
"""
import json
import pytest
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def data_dir():
    return DATA_DIR


@pytest.fixture(scope="module")
def destinations():
    with open(DATA_DIR / "destinations.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def internal_maps():
    with open(DATA_DIR / "internal_maps.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def internal_nodes():
    with open(DATA_DIR / "internal_nodes.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def internal_edges():
    with open(DATA_DIR / "internal_edges.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def facilities():
    with open(DATA_DIR / "facilities.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def users():
    with open(DATA_DIR / "users.json", "r", encoding="utf-8") as f:
        return json.load(f)
