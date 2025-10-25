import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

vi.mock('../api/client', () => ({
  replanSimulation: vi.fn().mockResolvedValue(undefined),
}));

import { replanSimulation } from '../api/client';
import { useSimStore } from './simStore';

const mockStateMessage = {
  type: 'state' as const,
  tick: 1,
  agents: [
    { id: 1, position: [0, 0, 0], velocity: [1, 0, 0] },
    { id: 2, position: [1, 0, 1], velocity: [0, 0, 1] },
  ],
  fires: [{ position: [2, 0, 2], intensity: 1 }],
  stats: {
    agent_count: 2,
    active_agents: 2,
    average_speed: 1.0,
    congestion_ratio: 0.1,
  },
};

describe('simStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('applies WebSocket state messages', () => {
    const store = useSimStore();
    store.applySocketMessage(mockStateMessage);

    expect(store.agents).toHaveLength(2);
    expect(store.fires).toHaveLength(1);
    expect(store.stats.average_speed).toBeCloseTo(1.0);
  });

  it('adds manual fire and triggers replan', async () => {
    const store = useSimStore();
    store.sessionId = 'session-1';
    store.setMode('manual');

    await store.addManualFire([3, 0, 3]);

    expect(store.manualFires).toHaveLength(1);
    expect(replanSimulation).toHaveBeenCalledTimes(1);
    expect(replanSimulation).toHaveBeenCalledWith({
      session_id: 'session-1',
      fires: store.manualFires,
      reason: 'manual_selection',
    });
  });
});
