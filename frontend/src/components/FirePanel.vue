<template>
  <section class="panel">
    <h2>火点管理</h2>
    <p class="hint">
      当前火点列表来自后端状态，手动模式下可点击场景放置新火点并触发 /sim/replan。
    </p>
    <h3>实时火点</h3>
    <ul class="fire-list">
      <li v-for="fire in fires" :key="fire.position.join('-')">
        🔥 ({{ fire.position[0].toFixed(1) }}, {{ fire.position[2].toFixed(1) }}) · 强度 {{ fire.intensity.toFixed(2) }}
      </li>
      <li v-if="fires.length === 0" class="placeholder">暂无火点</li>
    </ul>
    <template v-if="manualFires.length">
      <h3>手动火点 ({{ manualFires.length }})</h3>
      <ul class="fire-list">
        <li v-for="fire in manualFires" :key="`manual-${fire.position.join('-')}`">
          📍 ({{ fire.position[0].toFixed(1) }}, {{ fire.position[2].toFixed(1) }})
        </li>
      </ul>
      <button type="button" class="ghost" @click="clearManual">清空手动火点</button>
    </template>
  </section>
</template>

<script setup lang="ts">
import { useSimStore } from '../store/simStore';

const store = useSimStore();
const fires = store.fires;
const manualFires = store.manualFires;

function clearManual() {
  void store.clearManualFires();
}
</script>

<style scoped>
.panel {
  padding: 1rem;
  background: #ffffff;
  border-radius: 0.75rem;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.hint {
  font-size: 0.85rem;
  color: rgba(15, 23, 42, 0.6);
}

.fire-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-family: monospace;
  color: #0f172a;
}

.placeholder {
  color: rgba(15, 23, 42, 0.4);
  font-style: italic;
}

button {
  align-self: flex-start;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid #2563eb;
  background: rgba(37, 99, 235, 0.08);
  color: #1d4ed8;
  cursor: pointer;
}

.ghost {
  border-color: #ef4444;
  color: #dc2626;
  background: rgba(239, 68, 68, 0.08);
}
</style>
