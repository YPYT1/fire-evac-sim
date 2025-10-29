/**
 * 管理人群 InstancedMesh 的创建与更新。
 */
import * as THREE from 'three';

export interface AgentVisual {
  mesh: THREE.InstancedMesh;
  maxAgents: number;
}

export function createAgentsVisual(maxAgents: number): AgentVisual {
  const geometry = new THREE.SphereGeometry(0.2, 12, 12);
  const material = new THREE.MeshStandardMaterial({ color: 0xff3b30, emissive: 0x3b0b0b, emissiveIntensity: 0.2 });
  const mesh = new THREE.InstancedMesh(geometry, material, maxAgents);
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  mesh.name = 'Agents';
  return { mesh, maxAgents };
}

export function updateAgentsMatrix(visual: AgentVisual, agents: Array<{ position: [number, number, number] }>): void {
  const dummy = new THREE.Object3D();
  const count = Math.min(agents.length, visual.maxAgents);
  visual.mesh.count = count;
  for (let idx = 0; idx < count; idx += 1) {
    const agent = agents[idx];
    const [x, y, z] = agent.position;
    dummy.position.set(x, y + 0.2, z);
    dummy.updateMatrix();
    visual.mesh.setMatrixAt(idx, dummy.matrix);
  }
  visual.mesh.instanceMatrix.needsUpdate = true;
}
