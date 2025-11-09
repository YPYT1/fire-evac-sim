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
      const flicker = Math.sin(t * 8.5 + index * 1.3) * 0.1 + 1;
      child.scale.setScalar(baseScale * pulse * flicker);
      if (child.material instanceof THREE.MeshBasicMaterial) {
        child.material.opacity = 0.3 + 0.25 * pulse * flicker;
      }
      return;
    }
    const sprite = child as THREE.Sprite;
    const { baseScale = 1.2, intensity = 1.0, phase = 0 } = sprite.userData ?? {};
    
    // 多频率组合产生更自然的波动
    const pulse1 = Math.sin(t * 1.6 + phase + index * 0.15) * 0.3;
    const pulse2 = Math.sin(t * 2.8 + phase * 1.5) * 0.15;
    const flicker = Math.sin(t * 9.2 + index * 2.1) * 0.12;
    const combined = 0.85 + pulse1 + pulse2 + flicker;
    
    // 横向和纵向摆动
    const wobbleX = Math.sin(t * 1.2 + phase) * 0.08;
    const wobbleY = Math.sin(t * 0.9 + phase * 0.8) * 0.12;
    const wobbleZ = Math.cos(t * 1.1 + phase * 1.2) * 0.06;
    
    const scale = baseScale * (0.7 + combined * 0.6);
    sprite.scale.set(scale, scale * 1.1, scale);
    
    // 更丰富的颜色变化
    const lerpFactor = (combined + 1) * 0.5;
    if (sprite.material instanceof THREE.SpriteMaterial) {
      if (lerpFactor > 0.75) {
        // 高亮时：金黄 -> 橙红 -> 白芯
        const tempColor = COLOR_COOL.clone().lerp(COLOR_HOT, lerpFactor * 0.9);
        sprite.material.color = tempColor.lerp(COLOR_CORE, (lerpFactor - 0.75) * 0.8);
      } else if (lerpFactor > 0.5) {
        // 中等：金黄 -> 橙红
        sprite.material.color = COLOR_COOL.clone().lerp(COLOR_HOT, (lerpFactor - 0.5) * 2);
      } else {
        // 低亮：深橙 -> 金黄
        sprite.material.color = new THREE.Color(0xff6020).lerp(COLOR_COOL, lerpFactor * 2);
      }
      sprite.material.opacity = 0.6 + 0.4 * lerpFactor * intensity;
    }
    
    // 应用摆动
    sprite.position.x += wobbleX * 0.03;
    sprite.position.y += wobbleY * 0.025;
    sprite.position.z += wobbleZ * 0.02;
  });
}
