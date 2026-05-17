"""Unit tests for src/guardrails/kill_switch.py — ADR-0025, spec 16 §3.6."""

import threading

import pytest

import src.guardrails.kill_switch as ks
from src.domain.exceptions import KillSwitchActivated


@pytest.fixture(autouse=True)
def reset_kill_switch():
    """Ensure kill-switch is deactivated before and after every test."""
    ks.deactivate(deactivated_by="test-setup")
    yield
    ks.deactivate(deactivated_by="test-teardown")


@pytest.mark.unit
class TestKillSwitch:
    def test_inactive_by_default(self) -> None:
        assert not ks.is_active()

    def test_activate_sets_active(self) -> None:
        ks.activate(activated_by="sre-oncall", reason="audit write failure")
        assert ks.is_active()

    def test_enforce_raises_when_active(self) -> None:
        ks.activate(activated_by="sre-oncall", reason="audit write failure")
        with pytest.raises(KillSwitchActivated) as exc_info:
            ks.enforce()
        assert "sre-oncall" in str(exc_info.value)

    def test_enforce_passes_when_inactive(self) -> None:
        ks.enforce()  # must not raise

    def test_deactivate_clears_switch(self) -> None:
        ks.activate(activated_by="test", reason="test")
        ks.deactivate(deactivated_by="operator")
        assert not ks.is_active()
        ks.enforce()  # must not raise after deactivation

    def test_thread_safety_concurrent_enforce(self) -> None:
        """Multiple threads calling enforce() simultaneously must not race."""
        errors: list[Exception] = []

        def worker() -> None:
            try:
                ks.enforce()
            except KillSwitchActivated:
                pass
            except Exception as exc:
                errors.append(exc)

        ks.activate(activated_by="stress-test", reason="concurrent test")
        threads = [threading.Thread(target=worker) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety violation: {errors}"
