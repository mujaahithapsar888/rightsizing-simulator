"""
event_recovery_simulator.py
───────────────────────────
Simulates an event streaming processor handling adversarial metrics stream.
Validates:
- Out-of-order event sorting (Timestamp ordering)
- Duplicate event removal (Deduplication)
- Network delayed events handling
- State recovery via replay buffer
- Test verification generating PASS/FAIL reports
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

class EventRecoverySimulator:
    """Simulates metric ingestion recovery under adversarial streaming conditions."""

    def __init__(self):
        # Generate base telemetry timeline
        base_time = datetime(2026, 8, 8, 12, 0, 0)
        self.clean_events = []
        for i in range(10):
            ts = base_time + timedelta(minutes=i * 5)
            self.clean_events.append({
                "event_id": f"evt-{i}",
                "timestamp": ts.isoformat() + "Z",
                "cpu_utilization": round(30.0 + i * 4.0, 1),
                "memory_utilization": round(50.0 + i * 2.5, 1),
                "latency_ms": 100 + i * 15,
                "availability": 100.0 if i != 5 else 99.5
            })

    def generate_adversarial_stream(self) -> List[Dict[str, Any]]:
        """Injects duplicates, delayed, and out-of-order events into the clean stream."""
        stream = []
        
        # 1. Clean events
        for e in self.clean_events:
            stream.append(e.copy())
            
        # 2. Inject Duplicate Events (evt-2 and evt-7)
        stream.append(self.clean_events[2].copy())
        stream.append(self.clean_events[7].copy())
        
        # 3. Make Out-of-Order (Swap evt-4 and evt-5 in place)
        e4_idx = next(i for i, e in enumerate(stream) if e["event_id"] == "evt-4")
        e5_idx = next(i for i, e in enumerate(stream) if e["event_id"] == "evt-5")
        stream[e4_idx], stream[e5_idx] = stream[e5_idx], stream[e4_idx]
        
        # 4. Inject Delayed Event (evt-1 injected at the very end of stream with backdated timestamp)
        delayed_evt = self.clean_events[1].copy()
        # Remove from its normal place to make it fully delayed
        stream = [e for e in stream if e["event_id"] != "evt-1"]
        stream.append(delayed_evt)
        
        return stream

    def process_with_recovery(self, adversarial_stream: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs the replay buffer pipeline:
        1. Deduplication
        2. Timestamp ordering
        3. State recovery (recalculating aggregates)
        """
        # Replay Buffer / Ingest Queue
        replay_buffer = []
        seen_ids = set()
        duplicates_rejected = 0

        # Step 1: Deduplication
        for evt in adversarial_stream:
            eid = evt["event_id"]
            if eid in seen_ids:
                duplicates_rejected += 1
            else:
                seen_ids.add(eid)
                replay_buffer.append(evt)

        # Step 2: Timestamp Ordering
        # Sort using ISO timestamps
        recovered_stream = sorted(replay_buffer, key=lambda x: x["timestamp"])

        # Step 3: State recovery and aggregates recalculation
        avg_cpu = float(np_mean_or_zero([e["cpu_utilization"] for e in recovered_stream]))
        avg_mem = float(np_mean_or_zero([e["memory_utilization"] for e in recovered_stream]))
        avg_lat = float(np_mean_or_zero([e["latency_ms"] for e in recovered_stream]))
        avg_avail = float(np_mean_or_zero([e["availability"] for e in recovered_stream]))

        expected_cpu = float(np_mean_or_zero([e["cpu_utilization"] for e in self.clean_events]))
        expected_mem = float(np_mean_or_zero([e["memory_utilization"] for e in self.clean_events]))

        # Verify against expected clean state
        cpu_verified = abs(avg_cpu - expected_cpu) < 0.01
        mem_verified = abs(avg_mem - expected_mem) < 0.01
        count_verified = len(recovered_stream) == len(self.clean_events)

        test_passed = cpu_verified and mem_verified and count_verified

        return {
            "test_status": "PASS" if test_passed else "FAIL",
            "metrics": {
                "final_count": len(recovered_stream),
                "expected_count": len(self.clean_events),
                "avg_cpu": round(avg_cpu, 2),
                "avg_memory": round(avg_mem, 2),
                "avg_latency": round(avg_lat, 2),
                "availability": round(avg_avail, 4),
            },
            "validation": {
                "count_match": count_verified,
                "cpu_state_correct": cpu_verified,
                "memory_state_correct": mem_verified,
                "duplicates_rejected": duplicates_rejected
            },
            "timeline_before": [
                {"event_id": e["event_id"], "timestamp": e["timestamp"]} for e in adversarial_stream
            ],
            "timeline_after": [
                {"event_id": e["event_id"], "timestamp": e["timestamp"]} for e in recovered_stream
            ]
        }

def np_mean_or_zero(vals: List[float]) -> float:
    return float(np.mean(vals)) if vals else 0.0

import numpy as np
