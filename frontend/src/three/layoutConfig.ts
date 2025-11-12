export interface LayoutFloorConfig {
  level: number;
  includeOuterWalls: boolean;
  cornerRooms: boolean;
  seating?: {
    spacingX: number;
    spacingZ: number;
    marginX: number;
    marginZ: number;
    centralClearance?: number;
    excludedZones?: Array<{ x: number; z: number; halfWidth: number; halfDepth: number }>;
  };
  sideRoom?: {
    side: 'east' | 'west' | 'south' | 'north';
    width: number;
    depth: number;
    offsetZ?: number;
    offsetX?: number;
    centerX?: number;
    centerZ?: number;
    doorWidth?: number;
    doorHeight?: number;
    doorOffset?: number;
  };
}

export interface LayoutConfig {
  stairs: {
    westEnabled: boolean;
    eastEnabled: boolean;
    southEnabled: boolean;
  };
  floors: LayoutFloorConfig[];
}

export const layoutConfig: LayoutConfig = {
  stairs: {
    westEnabled: true,
    eastEnabled: true,
    southEnabled: true,
  },
  floors: [
    {
      level: 0,
      includeOuterWalls: true,
      cornerRooms: false,
      seating: {
        spacingX: 5,
        spacingZ: 5,
        marginX: 6,
        marginZ: 6,
        centralClearance: 5,
      },
    },
    {
      level: 1,
      includeOuterWalls: false,
      cornerRooms: false,
      seating: {
        spacingX: 5,
        spacingZ: 5,
        marginX: 6,
        marginZ: 6,
        centralClearance: 6,
      },
    },
    {
      level: 2,
      includeOuterWalls: false,
      cornerRooms: false,
      sideRoom: {
        side: 'north',
        width: 44,
        depth: 14,
        offsetX: 0,
        centerZ: 23,
        doorWidth: 3,
        doorHeight: 3.5,
        doorOffset: 0,
      },
      seating: {
        spacingX: 6,
        spacingZ: 6,
        marginX: 10,
        marginZ: 10,
        centralClearance: 6,
        excludedZones: [{ x: 0, z: 23, halfWidth: 24, halfDepth: 14 }],
      },
    },
  ],
};
