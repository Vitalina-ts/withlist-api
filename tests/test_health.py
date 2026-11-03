from datetime import datetime
from unittest.mock import Mock

import pytest
from redis.exceptions import ConnectionError


@pytest.mark.parametrize("redis_available", [True, False])
def test_health_without_database(api, client, monkeypatch, redis_available):
    import database

    def forbid_database(*args, **kwargs):
        raise AssertionError("Health must not connect to PostgreSQL")

    monkeypatch.setattr(database.engine, "connect", forbid_database)
    redis = Mock()
    redis.ping.side_effect = None if redis_available else ConnectionError("offline")
    monkeypatch.setattr(api, "redis_client", redis)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["redis"] == ("healthy" if redis_available else "unhealthy")
    assert datetime.fromisoformat(body["timestamp"])
    redis.ping.assert_called_once_with()
