/**
 * 示例：在此定义自建建筑模型的组装逻辑。
 * TODO: 由建模团队根据真实场景补充。
 */
import * as THREE from 'three';

export function createHouse(): THREE.Group {
  const group = new THREE.Group();
  const placeholder = new THREE.BoxGeometry(4, 3, 4);
  const material = new THREE.MeshStandardMaterial({ color: 0x94a3b8, wireframe: true });
  const mesh = new THREE.Mesh(placeholder, material);
  mesh.position.set(0, 1.5, 0);
  group.add(mesh);
  group.name = 'HousePlaceholder';
  return group;
}
