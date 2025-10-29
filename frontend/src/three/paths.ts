/**
 * 路径可视化：使用 LineSegments 简化展示。
 */
import * as THREE from 'three';

export function createPathLayer(): THREE.Group {
  const group = new THREE.Group();
  group.name = 'Paths';
  return group;
}

export function updatePaths(group: THREE.Group, paths: number[][][]): void {
  group.clear();
  paths.forEach((path) => {
    const points = path.map(([x, y, z]) => new THREE.Vector3(x, y + 0.05, z));
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({ color: 0x22c55e });
    const line = new THREE.Line(geometry, material);
    group.add(line);
  });
}
