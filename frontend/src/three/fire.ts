/**
 * 火源可视化工具。
 */
import * as THREE from 'three';

const COLOR_HOT = new THREE.Color(0xff512f);
const COLOR_COOL = new THREE.Color(0xffc371);
const COLOR_CORE = new THREE.Color(0xffffff);
const COLOR_SMOKE = new THREE.Color(0x2f2f2f);
const COLOR_GLOW = new THREE.Color(0xffa94d);

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
    const smokeMaterial = new THREE.SpriteMaterial({
      color: COLOR_SMOKE.clone(),
      transparent: true,
      opacity: 0.2,
      depthWrite: false,
    });
    const smoke = new THREE.Sprite(smokeMaterial);
    smoke.position.set(x, y + 1.6, z);
    const smokeScale = 2.4 + intensity * 1.6;
    smoke.scale.setScalar(smokeScale);
    smoke.userData = { baseScale: smokeScale, intensity: intensity * 0.6, phase: index * 0.33 + Math.PI / 5 };
    group.add(smoke);

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

    const glowGeometry = new THREE.CircleGeometry(0.8 + intensity * 0.4, 32);
    glowGeometry.rotateX(-Math.PI / 2);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: COLOR_GLOW.clone(),
      transparent: true,
      opacity: 0.35,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const glow = new THREE.Mesh(glowGeometry, glowMaterial);
    glow.position.set(x, y + 0.02, z);
    glow.userData = { pulse: 0, baseScale: 0.8 + intensity * 0.6 };
    group.add(glow);
  });
}

export function animateFireMarkers(group: THREE.Group, time: number): void {
  const t = time * 0.002;
  group.children.forEach((child, index) => {
    if (child instanceof THREE.Mesh) {
      const { baseScale = 1.0 } = child.userData ?? {};
      const pulse = Math.sin(t * 1.4 + index * 0.5) * 0.2 + 1;
      child.scale.setScalar(baseScale * pulse);
      if (child.material instanceof THREE.MeshBasicMaterial) {
        child.material.opacity = 0.25 + 0.2 * pulse;
      }
      return;
    }
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
