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

  // 只在仿真启动后才应用楼层视角
  watch(
    () => [store.mode, store.sessionId] as const,
    ([mode, sessionId]) => {
      if (sessionId) {
        // 只有仿真运行中才应用视角切换
        updateFloorVisibility(mode);
        adjustCameraForFloor(mode);
      } else {
        // 停止后恢复所有层可见
        resetVisibility();
      }
    },
    { immediate: false }
  );

  animate();
});

function updateFloorVisibility(mode: 'floor1' | 'floor2' | 'floor3') {
  if (!buildingModel || !bundle) return;

  buildingModel.traverse((child) => {
    const y = child.position.y;
    const meshName = child.name.toLowerCase();
    const parentName = child.parent?.name.toLowerCase() || '';
    
    // 判断是否是楼梯
    const isStaircase = meshName === 'staircase' || parentName === 'staircase';
    const stairFloorLevel = child.userData.floorLevel || child.parent?.userData.floorLevel || 0;
    
    // 判断是否是地板/楼顶
    const isFloor = meshName.includes('floor') || meshName.includes('ceiling');
    
    // 判断是否是三楼房间（Y >= 8）
    const isFloor3Room = y >= 8;
    
    // 保存原始材质
    if (child instanceof THREE.Mesh && !child.userData.originalMaterial && child.material) {
      child.userData.originalMaterial = child.material;
    }
    
    if (mode === 'floor1') {
      // 一楼模式：一楼墙体透明25%，二三楼全部隐藏（包括地板、桂椅、房间、楼梯）
      if (y >= 4) {
        // 二三楼全部隐藏
        child.visible = false;
      } else {
        // 一楼：墙体透明
        child.visible = true;
        if (child instanceof THREE.Mesh && child.userData.originalMaterial && y > 0.1 && !isFloor) {
          child.material = (child.userData.originalMaterial as THREE.Material).clone();
          child.material.opacity = 0.25;
          child.material.transparent = true;
          child.material.depthWrite = false;
        } else if (child instanceof THREE.Mesh && child.userData.originalMaterial) {
          child.material = child.userData.originalMaterial;
        }
      }
    } else if (mode === 'floor2') {
      // 二楼模式：一楼墙体高度透明，二楼完全显示，三楼全部隐藏
      
      // 三楼：全部隐藏
      if (y >= 8) {
        child.visible = false;
      }
      // 楼梯特殊处理
      else if (isStaircase) {
        if (stairFloorLevel >= 4) {
          // 三楼通往二楼的楼梯：隐藏
          child.visible = false;
        } else {
          // 二楼通往一楼的楼梯：显示
          child.visible = true;
          if (child instanceof THREE.Mesh && child.userData.originalMaterial) {
            child.material = child.userData.originalMaterial;
          }
        }
      }
      // 二楼：完全显示
      else if (y >= 4 && y < 8) {
        child.visible = true;
        if (child instanceof THREE.Mesh && child.userData.originalMaterial) {
          child.material = child.userData.originalMaterial;
        }
      }
      // 一楼：墙体高度透明
      else if (y < 4) {
        child.visible = true;
        if (child instanceof THREE.Mesh && child.userData.originalMaterial) {
          if (!isFloor && y > 0.1) {
            // 墙体：高度透明
            child.material = (child.userData.originalMaterial as THREE.Material).clone();
            child.material.opacity = 0.05;  // 5%不透明度（95%透明）
            child.material.transparent = true;
            child.material.depthWrite = false;
          } else {
            // 地板：正常显示
            child.material = child.userData.originalMaterial;
          }
        }
      }
    } else {
      // 三楼模式：一二楼墙体高度透明，三楼墙体透明25%，所有楼梯显示
      child.visible = true;
      
      if (isStaircase) {
        // 所有楼梯：正常显示
        if (child instanceof THREE.Mesh && child.userData.originalMaterial) {
          child.material = child.userData.originalMaterial;
        }
      }
      // 一楼
      else if (y < 4) {
        if (child instanceof THREE.Mesh && child.userData.originalMaterial) {
          if (!isFloor && y > 0.1) {
            // 一楼墙体：高度透明
            child.material = (child.userData.originalMaterial as THREE.Material).clone();
            child.material.opacity = 0.05;  // 5%不透明度
            child.material.transparent = true;
            child.material.depthWrite = false;
          } else {
            // 地板：正常显示
            child.material = child.userData.originalMaterial;
          }
        }
      }
      // 二楼
      else if (y >= 4 && y < 8) {
        if (child instanceof THREE.Mesh && child.userData.originalMaterial) {
          if (!isFloor && y > 4.1) {
            // 二楼墙体：透明25%
            child.material = (child.userData.originalMaterial as THREE.Material).clone();
            child.material.opacity = 0.25;
            child.material.transparent = true;
            child.material.depthWrite = false;
          } else {
            // 地板：正常显示
            child.material = child.userData.originalMaterial;
          }
        }
      }
      // 三楼
      else if (y >= 8) {
        if (child instanceof THREE.Mesh && child.userData.originalMaterial) {
          if (!isFloor && y > 8.1) {
            // 三楼房间墙体：透明25%
            child.material = (child.userData.originalMaterial as THREE.Material).clone();
            child.material.opacity = 0.25;
            child.material.transparent = true;
            child.material.depthWrite = false;
          } else {
            // 地板：正常显示
            child.material = child.userData.originalMaterial;
          }
        }
      }
    }
  });
}

function resetVisibility() {
  if (!buildingModel) return;
  
  // 恢复所有元素可见和原始材质
  buildingModel.traverse((child) => {
    child.visible = true;
    if (child instanceof THREE.Mesh && child.userData.originalMaterial) {
      child.material = child.userData.originalMaterial;
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
