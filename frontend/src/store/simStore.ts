/**
 * Pinia 存储仿真状态，集中管理会话 ID、代理/火源数据。
 */
import { defineStore } from 'pinia';
import { ref, shallowRef } from 'vue';
import type { FireSource, WebSocketMessage, SimStats } from '../api/client';
import { replanSimulation } from '../api/client';

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
  const stats = ref<SimStats>({
    agent_count: 0,
    active_agents: 0,
    average_speed: 0,
    congestion_ratio: 0,
    speed_mean: 0,
    speed_std: 0,
    fire_decay: 0,
  });
  const mode = ref<'fixed' | 'random' | 'manual'>('fixed');
  const manualFires = shallowRef<FireSource[]>([]);
  const manualFireLimit = 5;
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
      if (msg.stats) {
        stats.value = msg.stats;
        if (typeof msg.tick_hz === 'number') {
          tickHz.value = msg.tick_hz;
        }
        if (!msg.stats.speed_mean) {
          stats.value = {
            ...stats.value,
            speed_mean: stats.value.speed_mean ?? 0,
            speed_std: stats.value.speed_std ?? 0,
            fire_decay: stats.value.fire_decay ?? 0,
          };
        }
      }
    }
    if (msg.type === 'end') {
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
    }
  }

  function setMode(nextMode: 'fixed' | 'random' | 'manual') {
    mode.value = nextMode;
    if (nextMode !== 'manual') {
      manualFires.value = [];
    }
  }

  async function addManualFire(position: [number, number, number]) {
    if (!sessionId.value) return;
    if (mode.value !== 'manual') return;
    const nextFire: FireSource = { position, intensity: 1.0 };
    const nextList = [...manualFires.value, nextFire].slice(-manualFireLimit);
    manualFires.value = nextList;
    await replanSimulation({
      session_id: sessionId.value,
      fires: nextList,
      reason: 'manual_selection',
    });
  }

  async function clearManualFires() {
    manualFires.value = [];
    if (sessionId.value && mode.value === 'manual') {
      await replanSimulation({
        session_id: sessionId.value,
        fires: [],
        reason: 'manual_clear',
      });
    }
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
    manualFires.value = [];
    lastTickProcessed.value = null;
  }

  return {
    sessionId,
    tickHz,
    agents,
    fires,
    stats,
    mode,
    manualFires,
    applySocketMessage,
    setMode,
    addManualFire,
    clearManualFires,
    reset,
  };
});
