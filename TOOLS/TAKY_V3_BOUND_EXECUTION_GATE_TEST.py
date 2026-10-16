#!/usr/bin/env python3
"""Verify signed context delivery never silently turns into an unacknowledged model call."""
import TAKY_CLI_DETACHED_E2E_CANDIDATE as cli
ids=("fbc544e8b18342df929ed0287454cd53","336cab100f824164aa7c33f60f962bd1")
for taskid in ids:
    try:
        cli.get_task(taskid)
        raise AssertionError("CONTEXT_BOUND_EXECUTION_WAS_INCORRECTLY_ALLOWED")
    except RuntimeError as ex:
        assert str(ex)=="CONTEXT_BOUND_PROVIDER_DELIVERY_NOT_IMPLEMENTED",str(ex)
print("BOUND_CONTEXT_NOT_CONSUMED_PROVIDER_GATE_PASS BOTH_ACTORS NO_MODEL_CALLS")
