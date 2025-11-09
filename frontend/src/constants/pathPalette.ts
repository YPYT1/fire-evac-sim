export type FloorBand = 'floor1' | 'floor2' | 'floor3' | 'stair';

interface FloorColorEntry {
  id: FloorBand;
  label: string;
  desc: string;
  core: string;
  halo: string;
}

const FLOOR_HEIGHTS: Record<Exclude<FloorBand, 'stair'>, number> = {
  floor1: 0.0,
  floor2: 4.0,
  floor3: 8.0,
};

const HEIGHT_TOLERANCE = 0.85;

export const PATH_LEGEND: FloorColorEntry[] = [
  {
    id: 'floor3',
    label: '三层走廊',
    desc: '两处楼梯汇入二层',
    core: '#7c3aed',
    halo: '#c084fc',
  },
  {
    id: 'floor2',
    label: '二层连廊',
    desc: '三处楼梯 / 折向一层',
    core: '#0ea5e9',
    halo: '#60a5fa',
  },
  {
    id: 'floor1',
    label: '一层出口',
    desc: '四个门厅汇流',
    core: '#f97316',
    halo: '#fed7aa',
  },
  {
    id: 'stair',
    label: '楼梯 / 垂直通道',
    desc: '跨层下行与缓冲区',
    core: '#fde68a',
    halo: '#fef9c3',
  },
];

const COLOR_LOOKUP: Record<FloorBand, FloorColorEntry> = PATH_LEGEND.reduce((acc, entry) => {
  acc[entry.id] = entry;
  return acc;
}, {} as Record<FloorBand, FloorColorEntry>);

export function classifyFloorByHeight(y: number): FloorBand {
  let best: FloorBand = 'stair';
  let bestDelta = Number.POSITIVE_INFINITY;
  (Object.keys(FLOOR_HEIGHTS) as Array<Exclude<FloorBand, 'stair'>>).forEach((floor) => {
    const delta = Math.abs(y - FLOOR_HEIGHTS[floor]);
    if (delta < bestDelta) {
      best = floor;
      bestDelta = delta;
    }
  });
  if (bestDelta <= HEIGHT_TOLERANCE) {
    return best;
  }
  return 'stair';
}

export function getFloorColor(floor: FloorBand): FloorColorEntry {
  return COLOR_LOOKUP[floor] ?? COLOR_LOOKUP.floor1;
}

export function floorColorHex(floor: FloorBand): string {
  return getFloorColor(floor).core;
}
