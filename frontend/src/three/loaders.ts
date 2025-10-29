/**
 * GLB 模型加载工具，附带坐标对齐。
 */
import * as THREE from 'three';
import { Canteen } from './models/Canteen';

const ALIGNMENT_PATH = '/models/building_alignment.json';

interface AlignmentMeta {
  version: number;
  model?: {
    offset?: [number, number, number];
    scale?: number;
    rotation_y_deg?: number;
  };
}

export async function loadBuilding(): Promise<THREE.Group> {
  // 项目当前不使用外部 glb，直接返回程序化模型以避免多余的网络请求与控制台告警。
  const canteen = new Canteen().getGroup();
  canteen.name = 'CanteenModel';
  const alignment = await loadAlignmentMeta();
  applyAlignment(canteen, alignment);
  return canteen;
}

async function loadAlignmentMeta(): Promise<AlignmentMeta | null> {
  try {
    const response = await fetch(ALIGNMENT_PATH);
    if (!response.ok) return null;
    const data = (await response.json()) as AlignmentMeta;
    return data;
  } catch (error) {
    console.warn('加载模型对齐元数据失败，将使用默认值。', error);
    return null;
  }
}

function applyAlignment(model: THREE.Group, alignment: AlignmentMeta | null): void {
  const offset = alignment?.model?.offset ?? [0, 0, 0];
  const scale = alignment?.model?.scale ?? 1;
  const rotation = alignment?.model?.rotation_y_deg ?? 0;

  model.position.set(offset[0], offset[1], offset[2]);
  model.scale.setScalar(scale);
  model.rotation.set(0, (rotation * Math.PI) / 180, 0);
}
