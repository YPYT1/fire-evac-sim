<template>
  <canvas ref="canvasRef" class="scene-canvas"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue';
import * as THREE from 'three';
import { createScene, render, type SceneBundle } from '../three/scene';
import { loadBuilding } from '../three/loaders';
import { createAgentsVisual, updateAgentsMatrix } from '../three/agents';
import { createPathLayer, updatePaths, animatePaths } from '../three/paths';
import { useSimStore } from '../store/simStore';
import { FireParticleManager, isNebulaSupported } from '../three/fireParticles';
import { createFireMarker, updateFireMarkers, animateFireMarkers } from '../three/fire';

const canvasRef = ref<HTMLCanvasElement | null>(null);
let bundle: SceneBundle | null = null;
let frameId = 0;
let agentsVisual: ReturnType<typeof createAgentsVisual> | null = null;
let pathGroup: THREE.Group | null = null;
let fireManager: FireParticleManager | null = null;
let fireFallbackGroup: THREE.Group | null = null;
let lastTime = 0;

const store = useSimStore();

function animate(time?: number) {
  if (!bundle) return;
  const now = typeof time === 'number' ? time : performance.now();
  const delta = (now - lastTime) / 1000;
  lastTime = now;
  if (fireManager) {
    fireManager.update(delta);
  } else if (fireFallbackGroup) {
    animateFireMarkers(fireFallbackGroup, now);
  }
  if (pathGroup) {
    animatePaths(pathGroup, delta);
  }
  render(bundle);
  frameId = requestAnimationFrame(animate);
}

onMounted(async () => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  bundle = createScene(canvas);

  agentsVisual = createAgentsVisual(1024);
  pathGroup = createPathLayer();
  if (isNebulaSupported) {
    try {
      fireManager = new FireParticleManager(bundle.scene);
    } catch (error) {
      console.warn('Fire particle system unavailable, falling back to sprite markers.', error);
      fireManager = null;
      fireFallbackGroup = createFireMarker();
      bundle.scene.add(fireFallbackGroup);
    }
  } else {
    fireFallbackGroup = createFireMarker();
    bundle.scene.add(fireFallbackGroup);
  }

  bundle.scene.add(agentsVisual.mesh);
  bundle.scene.add(pathGroup);

  try {
    const building = await loadBuilding();
    bundle.scene.add(building);
  } catch (error) {
    console.warn('加载建筑模型失败：', error);
  }

  lastTime = performance.now();
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
      if (fireManager) {
        fireManager.setFires(fires);
      } else if (fireFallbackGroup) {
        updateFireMarkers(fireFallbackGroup, fires);
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
  fireManager?.dispose();
  fireFallbackGroup = null;
});
</script>

<style scoped>
.scene-canvas {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
