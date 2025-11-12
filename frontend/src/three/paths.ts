import * as THREE from 'three';
import { LineGeometry } from 'three/examples/jsm/lines/LineGeometry.js';
import { LineMaterial } from 'three/examples/jsm/lines/LineMaterial.js';
import { Line2 } from 'three/examples/jsm/lines/Line2.js';
import { classifyFloorByHeight, getFloorColor, type FloorBand } from '../constants/pathPalette';

const pathResolution = new THREE.Vector2(1, 1);
let resolutionWatcherBound = false;

// 性能优化：限制最大路径渲染数量
const MAX_PATHS_TO_RENDER = 300;

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

  // 性能优化：限制路径数量，优先渲染最后的路径（最近添加的代理）
  const pathsToRender = paths.length > MAX_PATHS_TO_RENDER 
    ? paths.slice(-MAX_PATHS_TO_RENDER) 
    : paths;

  if (paths.length > MAX_PATHS_TO_RENDER) {
    console.warn(`路径数量（${paths.length}）超过最大限制（${MAX_PATHS_TO_RENDER}），仅渲染最近的 ${MAX_PATHS_TO_RENDER} 条`);
  }

  pathsToRender.forEach((path) => {
    if (!Array.isArray(path) || path.length < 2) {
      return;
    }
    const segments = splitByFloor(path);
    segments.forEach((segment) => {
      const positions: number[] = [];
      segment.points.forEach(([x, y, z]) => {
        positions.push(x, y + 0.05, z);
      });
      if (positions.length < 6) {
        return;
      }

      const palette = getFloorColor(segment.floor);
      const haloGeometry = new LineGeometry();
      haloGeometry.setPositions(positions);
      const haloMaterial = new LineMaterial({
        color: new THREE.Color(palette.halo),
        linewidth: 0.32,
        opacity: 0.4,
        transparent: true,
        dashed: false,
        depthTest: false,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        worldUnits: true,
      });
      haloMaterial.resolution.copy(pathResolution);
      const halo = new Line2(haloGeometry, haloMaterial);
      halo.computeLineDistances();
      halo.userData = { type: 'path-line', layer: 'halo', floor: segment.floor };
      group.add(halo);

      const coreGeometry = new LineGeometry();
      coreGeometry.setPositions(positions);
      const coreMaterial = new LineMaterial({
        color: new THREE.Color(palette.core),
        linewidth: 0.14,
        opacity: 1,
        transparent: true,
        dashed: true,
        dashSize: 0.22,
        gapSize: 0.1,
        worldUnits: true,
        depthTest: true,
        depthWrite: false,
      });
      coreMaterial.resolution.copy(pathResolution);
      const coreLine = new Line2(coreGeometry, coreMaterial);
      coreLine.computeLineDistances();
      coreLine.userData = { type: 'path-line', layer: 'core', floor: segment.floor };
      group.add(coreLine);
    });

    const lastSegment = segments[segments.length - 1];
    const arrowPalette = lastSegment ? getFloorColor(lastSegment.floor) : getFloorColor('floor1');
    const arrowColor = new THREE.Color(arrowPalette.core);
    const arrow = createArrow(arrowColor, path[path.length - 2], path[path.length - 1]);
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
  const shaftGeometry = new THREE.CylinderGeometry(0.07, 0.07, Math.min(length, 1.5), 8, 1);
  const shaftMaterial = new THREE.MeshStandardMaterial({
    color,
    emissive: color.clone().multiplyScalar(0.8),
    emissiveIntensity: 1.1,
    metalness: 0.2,
    roughness: 0.4,
  });
  const shaft = new THREE.Mesh(shaftGeometry, shaftMaterial);
  shaft.position.y = length / 2;
  group.add(shaft);

  const headGeometry = new THREE.ConeGeometry(0.2, 0.4, 14);
  const headMaterial = new THREE.MeshStandardMaterial({
    color,
    emissive: color.clone().multiplyScalar(1.0),
    emissiveIntensity: 1.2,
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

interface ColoredSegment {
  floor: FloorBand;
  points: number[][];
}

function splitByFloor(path: number[][]): ColoredSegment[] {
  const segments: ColoredSegment[] = [];
  if (path.length < 2) {
    return segments;
  }
  let currentFloor: FloorBand = classifyFloorByHeight(path[0][1]);
  let currentPoints: number[][] = [path[0]];
  for (let i = 1; i < path.length; i += 1) {
    const point = path[i];
    const floor = classifyFloorByHeight(point[1]);
    if (floor !== currentFloor) {
      currentPoints.push(point);
      if (currentPoints.length >= 2) {
        segments.push({ floor: currentFloor, points: [...currentPoints] });
      }
      currentFloor = floor;
      currentPoints = [point];
    } else {
      currentPoints.push(point);
    }
  }
  if (currentPoints.length >= 2) {
    segments.push({ floor: currentFloor, points: currentPoints });
  }
  return segments;
}
