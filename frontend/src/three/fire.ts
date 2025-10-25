/**
 * 火源可视化工具。
 */
import * as THREE from 'three';

export function createFireMarker(): THREE.Group {
  const group = new THREE.Group();
  group.name = 'Fires';
  return group;
}

export function updateFireMarkers(group: THREE.Group, fires: Array<{ position: [number, number, number] }>): void {
  group.clear();
  fires.forEach((fire) => {
    const [x, y, z] = fire.position;
    const spriteMaterial = new THREE.SpriteMaterial({ color: 0xf97316 });
    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.position.set(x, y + 0.5, z);
    sprite.scale.setScalar(1.2);
    group.add(sprite);
  });
}
