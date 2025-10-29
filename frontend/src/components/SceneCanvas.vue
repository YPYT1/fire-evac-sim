<template>
  <canvas ref="canvasRef" class="scene-canvas"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue';
import * as THREE from 'three';
import { createScene, render, type SceneBundle } from '../three/scene';
import { loadBuilding } from '../three/loaders';
import { createAgentsVisual, updateAgentsMatrix } from '../three/agents';
import { createFireMarker, updateFireMarkers, animateFireMarkers } from '../three/fire';
import { createPathLayer, updatePaths } from '../three/paths';
import { useSimStore } from '../store/simStore';

const canvasRef = ref<HTMLCanvasElement | null>(null);
let bundle: SceneBundle | null = null;
let frameId = 0;
let agentsVisual: ReturnType<typeof createAgentsVisual> | null = null;
let fireGroup: THREE.Group | null = null;
let pathGroup: THREE.Group | null = null;

const store = useSimStore();

function animate() {
  if (!bundle) return;
  if (fireGroup) {
    animateFireMarkers(fireGroup, performance.now());
  }
  render(bundle);
  frameId = requestAnimationFrame(animate);
}

onMounted(async () => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  bundle = createScene(canvas);

  agentsVisual = createAgentsVisual(1024);
  fireGroup = createFireMarker();
  pathGroup = createPathLayer();

  bundle.scene.add(agentsVisual.mesh);
  bundle.scene.add(fireGroup);
  bundle.scene.add(pathGroup);

  try {
    const building = await loadBuilding();
    bundle.scene.add(building);
  } catch (error) {
    console.warn('加载建筑模型失败：', error);
  }

  watch(
    () => store.agents,
    (agents) => {
      if (agentsVisual) {
        updateAgentsMatrix(agentsVisual, agents);
      }
    },
    { immediate: true }
  );

  watch(
    () => store.paths,
    (paths) => {
      if (pathGroup) {
        updatePaths(pathGroup, paths);
      }
    },
    { immediate: true }
  );

  watch(
    () => store.fires,
    (fires) => {
      if (fireGroup) {
        updateFireMarkers(fireGroup, fires);
      }
    },
    { immediate: true }
  );

  animate();
});

onBeforeUnmount(() => {
  cancelAnimationFrame(frameId);
  if (bundle) {
    bundle.renderer.dispose();
  }
});
</script>

<style scoped>
.scene-canvas {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
