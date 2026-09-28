import asyncio
import httpx
import random
import math
from datetime import datetime, timezone

API_URL = "http://localhost:8000/api/v1/telemetry/stream"
INSTANCE_TYPES = ["c5.xlarge", "c5.2xlarge", "c5.4xlarge"]

async def generate_workload():
    async with httpx.AsyncClient() as client:
        print(f"Starting workload generator towards {API_URL}")
        while True:
            events = []
            now = datetime.now(timezone.utc)
            
            for _ in range(random.randint(1, 5)):
                inst = random.choice(INSTANCE_TYPES)
                # simulate some sinusoidal diurnal load
                hour = now.hour
                base_load = 50 + 30 * math.sin(hour * math.pi / 12)
                noise = random.uniform(-10, 10)
                
                cpu = min(100.0, max(0.0, base_load + noise))
                mem = min(100.0, max(0.0, base_load * 0.8 + noise))
                
                latency = 100.0 + (cpu ** 2) / 100.0  # exponential latency scaling on CPU
                
                event = {
                    "timestamp": now.isoformat(),
                    "instance_type": inst,
                    "cpu_utilization": round(cpu, 2),
                    "memory_utilization": round(mem, 2),
                    "latency_ms": round(latency, 2),
                    "request_volume": random.randint(100, 10000),
                    "error_rate_pct": round(random.uniform(0, 1), 2) if cpu < 90 else round(random.uniform(1, 5), 2),
                    "availability": 99.99 if cpu < 90 else 99.5,
                    "instance_count": random.randint(1, 10),
                    "instance_price": 0.34
                }
                events.append(event)
                
            try:
                resp = await client.post(API_URL, json={"events": events})
                print(f"Sent {len(events)} events, status: {resp.status_code}")
            except Exception as e:
                print(f"Failed to send telemetry: {e}")
                
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(generate_workload())
