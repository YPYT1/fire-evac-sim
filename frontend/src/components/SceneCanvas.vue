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
let buildingModel: THREE.Group | null = null;

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
    buildingModel = await loadBuilding();
    bundle.scene.add(buildingModel);
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

  watch(
    () => store.mode,
    (mode) => {
      updateFloorVisibility(mode);
      adjustCameraForFloor(mode);
    },
    { immediate: false }
  );

  animate();
});

function updateFloorVisibility(mode: 'floor1' | 'floor2' | 'floor3') {
  if (!buildingModel || !bundle) return;

  // 根据模式设置楼层可见性
  buildingModel.traverse((child) => {
    if (child instanceof THREE.Mesh || child instanceof THREE.Group) {
      const position = child.position;
      const y = position.y;

      // 根据 Y 坐标判断楿层
      if (mode === 'floor1') {
        // 一层模式：隐藏二三层
        child.visible = y < 4.5;
      } else if (mode === 'floor2') {
        // 二层模式：隐藏三层，淡化一层
        if (y >= 8) {
          child.visible = false;
        } else {
          child.visible = true;
          if (child instanceof THREE.Mesh && child.material) {
            const mat = child.material as THREE.Material;
            if (y < 1) {
              mat.opacity = 0.3;
              mat.transparent = true;
            } else {
              mat.opacity = 1;
            }
          }
        }
      } else {
        // 三层模式：淡化一二层
        child.visible = true;
        if (child instanceof THREE.Mesh && child.material) {
          const mat = child.material as THREE.Material;
          if (y < 6) {
            mat.opacity = 0.25;
            mat.transparent = true;
          } else {
            mat.opacity = 1;
          }
        }
      }
    }
  });
}

function adjustCameraForFloor(mode: 'floor1' | 'floor2' | 'floor3') {
  if (!bundle) return;

  const camera = bundle.camera;
  const controls = bundle.controls;

  // 根据楼层调整相机高度和目标点
  const targetY = mode === 'floor1' ? 2 : mode === 'floor2' ? 6 : 10;
  const cameraY = mode === 'floor1' ? 60 : mode === 'floor2' ? 65 : 75;

  // 平滑过渡
  const duration = 800;
  const startY = camera.position.y;
  const startTargetY = controls.target.y;
  const startTime = performance.now();

  function animateCamera(time: number) {
    const elapsed = time - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out-cubic

    camera.position.y = startY + (cameraY - startY) * eased;
    controls.target.y = startTargetY + (targetY - startTargetY) * eased;
    controls.update();

    if (progress < 1) {
      requestAnimationFrame(animateCamera);
    }
  }

  requestAnimationFrame(animateCamera);
}

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
