/**
 * Pinia 存储仿真状态，集中管理会话 ID、代理/火源数据。
 */
import { defineStore } from 'pinia';
import { ref, shallowRef } from 'vue';
import type { FireSource, WebSocketMessage, SimStats } from '../api/client';

type SimMode = 'floor1' | 'floor2' | 'floor3';

interface AgentState {
  id: number;
  position: [number, number, number];
  velocity: [number, number, number];
}

export const useSimStore = defineStore('sim', () => {
  const sessionId = ref<string | null>(null);
  const tickHz = ref<number>(20);
  const agents = shallowRef<AgentState[]>([]);
  const fires = shallowRef<FireSource[]>([]);
  const paths = shallowRef<number[][][]>([]);
  const stats = ref<SimStats>({
    agent_count: 0,
    active_agents: 0,
    average_speed: 0,
    congestion_ratio: 0,
    speed_mean: 0,
    speed_std: 0,
    fire_decay: 0,
  });
  const mode = ref<SimMode>('floor1');
  const lastTickProcessed = ref<number | null>(null);

  function applySocketMessage(msg: WebSocketMessage) {
    if (msg.type === 'hello') {
      sessionId.value = msg.session_id;
    }
    if (msg.type === 'state') {
      const tick = typeof msg.tick === 'number' ? msg.tick : null;
      if (tick !== null) {
        const step = Math.max(1, Math.round(tickHz.value / 10));
        if (lastTickProcessed.value !== null) {
          const delta = tick - lastTickProcessed.value;
          if (delta <= 0) {
            return;
          }
          if (delta < step) {
            return;
          }
        }
        lastTickProcessed.value = tick;
      }

      agents.value = msg.agents as AgentState[];
      fires.value = msg.fires as FireSource[];
      paths.value = (msg.paths as number[][][]) ?? [];
      if (msg.stats) {
        stats.value = {
          ...msg.stats,
          speed_mean: msg.stats.speed_mean ?? stats.value.speed_mean ?? 0,
          speed_std: msg.stats.speed_std ?? stats.value.speed_std ?? 0,
          fire_decay: msg.stats.fire_decay ?? stats.value.fire_decay ?? 0,
        };
        if (typeof msg.tick_hz === 'number') {
          tickHz.value = msg.tick_hz;
        }
      }
    }
    if (msg.type === 'end') {
      sessionId.value = null;
      agents.value = [];
      fires.value = [];
      paths.value = [];
      stats.value = {
        agent_count: 0,
        active_agents: 0,
        average_speed: 0,
        congestion_ratio: 0,
        speed_mean: 0,
        speed_std: 0,
        fire_decay: 0,
      };
    }
  }

  function setMode(nextMode: SimMode) {
    mode.value = nextMode;
  }

  function reset() {
    sessionId.value = null;
    agents.value = [];
    fires.value = [];
    stats.value = {
      agent_count: 0,
      active_agents: 0,
      average_speed: 0,
      congestion_ratio: 0,
      speed_mean: 0,
      speed_std: 0,
      fire_decay: 0,
    };
    lastTickProcessed.value = null;
    paths.value = [];
  }

  return {
    sessionId,
    tickHz,
    agents,
    fires,
    paths,
    stats,
    mode,
    applySocketMessage,
    setMode,
    reset,
  };
});
