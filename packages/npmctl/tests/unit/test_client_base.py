from __future__ import annotations

from npmctl.client.base import _extract_token


def test_extract_token_accepts_numeric_expiry() -> None:
    assert _extract_token({"token": "abc", "expires": 1893456000}) == ("abc", 1893456000)


def test_extract_token_accepts_iso_expiry() -> None:
    token, expires = _extract_token({"token": "abc", "expires": "2030-01-01T00:00:00.000Z"})

    assert token == "abc"
    assert expires == 1893456000
