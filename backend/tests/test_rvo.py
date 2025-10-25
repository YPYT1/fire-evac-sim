"""RVO 管理器基础测试。"""

from backend.app.sim.rvo import RVOManager


def test_rvo_simple_strategy_step():
    manager = RVOManager(strategy="simple", timestep=0.5)
    agent_id = manager.add_agent((0.0, 0.0))
    manager.set_preferred_velocity(agent_id, (1.0, 0.0))

    manager.step()
    position = manager.get_agent_position(agent_id)

    assert position[0] == 0.5
    assert position[1] == 0.0


def test_rvo_requested_strategy_fallback():
    manager = RVOManager(strategy="rvo2", timestep=0.1)
    # 如果 python-rvo2 未安装，应自动回退 simple
    assert manager.effective_strategy in {"rvo2", "simple", "rvo2_py"}
