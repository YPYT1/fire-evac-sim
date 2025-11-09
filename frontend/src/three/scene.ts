/**
 * Three.js 场景初始化与基本渲染循环。
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export interface SceneBundle {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  controls: OrbitControls;
}

export function createScene(canvas: HTMLCanvasElement): SceneBundle {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  if ('outputColorSpace' in renderer) {
    (renderer as any).outputColorSpace = THREE.SRGBColorSpace;
  }
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf6f8fb);
  scene.fog = new THREE.Fog(0xf6f8fb, 150, 320);

  const camera = new THREE.PerspectiveCamera(60, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
  camera.position.set(0, 75, 90);
  camera.lookAt(0, 12, 0);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.maxPolarAngle = Math.PI * 0.49;
  controls.minDistance = 20;
  controls.maxDistance = 160;
  controls.target.set(0, 12, 0);

  const hemi = new THREE.HemisphereLight(0xddebf9, 0x66707a, 0.4);
  scene.add(hemi);

  const directional = new THREE.DirectionalLight(0xfff6e5, 0.85);
  directional.position.set(40, 80, 30);
  directional.castShadow = true;
  directional.shadow.mapSize.set(2048, 2048);
  directional.shadow.camera.near = 10;
  directional.shadow.camera.far = 200;
  directional.shadow.camera.left = -100;
  directional.shadow.camera.right = 100;
  directional.shadow.camera.top = 100;
  directional.shadow.camera.bottom = -20;
  scene.add(directional);

  const rim = new THREE.DirectionalLight(0xc9ddff, 0.35);
  rim.position.set(-60, 30, -40);
  scene.add(rim);

  const groundGeometry = new THREE.PlaneGeometry(220, 220);
  const groundMaterial = new THREE.MeshStandardMaterial({
    color: 0xe2e8f0,
    roughness: 0.9,
    metalness: 0.05,
  });
  const ground = new THREE.Mesh(groundGeometry, groundMaterial);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.01;
  ground.receiveShadow = true;
  scene.add(ground);

  const gridHelper = new THREE.GridHelper(120, 60, 0xbcd2f8, 0xe2e8f0);
  scene.add(gridHelper);

  return { scene, camera, renderer, controls };
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
  bundle.controls.update();
  bundle.renderer.render(bundle.scene, bundle.camera);
}
