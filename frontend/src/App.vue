<template>
  <div class="shell">
    <header class="shell__header">
      <h1>Fire Evacuation Simulation</h1>
      <p>火灾疏散仿真平台 · Vue3 + Three.js</p>
    </header>
    <section class="shell__body">
      <RouterView />
    </section>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router';
</script>

<style scoped>
.shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f8fafc;
  color: #0f172a;
}

.shell__header {
  padding: 1rem 2rem;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  background: #ffffff;
}

.shell__body {
  flex: 1;
  padding: 1.5rem 2rem;
}
</style>
