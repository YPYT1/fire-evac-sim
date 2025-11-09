<template>
  <section class="panel">
    <h2>实时状态</h2>
    <ul class="stats">
      <li>
        <span>会话</span>
        <strong>{{ store.sessionId ?? '未连接' }}</strong>
      </li>
      <li>
        <span>Tick</span>
        <strong>{{ store.tickHz }} Hz</strong>
      </li>
      <li>
        <span>在场人数</span>
        <strong>{{ store.stats.active_agents }} / {{ store.stats.agent_count }}</strong>
      </li>
      <li>
        <span>平均速度</span>
        <strong>{{ store.stats.average_speed.toFixed(2) }} m/s</strong>
      </li>
      <li>
        <span>拥堵率</span>
        <strong>{{ (store.stats.congestion_ratio * 100).toFixed(1) }}%</strong>
      </li>
      <li>
        <span>目标速度</span>
        <strong>{{ store.stats.speed_mean?.toFixed(2) ?? '0.00' }} ± {{ store.stats.speed_std?.toFixed(2) ?? '0.00' }} m/s</strong>
      </li>
      <li>
        <span>火焰扩散衰减</span>
        <strong>{{ ((store.stats.fire_decay ?? 0) * 100).toFixed(1) }}%</strong>
      </li>
      <li class="legend-row">
        <span>当前楼层颜色</span>
        <span class="legend-badge" :style="floorBadgeStyle">{{ modeLabel }}</span>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { useSimStore } from '../store/simStore';
import { computed } from 'vue';
import { floorColorHex } from '../constants/pathPalette';

const store = useSimStore();
const modeLabel = computed(() => {
  switch (store.mode) {
    case 'floor2':
      return '二层';
    case 'floor3':
      return '三层';
    default:
      return '一层';
  }
});
const floorBadgeStyle = computed(() => ({
  background: floorColorHex(store.mode),
  boxShadow: `0 0 10px ${floorColorHex(store.mode)}55`,
}));
</script>

<style scoped>
.panel {
  padding: 1rem;
  background: #ffffff;
  border-radius: 0.75rem;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stats {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.stats li {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: rgba(15, 23, 42, 0.75);
}

.stats strong {
  font-size: 1rem;
  color: #1d4ed8;
}

.legend-row {
  align-items: center;
}

.legend-badge {
  min-width: 3rem;
  text-align: center;
  border-radius: 999px;
  padding: 0.1rem 0.5rem;
  font-size: 0.8rem;
  color: #0f172a;
  border: 1px solid rgba(15, 23, 42, 0.15);
}
</style>
