import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

import { useSimStore } from './simStore';

const mockStateMessage = {
  type: 'state' as const,
  tick: 1,
  agents: [
    { id: 1, position: [0, 0, 0], velocity: [1, 0, 0] },
    { id: 2, position: [1, 0, 1], velocity: [0, 0, 1] },
  ],
  fires: [{ position: [2, 0, 2], intensity: 1 }],
  paths: [
    [
      [0, 0, 0],
      [1, 0, 1],
    ],
  ],
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
    expect(store.paths).toHaveLength(1);
  });

  it('updates mode correctly', () => {
    const store = useSimStore();
    store.setMode('floor2');
    expect(store.mode).toBe('floor2');
  });
});
