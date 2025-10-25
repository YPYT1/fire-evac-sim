<template>
  <canvas
    ref="canvasRef"
    class="scene-canvas"
    :class="{ 'scene-canvas--manual': store.mode === 'manual' && !!store.sessionId }"
  ></canvas>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue';
import * as THREE from 'three';
import { createScene, render, type SceneBundle } from '../three/scene';
import { loadBuilding } from '../three/loaders';
import { createHouse } from '../three/models/House';
import { createAgentsVisual, updateAgentsMatrix } from '../three/agents';
import { createFireMarker, updateFireMarkers } from '../three/fire';
import { createPathLayer } from '../three/paths';
import { useSimStore } from '../store/simStore';

const canvasRef = ref<HTMLCanvasElement | null>(null);
let bundle: SceneBundle | null = null;
let frameId = 0;
let agentsVisual: ReturnType<typeof createAgentsVisual> | null = null;
let fireGroup: THREE.Group | null = null;
let pathGroup: THREE.Group | null = null;

const store = useSimStore();
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
const intersectionPoint = new THREE.Vector3();

function animate() {
  if (!bundle) return;
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
    console.warn('加载建筑模型失败，请替换为自建 glb：', error);
    bundle.scene.add(createHouse());
  }

  canvas.addEventListener('pointerdown', handlePointerDown);
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
  const canvas = canvasRef.value;
  if (canvas) {
    canvas.removeEventListener('pointerdown', handlePointerDown);
  }
  if (bundle) {
    bundle.renderer.dispose();
  }
});

function handlePointerDown(event: PointerEvent) {
  if (store.mode !== 'manual' || !store.sessionId) return;
  if (!bundle) return;
  const canvas = canvasRef.value;
  if (!canvas) return;

  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(pointer, bundle.camera);
  const hit = raycaster.ray.intersectPlane(groundPlane, intersectionPoint);
  if (!hit) return;

  void store.addManualFire([hit.x, 0, hit.z]);
}
</script>

<style scoped>
.scene-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.scene-canvas--manual {
  cursor: crosshair;
}
</style>
