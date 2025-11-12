<template>
  <section class="panel">
    <ToastNotification
      :message="toastMessage"
      :type="toastType"
      :visible="showToast"
      @close="showToast = false"
    />
    <h2>控制面板</h2>
    <form class="form" @submit.prevent="onStart">
      <label class="form__field">
        模式
        <div class="mode-picker">
          <span class="mode-dot" :style="modeSwatchStyle" />
          <select v-model="mode">
            <option value="floor1">一楼着火点</option>
            <option value="floor2">二楼着火点</option>
            <option value="floor3">三楼着火点</option>
          </select>
        </div>
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
      <div class="form__field crowd-field">
        <div class="crowd-header">
          <span>人群分流参数</span>
          <small>实时发送到 crowd 模块</small>
        </div>
        <div class="crowd-control">
          <label>影响半径 <span>{{ crowdRadius.toFixed(2) }} m</span></label>
          <input type="range" min="0.8" max="2.2" step="0.05" v-model.number="crowdRadius" />
        </div>
        <div class="crowd-control">
          <label>斥力增益 <span>{{ crowdGain.toFixed(2) }}</span></label>
          <input type="range" min="0" max="2.5" step="0.05" v-model.number="crowdGain" />
        </div>
        <div class="crowd-control">
          <label>推力系数 <span>{{ crowdPush.toFixed(2) }}</span></label>
          <input type="range" min="0" max="1.2" step="0.05" v-model.number="crowdPush" />
        </div>
      </div>
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
import { floorColorHex } from '../constants/pathPalette';
import ToastNotification from './ToastNotification.vue';

const store = useSimStore();
const mode = computed({
  get: () => store.mode,
  set: (value: 'floor1' | 'floor2' | 'floor3') => store.setMode(value),
});
const modeSwatchStyle = computed(() => ({
  background: floorColorHex(mode.value),
  boxShadow: `0 0 12px ${floorColorHex(mode.value)}33`,
}));
const agents = ref(200);
const tickHz = ref(20);
const speedOptions = [
  { label: '1x', value: 1 },
  { label: '1.5x', value: 1.5 },
  { label: '2x', value: 2 },
];
const speedMultiplier = ref(1);
const crowdRadius = ref(1.45);
const crowdGain = ref(1.25);
const crowdPush = ref(0.6);
const starting = ref(false);
const showToast = ref(false);
const toastMessage = ref('');
const toastType = ref<'success' | 'error' | 'warning' | 'info'>('info');
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
      crowd: {
        repulsion_radius: crowdRadius.value,
        repulsion_gain: crowdGain.value,
        repulsion_push_strength: crowdPush.value,
      },
    });
    store.tickHz = response.tick_hz;
    store.setMode(mode.value);
    connectSocket(response.session_id);
  } catch (error) {
    console.error('启动仿真失败', error);
    const message = error instanceof Error ? error.message : String(error);
    showToastNotification(`启动仿真失败：${message}`, 'error');
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
  socket.onopen = () => {
    showToastNotification('仿真已启动', 'success');
  };
  socket.onerror = () => {
    showToastNotification('WebSocket 连接失败，请检查后端服务', 'error');
  };
}

function showToastNotification(message: string, type: 'success' | 'error' | 'warning' | 'info') {
  toastMessage.value = message;
  toastType.value = type;
  showToast.value = true;
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

.mode-picker {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mode-dot {
  width: 1rem;
  height: 1rem;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.15);
  flex-shrink: 0;
}

.crowd-field {
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 0.6rem;
  padding: 0.75rem;
  gap: 0.65rem;
}

.crowd-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: rgba(15, 23, 42, 0.75);
}

.crowd-control {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.crowd-control label {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: rgba(15, 23, 42, 0.8);
}

.crowd-control input[type='range'] {
  width: 100%;
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
