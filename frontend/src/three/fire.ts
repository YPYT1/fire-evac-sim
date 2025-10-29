/**
 * 火源可视化工具。
 */
import * as THREE from 'three';

const COLOR_HOT = new THREE.Color(0xff512f);
const COLOR_COOL = new THREE.Color(0xffc371);
const COLOR_CORE = new THREE.Color(0xffffff);

export function createFireMarker(): THREE.Group {
  const group = new THREE.Group();
  group.name = 'Fires';
  return group;
}

export function updateFireMarkers(group: THREE.Group, fires: Array<{ position: [number, number, number]; intensity?: number }>): void {
  group.clear();
  fires.forEach((fire, index) => {
    const [x, y, z] = fire.position;
    const intensity = typeof fire.intensity === 'number' ? fire.intensity : 1.0;
    const outerMaterial = new THREE.SpriteMaterial({ color: COLOR_COOL.clone(), transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false });
    const outer = new THREE.Sprite(outerMaterial);
    outer.position.set(x, y + 0.6, z);
    const baseScale = 1.6 + intensity * 0.9;
    outer.scale.setScalar(baseScale);
    outer.userData = { baseScale, intensity, phase: index * 0.5 };
    group.add(outer);

    const coreMaterial = new THREE.SpriteMaterial({ color: COLOR_CORE.clone(), transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false });
    const core = new THREE.Sprite(coreMaterial);
    core.position.set(x, y + 1.0, z);
    const coreBase = 0.6 + intensity * 0.4;
    core.scale.setScalar(coreBase);
    core.userData = { baseScale: coreBase, intensity, phase: index * 0.7 + Math.PI / 3 };
    group.add(core);
  });
}

export function animateFireMarkers(group: THREE.Group, time: number): void {
  const t = time * 0.002;
  group.children.forEach((child, index) => {
    const sprite = child as THREE.Sprite;
    const { baseScale = 1.2, intensity = 1.0, phase = 0 } = sprite.userData ?? {};
    const pulse = Math.sin(t * 1.6 + phase + index * 0.15) * 0.35 + 0.85;
    const wobble = Math.sin(t * 0.9 + phase) * 0.1;
    const scale = baseScale * (0.75 + pulse * 0.55);
    sprite.scale.set(scale, scale, scale);
    const lerpFactor = (pulse + 1) * 0.5;
    if (sprite.material instanceof THREE.SpriteMaterial) {
      if (lerpFactor > 0.7) {
        sprite.material.color = COLOR_COOL.clone().lerp(COLOR_HOT, lerpFactor).lerp(COLOR_CORE, 0.2 * lerpFactor);
      } else {
        sprite.material.color = COLOR_COOL.clone().lerp(COLOR_HOT, lerpFactor * 0.8);
      }
      sprite.material.opacity = 0.5 + 0.5 * lerpFactor * intensity;
    }
    sprite.position.y += wobble * 0.02;
  });
}
