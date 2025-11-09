import * as THREE from 'three';
import * as NebulaModule from 'three-nebula';

import type { FireSource } from '../api/client';

type NebulaEmitter = any;
type NebulaSystem = any;

const NebulaPkg: any = (NebulaModule as any).default ?? NebulaModule;
const SystemCtor = NebulaPkg?.System;
const SpriteRendererCtor = NebulaPkg?.SpriteRenderer;
const EmitterCtor = NebulaPkg?.Emitter;
const RateCtor = NebulaPkg?.Rate;
const SpanCtor = NebulaPkg?.Span;
const LifeCtor = NebulaPkg?.Life;
const BodySpriteCtor = NebulaPkg?.BodySprite;
const PositionCtor = NebulaPkg?.Position;
const SphereZoneCtor = NebulaPkg?.SphereZone;
const VelocityCtor = NebulaPkg?.Velocity;
const Vector3DCtor = NebulaPkg?.Vector3D;
const AlphaCtor = NebulaPkg?.Alpha;
const ColorCtor = NebulaPkg?.Color;
const ScaleCtor = NebulaPkg?.Scale;

export const isNebulaSupported =
  typeof SystemCtor === 'function' &&
  typeof SpriteRendererCtor === 'function' &&
  typeof EmitterCtor === 'function' &&
  typeof RateCtor === 'function';

function createFireTexture(size = 256): THREE.Texture {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext('2d');
  if (!context) {
    throw new Error('Unable to create fire texture canvas context');
  }

  // 创建带噪声的径向渐变
  const gradient = context.createRadialGradient(
    size / 2,
    size / 2,
    size * 0.05,
    size / 2,
    size / 2,
    size * 0.48,
  );
  
  // 更丰富的颜色过渡：白芯 -> 金黄 -> 橙红 -> 深红 -> 透明
  gradient.addColorStop(0, 'rgba(255,255,255,1.0)');
  gradient.addColorStop(0.15, 'rgba(255,245,200,0.98)');
  gradient.addColorStop(0.3, 'rgba(255,210,80,0.95)');
  gradient.addColorStop(0.5, 'rgba(255,140,40,0.85)');
  gradient.addColorStop(0.7, 'rgba(235,70,30,0.6)');
  gradient.addColorStop(0.85, 'rgba(180,30,20,0.3)');
  gradient.addColorStop(1, 'rgba(30,0,0,0)');

  context.fillStyle = gradient;
  context.fillRect(0, 0, size, size);

  // 添加噪声效果增加真实感
  const imageData = context.getImageData(0, 0, size, size);
  const data = imageData.data;
  for (let i = 0; i < data.length; i += 4) {
    const noise = (Math.random() - 0.5) * 25;
    data[i] = Math.max(0, Math.min(255, data[i] + noise));
    data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise * 0.8));
    data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise * 0.6));
  }
  context.putImageData(imageData, 0, 0);

  const texture = new THREE.CanvasTexture(canvas);
  texture.name = 'FireParticleTexture';
  texture.needsUpdate = true;
  return texture;
}

function lerp(min: number, max: number, factor: number): number {
  return min + (max - min) * factor;
}

interface FireEmitterEntry {
  flame: NebulaEmitter;
  smoke?: NebulaEmitter;
  intensity: number;
}

export class FireParticleManager {
  private system: NebulaSystem;
  private renderer: any;
  private texture: THREE.Texture;
  private emitters = new Map<string, FireEmitterEntry>();

  constructor(scene: THREE.Scene) {
    if (!isNebulaSupported) {
      throw new Error('three-nebula SpriteRenderer is unavailable on this platform');
    }
    this.texture = createFireTexture();
    try {
      this.renderer = new SpriteRendererCtor(scene, THREE);
      this.system = new SystemCtor();
      this.system.addRenderer(this.renderer);
    } catch (error) {
      this.texture.dispose();
      throw new Error(`three-nebula initialization failed: ${String(error)}`);
    }
  }

  setFires(fires: FireSource[]): void {
    const activeKeys = new Set<string>();

    fires.forEach((fire) => {
      const key = fire.position.join(',');
      activeKeys.add(key);
      const intensity = typeof fire.intensity === 'number' ? fire.intensity : 1.0;
      const entry = this.emitters.get(key);
      if (entry) {
        this.updateEmitter(entry, fire.position, intensity, key);
      } else {
        const created = this.createEmitterSet(fire.position, intensity);
        this.addEmitter(key, created, intensity);
      }
    });

    for (const [key, entry] of this.emitters.entries()) {
      if (!activeKeys.has(key)) {
        this.removeEmitter(key, entry);
      }
    }
  }

  update(delta: number): void {
    if (!this.system) return;
    this.system.update(delta);
  }

  dispose(): void {
    for (const [key, entry] of this.emitters.entries()) {
      this.removeEmitter(key, entry);
    }
    this.emitters.clear();
    this.renderer?.destroy?.();
    this.texture.dispose();
  }

  private createEmitterSet(position: [number, number, number], intensity: number): FireEmitterEntry {
    const flame = new EmitterCtor();

    // 增加粒子数量和随机性
    const rateParticles = lerp(45, 85, Math.min(intensity, 2));
    flame.setRate(new RateCtor(new SpanCtor(rateParticles * 0.9, rateParticles * 1.1), new SpanCtor(0.006, 0.014)));

    flame.addInitializers([
      // 增大初始发射区域，增加随机性
      new PositionCtor(new SphereZoneCtor(0, 0, 0, 0.8)),
      new LifeCtor(0.7, 1.8),
      new BodySpriteCtor(this.texture),
      // 添加横向随机速度，模拟火焰摆动
      new VelocityCtor(
        new Vector3DCtor(0, lerp(16, 28, intensity), 0),
        new SpanCtor(0.8, 1.6),
      ),
    ]);

    flame.addBehaviours([
      new AlphaCtor(1, 0),
      // 更丰富的颜色过渡：金黄 -> 橙红 -> 深红
      new ColorCtor(['#fff5c8', '#ffd250', '#ff8c28', '#eb461e'], [0, 0.3, 0.6, 1.0]),
      new ScaleCtor(lerp(0.9, 1.4, intensity), lerp(1.8, 2.6, intensity)),
    ]);

    flame.position.set(position[0], position[1] + 0.5, position[2]);

    // 增强烟雾效果
    const smoke = new EmitterCtor();
    smoke.setRate(new RateCtor(new SpanCtor(22, 38), new SpanCtor(0.012, 0.022)));
    smoke.addInitializers([
      new PositionCtor(new SphereZoneCtor(0, 0, 0, 1.0)),
      new LifeCtor(1.4, 2.8),
      new BodySpriteCtor(this.texture),
      // 烟雾添加横向扩散
      new VelocityCtor(new Vector3DCtor(0, lerp(7, 12, intensity), 0), new SpanCtor(0.4, 0.8)),
    ]);
    smoke.addBehaviours([
      new AlphaCtor(0.4, 0),
      // 烟雾颜色从灰到深灰到黑
      new ColorCtor(['#888888', '#444444', '#1a1a1a'], [0, 0.5, 1.0]),
      new ScaleCtor(lerp(1.4, 1.9, intensity), lerp(2.8, 3.6, intensity)),
    ]);
    smoke.position.set(position[0], position[1] + 1.4, position[2]);

    return { flame, smoke, intensity };
  }

  private updateEmitter(
    entry: FireEmitterEntry,
    position: [number, number, number],
    nextIntensity: number,
    key: string,
  ): void {
    entry.flame.position.set(position[0], position[1] + 0.5, position[2]);
    entry.smoke?.position.set(position[0], position[1] + 1.2, position[2]);
    if (Math.abs(nextIntensity - entry.intensity) < 0.05) {
      entry.intensity = nextIntensity;
      return;
    }
    const replacement = this.createEmitterSet(position, nextIntensity);
    this.removeEmitter(key, entry);
    this.addEmitter(key, replacement, nextIntensity);
  }

  private removeEmitter(key: string, entry: FireEmitterEntry): void {
    entry.flame.stopEmit?.();
    entry.smoke?.stopEmit?.();
    this.system.removeEmitter?.(entry.flame);
    if (entry.smoke) {
      this.system.removeEmitter?.(entry.smoke);
    }
    this.emitters.delete(key);
  }

  private addEmitter(key: string, entry: FireEmitterEntry, intensity: number): void {
    this.system.addEmitter?.(entry.flame);
    entry.smoke && this.system.addEmitter?.(entry.smoke);
    entry.flame.emit?.();
    entry.smoke?.emit?.();
    entry.intensity = intensity;
    this.emitters.set(key, entry);
  }
}
