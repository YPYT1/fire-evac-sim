<template>
  <section class="panel">
    <h2>路径颜色图例</h2>
    <ul class="legend">
      <li v-for="item in legend" :key="item.id">
        <span class="swatch" :style="swatchStyle(item)" />
        <div class="legend__text">
          <strong>{{ item.label }}</strong>
          <small>{{ item.desc }}</small>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { PATH_LEGEND } from '../constants/pathPalette';

const legend = PATH_LEGEND;

function swatchStyle(item: (typeof PATH_LEGEND)[number]) {
  return {
    background: item.core,
    boxShadow: `0 0 12px 0 ${item.halo}`,
  };
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

.legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.legend li {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: rgba(15, 23, 42, 0.78);
  font-size: 0.9rem;
}

.swatch {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.12);
}

.legend__text strong {
  display: block;
  font-weight: 600;
  color: #0f172a;
}

.legend__text small {
  font-size: 0.78rem;
  color: rgba(15, 23, 42, 0.6);
}
</style>
