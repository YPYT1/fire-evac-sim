import * as THREE from 'three';
import { LineGeometry } from 'three/examples/jsm/lines/LineGeometry.js';
import { LineMaterial } from 'three/examples/jsm/lines/LineMaterial.js';
import { Line2 } from 'three/examples/jsm/lines/Line2.js';

const pathResolution = new THREE.Vector2(1, 1);
let resolutionWatcherBound = false;

function refreshResolution(): void {
  if (typeof window === 'undefined') return;
  pathResolution.set(window.innerWidth || 1, window.innerHeight || 1);
}

function ensureResolutionWatcher(): void {
  if (typeof window === 'undefined' || resolutionWatcherBound) return;
  refreshResolution();
  window.addEventListener('resize', refreshResolution);
  resolutionWatcherBound = true;
}

export function createPathLayer(): THREE.Group {
  const group = new THREE.Group();
  group.name = 'Paths';
  return group;
}

export function updatePaths(group: THREE.Group, paths: number[][][]): void {
  disposeChildren(group);
  ensureResolutionWatcher();

  paths.forEach((path, index) => {
    if (!Array.isArray(path) || path.length < 2) {
      return;
    }
    const positions: number[] = [];
    path.forEach(([x, y, z]) => {
      positions.push(x, y + 0.05, z);
    });

    const geometry = new LineGeometry();
    geometry.setPositions(positions);

    const color = new THREE.Color().setHSL((index * 0.618) % 1, 0.65, 0.55);
    const material = new LineMaterial({
      color,
      linewidth: 0.06,
      opacity: 0.85,
      transparent: true,
      dashed: true,
      dashSize: 0.3,
      gapSize: 0.15,
      worldUnits: true,
    });
    material.resolution.copy(pathResolution);

    const line = new Line2(geometry, material);
    line.computeLineDistances();
    line.userData = { type: 'path-line', hue: (index * 0.618) % 1 };
    group.add(line);

    const arrow = createArrow(color, path[path.length - 2], path[path.length - 1]);
    group.add(arrow);
  });
}

export function animatePaths(group: THREE.Group, delta: number): void {
  group.children.forEach((child) => {
    if ((child as Line2).isLine2 && (child as Line2).material instanceof LineMaterial) {
      const mat = (child as Line2).material as LineMaterial;
      mat.dashOffset -= delta * 0.45;
      if (mat.dashOffset < -1) mat.dashOffset = 0;
      mat.needsUpdate = true;
    } else if (child.userData?.type === 'path-arrow') {
      child.rotation.y += delta * 0.5;
    }
  });
}

function disposeChildren(group: THREE.Group): void {
  group.children.forEach((child) => {
    const obj = child as THREE.Object3D & { geometry?: THREE.BufferGeometry; material?: THREE.Material | THREE.Material[] };
    if (obj.geometry) {
      obj.geometry.dispose();
    }
    const mat = obj.material;
    if (Array.isArray(mat)) {
      mat.forEach((m) => m?.dispose?.());
    } else {
      mat?.dispose?.();
    }
  });
  group.clear();
}

function createArrow(color: THREE.Color, from: number[], to: number[]): THREE.Group {
  const group = new THREE.Group();
  const length = Math.max(0.8, new THREE.Vector3(to[0] - from[0], to[1] - from[1], to[2] - from[2]).length());
  const shaftGeometry = new THREE.CylinderGeometry(0.05, 0.05, Math.min(length, 1.5), 8, 1);
  const shaftMaterial = new THREE.MeshStandardMaterial({
    color,
    emissive: color.clone().multiplyScalar(0.6),
    metalness: 0.2,
    roughness: 0.4,
  });
  const shaft = new THREE.Mesh(shaftGeometry, shaftMaterial);
  shaft.position.y = length / 2;
  group.add(shaft);

  const headGeometry = new THREE.ConeGeometry(0.16, 0.35, 12);
  const headMaterial = new THREE.MeshStandardMaterial({
    color,
    emissive: color.clone().multiplyScalar(0.8),
    metalness: 0.3,
    roughness: 0.2,
  });
  const head = new THREE.Mesh(headGeometry, headMaterial);
  head.position.y = length;
  group.add(head);

  group.position.set(from[0], from[1] + 0.05, from[2]);
  const target = new THREE.Vector3(to[0], to[1], to[2]);
  group.lookAt(target);
  group.rotateX(Math.PI / 2);
  group.userData = { type: 'path-arrow' };
  return group;
}
