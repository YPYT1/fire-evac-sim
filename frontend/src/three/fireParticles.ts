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

  const gradient = context.createRadialGradient(
    size / 2,
    size / 2,
    size * 0.05,
    size / 2,
    size / 2,
    size * 0.48,
  );
  gradient.addColorStop(0, 'rgba(255,255,255,0.95)');
  gradient.addColorStop(0.2, 'rgba(255,214,102,0.95)');
  gradient.addColorStop(0.45, 'rgba(255,127,39,0.8)');
  gradient.addColorStop(0.7, 'rgba(220,30,30,0.5)');
  gradient.addColorStop(1, 'rgba(30,0,0,0)');

  context.fillStyle = gradient;
  context.fillRect(0, 0, size, size);

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

    const rateParticles = lerp(35, 70, Math.min(intensity, 2));
    flame.setRate(new RateCtor(new SpanCtor(rateParticles), new SpanCtor(0.008, 0.012)));

    flame.addInitializers([
      new PositionCtor(new SphereZoneCtor(0, 0, 0, 0.6)),
      new LifeCtor(0.8, 1.5),
      new BodySpriteCtor(this.texture),
      new VelocityCtor(
        new Vector3DCtor(0, lerp(14, 24, intensity), 0),
        new SpanCtor(0.6, 1.4),
      ),
    ]);

    flame.addBehaviours([
      new AlphaCtor(1, 0),
      new ColorCtor('#ffd966', '#ff4d00'),
      new ScaleCtor(lerp(0.8, 1.2, intensity), lerp(1.6, 2.2, intensity)),
    ]);

    flame.position.set(position[0], position[1] + 0.5, position[2]);

    const smoke = new EmitterCtor();
    smoke.setRate(new RateCtor(new SpanCtor(18, 32), new SpanCtor(0.015, 0.02)));
    smoke.addInitializers([
      new PositionCtor(new SphereZoneCtor(0, 0, 0, 0.8)),
      new LifeCtor(1.2, 2.4),
      new BodySpriteCtor(this.texture),
      new VelocityCtor(new Vector3DCtor(0, lerp(6, 10, intensity), 0), new SpanCtor(0.3, 0.6)),
    ]);
    smoke.addBehaviours([
      new AlphaCtor(0.35, 0),
      new ColorCtor('#555555', '#111111'),
      new ScaleCtor(lerp(1.2, 1.6, intensity), lerp(2.5, 3.2, intensity)),
    ]);
    smoke.position.set(position[0], position[1] + 1.2, position[2]);

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
