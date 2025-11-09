<template>
  <section class="panel">
    <h2>控制面板</h2>
    <form class="form" @submit.prevent="onStart">
      <label class="form__field">
        模式
        <select v-model="mode">
          <option value="floor1">一楼着火点</option>
          <option value="floor2">二楼着火点</option>
          <option value="floor3">三楼着火点</option>
        </select>
      </label>
      <label class="form__field">
        人数
        <input type="number" min="1" v-model.number="agents" />
      </label>
      <label class="form__field">
        Tick Hz
        <input type="number" min="1" v-model.number="tickHz" />
      </label>
      <label class="form__field">
        播放速度
        <select v-model.number="speedMultiplier">
          <option v-for="option in speedOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>
      <button type="submit" :disabled="isRunning || starting">启动仿真</button>
  </form>
    <p class="hint">选择不同楼层可预览对应高度的疏散路径与火点分布。</p>
    <button type="button" class="stop" @click="onStop" :disabled="!isRunning">停止仿真</button>
    <p class="status">当前会话：{{ sessionLabel }}</p>
  </section>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useSimStore } from '../store/simStore';
import { openSimulationSocket, startSimulation, stopSimulation } from '../api/client';

const store = useSimStore();
const mode = computed({
  get: () => store.mode,
  set: (value: 'floor1' | 'floor2' | 'floor3') => store.setMode(value),
});
const agents = ref(200);
const tickHz = ref(20);
const speedOptions = [
  { label: '1x', value: 1 },
  { label: '1.5x', value: 1.5 },
  { label: '2x', value: 2 },
];
const speedMultiplier = ref(1);
const starting = ref(false);
let socket: WebSocket | null = null;

const isRunning = computed(() => !!store.sessionId);
const sessionLabel = computed(() => store.sessionId ?? '尚未启动');

async function onStart() {
  if (starting.value) return;
  starting.value = true;
  try {
    if (store.sessionId) {
      await onStop();
    }
    const response = await startSimulation({
      mode: mode.value,
      agents: {
        count: agents.value,
        speed_mean: 1.3,
        speed_std: 0.2,
      },
      time_scale: speedMultiplier.value,
    });
    store.tickHz = response.tick_hz;
    store.setMode(mode.value);
    connectSocket(response.session_id);
  } finally {
    starting.value = false;
  }
}

async function onStop() {
  if (!store.sessionId) return;
  await stopSimulation(store.sessionId);
  socket?.close();
  socket = null;
  store.reset();
  starting.value = false;
}

function connectSocket(sessionId: string) {
  socket?.close();
  socket = openSimulationSocket(sessionId, (message) => {
    store.applySocketMessage(message);
  });
}
</script>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  background: #ffffff;
  border-radius: 0.75rem;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
}

.form {
  display: grid;
  gap: 0.5rem;
}

.form__field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.9rem;
}

input,
select,
button {
  padding: 0.5rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(148, 163, 184, 0.6);
  background: #ffffff;
  color: #0f172a;
}

button {
  cursor: pointer;
  background: #2563eb;
  border-color: #1d4ed8;
  color: #ffffff;
}

.stop {
  background: #ef4444;
  border-color: #dc2626;
}

.status {
  font-size: 0.85rem;
  color: rgba(15, 23, 42, 0.7);
}

.hint {
  font-size: 0.85rem;
  color: #2563eb;
  margin: -0.25rem 0 0.25rem;
}
</style>
