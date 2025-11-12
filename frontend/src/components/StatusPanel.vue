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
      <li>
        <span>疑散进度</span>
        <strong>{{ evacuationProgress.toFixed(1) }}%</strong>
      </li>
      <li class="floor-distribution">
        <span>楼层人数分布</span>
        <div class="floor-bars">
          <div v-for="(count, floor) in floorDistribution" :key="floor" class="floor-bar">
            <span class="floor-label">{{ floor }}</span>
            <div class="bar-wrapper">
              <div class="bar-fill" :style="{ width: getBarWidth(count), background: getFloorBarColor(floor) }"></div>
              <span class="bar-count">{{ count }}</span>
            </div>
          </div>
        </div>
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

function classifyAgentFloor(y: number): string {
  if (y < 2) return '一层';
  if (y < 6) return '二层';
  return '三层';
}

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

const floorDistribution = computed(() => {
  const distribution: Record<string, number> = { '一层': 0, '二层': 0, '三层': 0 };
  store.agents.forEach((agent) => {
    const floor = classifyAgentFloor(agent.position[1]);
    distribution[floor] = (distribution[floor] || 0) + 1;
  });
  return distribution;
});

const evacuationProgress = computed(() => {
  if (store.stats.agent_count === 0) return 0;
  return ((store.stats.agent_count - store.stats.active_agents) / store.stats.agent_count) * 100;
});

function getBarWidth(count: number): string {
  const max = Math.max(...Object.values(floorDistribution.value));
  if (max === 0) return '0%';
  return `${(count / max) * 100}%`;
}

function getFloorBarColor(floor: string): string {
  const colorMap: Record<string, string> = {
    '一层': '#3b82f6',
    '二层': '#8b5cf6',
    '三层': '#ec4899',
  };
  return colorMap[floor] || '#94a3b8';
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

.floor-distribution {
  flex-direction: column !important;
  align-items: stretch !important;
  gap: 0.5rem;
}

.floor-bars {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-top: 0.3rem;
}

.floor-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.floor-label {
  min-width: 2.5rem;
  font-size: 0.8rem;
  color: rgba(15, 23, 42, 0.7);
}

.bar-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
}

.bar-fill {
  height: 1.2rem;
  border-radius: 0.3rem;
  transition: width 0.3s ease;
  min-width: 2px;
}

.bar-count {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1d4ed8;
  min-width: 2rem;
  text-align: right;
}
</style>
