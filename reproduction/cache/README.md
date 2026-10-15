# Cached numerical replay

Run `replay_core.py`, `replay_completed_native.py` and `replay_v119.py` with NumPy. Paths resolve relative to this folder, independently of the original project. Anonymous counts and frozen outputs reproduce the reported comparisons; these scripts do not train ASR models, decode audio or measure latency.

The matched N+R/S+R timing experiment is complete. Its separate statistical replay is `../../matched_cost_evidence/reproduce_cost_summary.py`. The DEV final-selector fit is `../fit/fit_frozen_selector.py`. The two commands have different validation scopes from cached output replay.
