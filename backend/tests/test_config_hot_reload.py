"""配置热更新行为测试。"""

from pathlib import Path
from textwrap import dedent

from backend.app.core.config import load_simulation_config


def write_config(path: Path, content: str) -> None:
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")


def test_load_simulation_config_hot_reload(tmp_path):
    config_path = tmp_path / "simulation.yaml"
    write_config(
        config_path,
        """
        sim:
          tick_hz: 18
        agents:
          count: 120
          speed:
            mean: 1.1
            std: 0.15
        fire:
          diffusion_decay: 0.9
        """,
    )

    settings = load_simulation_config(config_path)
    assert settings.tick_hz == 18
    assert settings.agent_count == 120
    assert settings.speed_mean == 1.1
    assert settings.speed_std == 0.15
    assert settings.fire_decay == 0.9

    write_config(
        config_path,
        """
        sim:
          tick_hz: 24
        agents:
          count: 160
          speed:
            mean: 1.35
            std: 0.18
        fire:
          diffusion_decay: 0.82
        """,
    )

    updated = load_simulation_config(config_path)
    assert updated.tick_hz == 24
    assert updated.agent_count == 160
    assert updated.speed_mean == 1.35
    assert updated.speed_std == 0.18
    assert updated.fire_decay == 0.82
