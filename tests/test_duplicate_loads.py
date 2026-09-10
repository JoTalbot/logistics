from uuid import uuid4

import pytest

from logistics.duplicate_loads import find_duplicate_load_groups


def test_duplicate_detection_is_tenant_scoped_and_deterministic():
    tenant_id = uuid4()
    left, right = uuid4(), uuid4()

    class Result:
        def fetchall(self):
            return [(left, right)]

    class Conn:
        def __init__(self):
            self.params = None
        def execute(self, sql, params=()):
            self.params = params
            return Result()

    conn = Conn()
    assert find_duplicate_load_groups(conn, tenant_id=tenant_id, window_hours=48) == [[left, right]]
    assert conn.params[0] == tenant_id


def test_invalid_window_rejected():
    class Conn:
        def execute(self, *args, **kwargs):
            raise AssertionError("database must not be queried")
    with pytest.raises(ValueError, match="window_hours"):
        find_duplicate_load_groups(Conn(), tenant_id=uuid4(), window_hours=0)
