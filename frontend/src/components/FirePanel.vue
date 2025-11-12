<template>
  <section class="panel">
    <div class="header">
      <h2>🔥 火点管理</h2>
      <span class="badge" :class="fireBadgeClass">{{ fires.length }} 个火点</span>
    </div>
    <p class="hint">
      火点根据所选楼层自动预设，可在后端动态调整或通过 API 触发重规划。
    </p>
    <div class="fire-stats">
      <div class="stat-item">
        <span class="stat-label">当前楼层</span>
        <span class="stat-value">{{ currentFloorLabel }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">平均强度</span>
        <span class="stat-value">{{ averageIntensity }}</span>
      </div>
    </div>
    <h3>实时火点</h3>
    <ul class="fire-list">
      <li v-for="(fire, index) in fires" :key="fire.position.join('-')" class="fire-item" :class="getIntensityClass(fire.intensity)">
        <div class="fire-icon">🔥</div>
        <div class="fire-info">
          <div class="fire-location">
            <span class="fire-number">#{{ index + 1 }}</span>
            <span class="fire-coords">X: {{ fire.position[0].toFixed(1) }}, Z: {{ fire.position[2].toFixed(1) }}</span>
            <span class="fire-floor">{{ getFloorLabel(fire.position[1]) }}</span>
          </div>
          <div class="fire-intensity">
            <span class="intensity-label">强度</span>
            <div class="intensity-bar">
              <div class="intensity-fill" :style="{ width: (fire.intensity * 100) + '%' }"></div>
            </div>
            <span class="intensity-value">{{ fire.intensity.toFixed(2) }}</span>
          </div>
        </div>
      </li>
      <li v-if="fires.length === 0" class="placeholder">
        <div class="empty-state">
          <div class="empty-icon">💧</div>
          <p>暂无火点</p>
          <p class="empty-hint">启动仿真后将自动生成火点</p>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useSimStore } from '../store/simStore';

const store = useSimStore();
const fires = computed(() => store.fires);

const currentFloorLabel = computed(() => {
  switch (store.mode) {
    case 'floor2': return '二楼';
    case 'floor3': return '三楼';
    default: return '一楼';
  }
});

const averageIntensity = computed(() => {
  if (fires.value.length === 0) return '0.00';
  const sum = fires.value.reduce((acc, fire) => acc + fire.intensity, 0);
  return (sum / fires.value.length).toFixed(2);
});

const fireBadgeClass = computed(() => {
  if (fires.value.length === 0) return 'badge--empty';
  if (fires.value.length > 3) return 'badge--danger';
  return 'badge--active';
});

function getFloorLabel(y: number): string {
  if (y < 2) return '一楼';
  if (y < 6) return '二楼';
  return '三楼';
}

function getIntensityClass(intensity: number): string {
  if (intensity >= 0.8) return 'intensity--high';
  if (intensity >= 0.5) return 'intensity--medium';
  return 'intensity--low';
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

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  transition: all 0.3s;
}

.badge--empty {
  background: rgba(148, 163, 184, 0.1);
  color: #64748b;
}

.badge--active {
  background: rgba(251, 146, 60, 0.15);
  color: #ea580c;
}

.badge--danger {
  background: rgba(239, 68, 68, 0.15);
  color: #dc2626;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.fire-stats {
  display: flex;
  gap: 1rem;
  padding: 0.75rem;
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.05), rgba(239, 68, 68, 0.05));
  border-radius: 0.5rem;
  margin-bottom: 0.75rem;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(15, 23, 42, 0.6);
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #ea580c;
}

.fire-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #fff;
  border-radius: 0.5rem;
  border: 1px solid rgba(251, 146, 60, 0.2);
  transition: all 0.2s;
}

.fire-item:hover {
  border-color: rgba(251, 146, 60, 0.5);
  box-shadow: 0 4px 12px rgba(251, 146, 60, 0.15);
  transform: translateY(-2px);
}

.intensity--high {
  border-left: 3px solid #dc2626;
}

.intensity--medium {
  border-left: 3px solid #ea580c;
}

.intensity--low {
  border-left: 3px solid #fb923c;
}

.fire-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.fire-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.fire-location {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.fire-number {
  font-weight: 700;
  color: #ea580c;
  font-size: 0.85rem;
}

.fire-coords {
  font-family: monospace;
  font-size: 0.85rem;
  color: #0f172a;
}

.fire-floor {
  padding: 0.1rem 0.5rem;
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.fire-intensity {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.intensity-label {
  font-size: 0.75rem;
  color: rgba(15, 23, 42, 0.6);
  min-width: 2.5rem;
}

.intensity-bar {
  flex: 1;
  height: 0.5rem;
  background: rgba(251, 146, 60, 0.1);
  border-radius: 999px;
  overflow: hidden;
}

.intensity-fill {
  height: 100%;
  background: linear-gradient(90deg, #fb923c, #dc2626);
  transition: width 0.3s;
  border-radius: 999px;
}

.intensity-value {
  font-weight: 700;
  color: #ea580c;
  font-size: 0.85rem;
  min-width: 2.5rem;
  text-align: right;
}

.placeholder {
  border: none;
  padding: 0;
}

.empty-state {
  text-align: center;
  padding: 2rem 1rem;
  color: rgba(15, 23, 42, 0.4);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.empty-hint {
  font-size: 0.75rem;
  margin-top: 0.25rem;
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
