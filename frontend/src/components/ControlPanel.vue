<template>
  <section class="panel">
    <h2>控制面板</h2>
    <form class="form" @submit.prevent="onStart">
      <label class="form__field">
        模式
        <select v-model="mode">
          <option value="fixed">固定火点</option>
          <option value="random">随机火点</option>
          <option value="manual">手动指定</option>
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
      <button type="submit" :disabled="isRunning">启动仿真</button>
    </form>
    <p v-if="mode === 'manual'" class="hint">
      手动模式：启动会话后，点击 3D 场景即可放置火点（最多 5 个）。
    </p>
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
  set: (value: 'fixed' | 'random' | 'manual') => store.setMode(value),
});
const agents = ref(200);
const tickHz = ref(20);
let socket: WebSocket | null = null;

const isRunning = computed(() => !!store.sessionId);
const sessionLabel = computed(() => store.sessionId ?? '尚未启动');

async function onStart() {
  const response = await startSimulation({
    mode: mode.value,
    agents: {
      count: agents.value,
      speed_mean: 1.3,
      speed_std: 0.2,
    },
  });
  store.tickHz = response.tick_hz;
  store.setMode(mode.value);
  connectSocket(response.session_id);
}

async function onStop() {
  if (!store.sessionId) return;
  await stopSimulation(store.sessionId);
  socket?.close();
  socket = null;
  store.reset();
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
