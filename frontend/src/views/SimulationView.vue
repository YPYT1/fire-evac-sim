<template>
  <div class="layout">
    <main class="layout__canvas">
      <SceneCanvas />
    </main>
    <aside class="layout__sidebar">
      <ControlPanel />
      <StatusPanel />
      <FirePanel />
    </aside>
  </div>
</template>

<script setup lang="ts">
import SceneCanvas from '../components/SceneCanvas.vue';
import ControlPanel from '../components/ControlPanel.vue';
import FirePanel from '../components/FirePanel.vue';
import StatusPanel from '../components/StatusPanel.vue';
</script>

<style scoped>
.layout {
  display: flex;
  height: 100%;
  background: #f8fafc;
  color: #0f172a;
}

.layout__canvas {
  flex: 1;
  position: relative;
  background: #ffffff;
  border-radius: 1rem;
  margin-right: 1rem;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.05);
}

.layout__sidebar {
  width: 320px;
  padding: 1rem;
  background: #f1f5f9;
  border-left: 1px solid rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  border-radius: 1rem;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.05);
}
</style>
