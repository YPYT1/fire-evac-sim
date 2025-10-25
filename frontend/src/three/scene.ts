/**
 * Three.js 场景初始化与基本渲染循环。
 */
import * as THREE from 'three';

export interface SceneBundle {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
}

export function createScene(canvas: HTMLCanvasElement): SceneBundle {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xffffff);

  const camera = new THREE.PerspectiveCamera(60, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
  camera.position.set(8, 12, 12);
  camera.lookAt(0, 0, 0);

  const ambient = new THREE.AmbientLight(0xffffff, 0.4);
  scene.add(ambient);

  const directional = new THREE.DirectionalLight(0xffffff, 0.8);
  directional.position.set(10, 20, 10);
  scene.add(directional);

  const gridHelper = new THREE.GridHelper(20, 20, 0x38bdf8, 0x38bdf8);
  scene.add(gridHelper);

  return { scene, camera, renderer };
}

export function resizeRenderer(bundle: SceneBundle): void {
  const { renderer, camera } = bundle;
  const canvas = renderer.domElement;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  if (canvas.width !== width || canvas.height !== height) {
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }
}

export function render(bundle: SceneBundle): void {
  resizeRenderer(bundle);
  bundle.renderer.render(bundle.scene, bundle.camera);
}
