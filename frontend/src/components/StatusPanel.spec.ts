import { render, screen } from '@testing-library/vue';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it } from 'vitest';

import StatusPanel from './StatusPanel.vue';
import { useSimStore } from '../store/simStore';

describe('StatusPanel', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renders session information and stats', () => {
    const store = useSimStore();
    store.sessionId = 'session-42';
    store.tickHz = 30;
    store.stats = {
      agent_count: 200,
      active_agents: 150,
      average_speed: 1.8,
      congestion_ratio: 0.25,
      speed_mean: 1.5,
      speed_std: 0.3,
      fire_decay: 0.92,
    };

    render(StatusPanel);

    expect(screen.getByText('session-42')).toBeInTheDocument();
    expect(screen.getByText('30 Hz')).toBeInTheDocument();
    expect(screen.getByText('150 / 200')).toBeInTheDocument();
    expect(screen.getByText(/1.80 m\/s/)).toBeInTheDocument();
    expect(screen.getByText(/25\.0%/)).toBeInTheDocument();
    expect(screen.getByText(/1\.50 ± 0\.30 m\/s/)).toBeInTheDocument();
    expect(screen.getByText(/92\.0%/)).toBeInTheDocument();
  });
});
