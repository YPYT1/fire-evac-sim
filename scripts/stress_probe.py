"""压力测试脚本：验证极端场景下的性能瓶颈（Stage 3-2）。"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import httpx

BASE_URL = os.environ.get("SIM_BASE_URL", "http://127.0.0.1:8000")
REPORT_PATH = Path(os.environ.get("STRESS_REPORT_PATH", "stress_report.json"))


@dataclass
class Sample:
    elapsed: float
    latency: float
    active_agents: int
    average_speed: float
    congestion_ratio: float


ScenarioType = Literal["crowd_peak", "exit_blocked"]


SCENARIOS: dict[ScenarioType, dict[str, Any]] = {
    "crowd_peak": {
        "payload": {
            "mode": "floor2",
            "agents": {"count": 600, "speed_mean": 1.2, "speed_std": 0.3},
            "goals": ["east_door"],
        },
        "duration": 6.0,
        "interval": 0.5,
    },
    "exit_blocked": {
        "payload": {
            "mode": "floor1",
            "agents": {"count": 240, "speed_mean": 1.3, "speed_std": 0.2},
            "goals": ["north_door"],
        },
        "manual_fires": [
            {"position": [0.0, 0.0, 29.0], "intensity": 1.4},
            {"position": [-2.0, 0.0, 28.0], "intensity": 1.1},
        ],
        "duration": 6.0,
        "interval": 0.5,
    },
}


async def run_scenario(
    client: httpx.AsyncClient, name: ScenarioType, config: dict[str, Any]
) -> dict[str, Any]:
    payload = config["payload"]
    duration = float(config.get("duration", 5.0))
    interval = float(config.get("interval", 0.5))

    print(f"\n▶ Stress scenario: {name}")
    start = await client.post("/sim/start", json=payload)
    start.raise_for_status()
    start_data = start.json()
    session_id = start_data["session_id"]
    print(f"  session_id={session_id}, tick_hz={start_data['tick_hz']}")

    samples: list[Sample] = []
    t_begin = time.perf_counter()

    if config.get("manual_fires"):
        await client.post(
            "/sim/replan",
            json={
                "session_id": session_id,
                "fires": config["manual_fires"],
                "reason": f"{name}_blocking",
            },
        )

    while True:
        now = time.perf_counter()
        if now - t_begin >= duration:
            break

        t0 = time.perf_counter()
        resp = await client.get("/sim/status", params={"session_id": session_id})
        latency = time.perf_counter() - t0
        resp.raise_for_status()
        payload = resp.json()
        samples.append(
            Sample(
                elapsed=now - t_begin,
                latency=latency,
                active_agents=int(payload.get("active_agents", 0)),
                average_speed=float(payload.get("average_speed", 0.0)),
                congestion_ratio=float(payload.get("congestion_ratio", 0.0)),
            )
        )
        await asyncio.sleep(interval)

    await client.post("/sim/stop", json={"session_id": session_id})
    return summarise(name, samples)


def summarise(name: str, samples: list[Sample]) -> dict[str, Any]:
    if not samples:
        return {"name": name, "samples": 0, "note": "no data collected"}

    latencies = [s.latency for s in samples]
    congestion = [s.congestion_ratio for s in samples]
    avg_speed = [s.average_speed for s in samples]
    active = [s.active_agents for s in samples]

    summary = {
        "name": name,
        "samples": len(samples),
        "latency_avg_ms": round(statistics.mean(latencies) * 1000, 2),
        "latency_p95_ms": round(percentile(latencies, 95) * 1000, 2),
        "congestion_peak": round(max(congestion, default=0.0), 3),
        "average_speed_min": round(min(avg_speed, default=0.0), 3),
        "active_agents_min": min(active, default=0),
        "active_agents_max": max(active, default=0),
    }

    print(
        "  summary: latency_avg={latency_avg_ms}ms | p95={latency_p95_ms}ms | "
        "congestion_peak={congestion_peak:.0%} | min_speed={average_speed_min}m/s".format(
            **summary
        )
    )
    return summary


def percentile(values: list[float], percentile_rank: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * percentile_rank / 100
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[int(k)]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


async def main() -> None:
    summaries: list[dict[str, Any]] = []
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        for name, config in SCENARIOS.items():
            try:
                summary = await run_scenario(client, name, config)
                summaries.append(summary)
            except httpx.HTTPError as exc:
                print(f"✖ Scenario {name} failed: {exc}")
                summaries.append({"name": name, "error": str(exc)})

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps({"summaries": summaries}, indent=2, ensure_ascii=False))
    print(f"\n▶ stress report saved to {REPORT_PATH.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
