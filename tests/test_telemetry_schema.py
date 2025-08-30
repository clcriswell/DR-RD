from utils.telemetry_schema import validate, upcast, CURRENT_SCHEMA_VERSION


def test_validate_adds_version_ts_and_drops_pii():
    ev = validate({"event": "start_run", "run_id": "r1", "email": "x@example.com"})
    assert ev["schema_version"] == CURRENT_SCHEMA_VERSION
    assert "ts" in ev
    assert "email" not in ev


def test_upcast_noop_for_v1():
    ev = {"event": "start_run", "run_id": "r1", "schema_version": CURRENT_SCHEMA_VERSION}
    assert upcast(ev)["schema_version"] == CURRENT_SCHEMA_VERSION
