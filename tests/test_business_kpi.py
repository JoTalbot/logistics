from logistics.business_kpi import snapshot_kpis


class FakeCursor:
    def __init__(self, value):
        self.value = value

    def fetchone(self):
        return (self.value,)


class FakeExecutor:
    def __init__(self):
        self.calls = []
        self.values = {
            "market_observations": 120,
            "customer_opportunities": 20,
            "priority_high": 5,
            "priority_open": 8,
            "delivery_success": 9,
            "delivery_failed": 1,
            "recurring": 7,
            "recurring_fresh": 4,
            "provider_errors": 1,
        }

    def __call__(self, sql, params=()):
        self.calls.append((sql, params))
        if "market_observations" in sql:
            value = self.values["market_observations"]
        elif "customer_opportunities" in sql:
            value = self.values["customer_opportunities"]
        elif "priority_score >=" in sql:
            value = self.values["priority_high"]
        elif "priority_status" in sql:
            value = self.values["priority_open"]
        elif "outcome = %s AND error_text" in sql:
            value = self.values["provider_errors"]
        elif "outcome = %s" in sql and params[-1] == "succeeded":
            value = self.values["delivery_success"]
        elif "outcome = %s" in sql:
            value = self.values["delivery_failed"]
        elif "recurring_demand_patterns" in sql and "freshness_score" in sql:
            value = self.values["recurring_fresh"]
        elif "recurring_demand_patterns" in sql:
            value = self.values["recurring"]
        else:
            raise AssertionError(f"unexpected SQL: {sql}")
        return FakeCursor(value)


def test_snapshot_kpis_is_tenant_scoped_and_deterministic():
    execute = FakeExecutor()
    tenant = "tenant-a"

    result = snapshot_kpis(execute, tenant)

    assert result.ingestion_volume == 120
    assert result.opportunities_created == 20
    assert result.high_priority_opportunities == 5
    assert result.open_priority_work == 8
    assert result.successful_deliveries == 9
    assert result.failed_deliveries == 1
    assert result.delivery_success_rate == 0.9
    assert result.recurring_demand_profiles == 7
    assert result.fresh_recurring_demand_profiles == 4
    assert result.provider_errors == 1
    assert all(params and params[0] == tenant for _, params in execute.calls)


def test_snapshot_kpis_has_zero_safe_delivery_rate():
    execute = FakeExecutor()
    execute.values["delivery_success"] = 0
    execute.values["delivery_failed"] = 0

    result = snapshot_kpis(execute, "tenant-b")

    assert result.delivery_success_rate == 0.0
