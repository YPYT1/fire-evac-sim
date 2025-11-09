import * as THREE from 'three';
import { Room } from './Room';
import { Staircase } from './Staircase';
import { Wall } from './Wall';

/**
 * 三层食堂模型，尺寸 60m × 60m，每层 4m 高。
 */
export class Canteen {
  private readonly group: THREE.Group;

  private readonly totalWidth = 60;
  private readonly totalDepth = 60;
  private readonly wallHeight = 4;
  private readonly wallThickness = 0.2;
  private readonly floors = 3;

  private readonly roomWidth = 18;
  private readonly roomDepth = 18;
  private readonly corridorWidth = 24;

  private readonly doorWidth = 3;
  private readonly doorHeight = 3.5;
  private readonly wallColor = 0xe8d5b7;

  constructor() {
    this.group = new THREE.Group();
    this.build();
  }

  private build(): void {
    for (let floor = 0; floor < this.floors; floor++) {
      const floorY = floor * this.wallHeight;
      const groundFloor = floor === 0;

      if (groundFloor) {
        this.createOuterWalls(floorY, true);
      }

      this.createCorridors(floorY);
      this.createCornerRooms(floorY);
      this.createSeating(floorY);
      this.createFloor(floorY);
    }

    this.createStaircases();
  }

  private createOuterWalls(floorY: number, hasDoors: boolean): void {
    const isSecondFloor = floorY === this.wallHeight;
    const frontDoorWidth = isSecondFloor ? this.doorWidth + 2 : this.doorWidth;
    const frontDoorHeight = isSecondFloor ? this.doorHeight : this.doorHeight;
    const allowFrontDoor = hasDoors || isSecondFloor;
    const allowBackDoor = hasDoors;
    const allowSideDoor = hasDoors;

    const frontWall = new Wall(
      this.totalWidth,
      this.wallHeight,
      this.wallThickness,
      this.wallColor,
      allowFrontDoor,
      frontDoorWidth,
      frontDoorHeight,
      0
    );
    frontWall.setPosition(0, floorY, this.totalDepth / 2);
    this.group.add(frontWall.getMesh());

    const backWall = new Wall(
      this.totalWidth,
      this.wallHeight,
      this.wallThickness,
      this.wallColor,
      allowBackDoor,
      this.doorWidth,
      this.doorHeight,
      0
    );
    backWall.setPosition(0, floorY, -this.totalDepth / 2);
    this.group.add(backWall.getMesh());

    const leftWall = new Wall(
      this.totalDepth,
      this.wallHeight,
      this.wallThickness,
      this.wallColor,
      allowSideDoor,
      this.doorWidth,
      this.doorHeight,
      0
    );
    leftWall.setPosition(-this.totalWidth / 2, floorY, 0);
    leftWall.setRotation(0, Math.PI / 2, 0);
    this.group.add(leftWall.getMesh());

    const rightWall = new Wall(
      this.totalDepth,
      this.wallHeight,
      this.wallThickness,
      this.wallColor,
      allowSideDoor,
      this.doorWidth,
      this.doorHeight,
      0
    );
    rightWall.setPosition(this.totalWidth / 2, floorY, 0);
    rightWall.setRotation(0, Math.PI / 2, 0);
    this.group.add(rightWall.getMesh());
  }

  private createCorridors(floorY: number): void {
    const material = new THREE.MeshStandardMaterial({ color: 0xe9e6df });
    const addPlane = (width: number, depth: number, centerX: number, centerZ: number) => {
      if (width <= 0 || depth <= 0) return;
      const geometry = new THREE.BoxGeometry(width, 0.1, depth);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(centerX, floorY + 0.05, centerZ);
      mesh.receiveShadow = true;
      this.group.add(mesh);
    };

    if (floorY === 0) {
      addPlane(this.totalWidth, this.corridorWidth, 0, 0);
      addPlane(this.corridorWidth, this.totalDepth, 0, 0);
      return;
    }

    const holes = this.getStairHoles(floorY);
    const halfWidth = this.totalWidth / 2;
    const halfDepth = this.totalDepth / 2;

    const holeXRanges = holes
      .map(({ x, width }) => [x - width / 2, x + width / 2] as [number, number])
      .sort((a, b) => a[0] - b[0]);

    let start = -halfWidth;
    holeXRanges.forEach(([left, right]) => {
      const end = Math.min(left, halfWidth);
      if (end - start > 0) {
        const width = end - start;
        const centerX = start + width / 2;
        addPlane(width, this.corridorWidth, centerX, 0);
      }
      start = Math.max(right, start);
    });
    if (halfWidth - start > 0) {
      const width = halfWidth - start;
      const centerX = start + width / 2;
      addPlane(width, this.corridorWidth, centerX, 0);
    }

    const holeZRanges = holes
      .map(({ z, depth }) => [z - depth / 2, z + depth / 2] as [number, number])
      .sort((a, b) => a[0] - b[0]);

    let vertical = -halfDepth;
    holeZRanges.forEach(([back, front]) => {
      const end = Math.min(back, halfDepth);
      if (end - vertical > 0) {
        const depth = end - vertical;
        const centerZ = vertical + depth / 2;
        addPlane(this.corridorWidth, depth, 0, centerZ);
      }
      vertical = Math.max(front, vertical);
    });
    if (halfDepth - vertical > 0) {
      const depth = halfDepth - vertical;
      const centerZ = vertical + depth / 2;
      addPlane(this.corridorWidth, depth, 0, centerZ);
    }
  }

  private createCornerRooms(floorY: number): void {
    const offsetX = this.corridorWidth / 2 + this.roomWidth / 2;
    const offsetZ = this.corridorWidth / 2 + this.roomDepth / 2;

    const doorNorthSouth = [
      {
        wall: 'back' as const,
        width: this.doorWidth,
        height: this.doorHeight,
        offset: 0,
      },
    ];
    const doorSouthNorth = [
      {
        wall: 'front' as const,
        width: this.doorWidth,
        height: this.doorHeight,
        offset: 0,
      },
    ];

    const northwest = new Room(
      this.roomWidth,
      this.roomDepth,
      this.wallHeight,
      this.wallThickness,
      this.wallColor,
      doorNorthSouth
    );
    northwest.setPosition(-offsetX, floorY, offsetZ);
    this.group.add(northwest.getGroup());

    const northeast = new Room(
      this.roomWidth,
      this.roomDepth,
      this.wallHeight,
      this.wallThickness,
      this.wallColor,
      doorNorthSouth
    );
    northeast.setPosition(offsetX, floorY, offsetZ);
    this.group.add(northeast.getGroup());

    const southwest = new Room(
      this.roomWidth,
      this.roomDepth,
      this.wallHeight,
      this.wallThickness,
      this.wallColor,
      doorSouthNorth
    );
    southwest.setPosition(-offsetX, floorY, -offsetZ);
    this.group.add(southwest.getGroup());

    const southeast = new Room(
      this.roomWidth,
      this.roomDepth,
      this.wallHeight,
      this.wallThickness,
      this.wallColor,
      doorSouthNorth
    );
    southeast.setPosition(offsetX, floorY, -offsetZ);
    this.group.add(southeast.getGroup());
  }

  private createSeating(floorY: number): void {
    const offsets = [-8, 0, 8];
    const stairZones = this.getStairLayout()
      .filter((layout) => layout.occupiedLevels.includes(floorY))
      .map(({ x, z, clearanceX, clearanceZ }) => ({
        x,
        z,
        clearanceX: clearanceX ?? 6,
        clearanceZ: clearanceZ ?? 6,
      }));

    offsets.forEach((x) => {
      offsets.forEach((z) => {
        if (Math.abs(x) < 1 && Math.abs(z) < 1) return;

        const nearStair = stairZones.some(
          (stair) =>
            Math.abs(x - stair.x) < stair.clearanceX && Math.abs(z - stair.z) < stair.clearanceZ
        );
        if (nearStair) return;

        const set = this.createDiningSet();
        set.position.set(x, floorY, z);
        this.group.add(set);
      });
    });
  }

  private createDiningSet(): THREE.Group {
    const group = new THREE.Group();
    const tableMaterial = new THREE.MeshStandardMaterial({ color: 0xc8c2b5 });
    const legMaterial = new THREE.MeshStandardMaterial({ color: 0x8d7b63 });
    const benchMaterial = new THREE.MeshStandardMaterial({ color: 0xb5aa94 });

    const tableTopGeometry = new THREE.BoxGeometry(4, 0.1, 2);
    tableTopGeometry.translate(0, 0.75, 0);
    const tableTop = new THREE.Mesh(tableTopGeometry, tableMaterial);
    tableTop.castShadow = true;
    tableTop.receiveShadow = true;
    group.add(tableTop);

    const legGeometry = new THREE.BoxGeometry(0.2, 0.75, 0.2);
    legGeometry.translate(0, 0.375, 0);
    const legOffsets: Array<[number, number]> = [
      [-1.7, -0.7],
      [1.7, -0.7],
      [-1.7, 0.7],
      [1.7, 0.7],
    ];
    legOffsets.forEach(([x, z]) => {
      const leg = new THREE.Mesh(legGeometry, legMaterial);
      leg.position.set(x, 0, z);
      leg.castShadow = true;
      leg.receiveShadow = true;
      group.add(leg);
    });

    const benchGeometry = new THREE.BoxGeometry(3.6, 0.15, 0.5);
    benchGeometry.translate(0, 0.225, 0);
    const benchOffset = 1.5;
    [-benchOffset, benchOffset].forEach((z) => {
      const bench = new THREE.Mesh(benchGeometry, benchMaterial);
      bench.position.set(0, 0, z);
      bench.castShadow = true;
      bench.receiveShadow = true;
      group.add(bench);
    });

    return group;
  }

  private createFloor(floorY: number): void {
    const material = new THREE.MeshStandardMaterial({ color: 0xd9d9d9, side: THREE.DoubleSide });
    if (floorY === 0) {
      const geometry = new THREE.PlaneGeometry(this.totalWidth, this.totalDepth);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.rotation.x = -Math.PI / 2;
      mesh.position.y = floorY + 0.01;
      mesh.receiveShadow = true;
      this.group.add(mesh);

      const apronMaterial = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, side: THREE.DoubleSide });
      const apronGeometry = new THREE.PlaneGeometry(this.totalWidth, 12);
      const apron = new THREE.Mesh(apronGeometry, apronMaterial);
      apron.rotation.x = -Math.PI / 2;
      apron.position.set(0, floorY + 0.009, -this.totalDepth / 2 - 6);
      apron.receiveShadow = true;
      this.group.add(apron);
      return;
    }

    const shape = new THREE.Shape();
    const halfWidth = this.totalWidth / 2;
    const halfDepth = this.totalDepth / 2;
    shape.moveTo(-halfWidth, -halfDepth);
    shape.lineTo(halfWidth, -halfDepth);
    shape.lineTo(halfWidth, halfDepth);
    shape.lineTo(-halfWidth, halfDepth);
    shape.lineTo(-halfWidth, -halfDepth);

    this.getStairHoles(floorY).forEach(({ x, z, width, depth }) => {
      const hole = new THREE.Path();
      const halfW = width / 2;
      const halfD = depth / 2;
      hole.moveTo(x - halfW, z - halfD);
      hole.lineTo(x - halfW, z + halfD);
      hole.lineTo(x + halfW, z + halfD);
      hole.lineTo(x + halfW, z - halfD);
      hole.lineTo(x - halfW, z - halfD);
      shape.holes.push(hole);
    });

    const geometry = new THREE.ShapeGeometry(shape);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.y = floorY + 0.01;
    mesh.receiveShadow = true;
    this.group.add(mesh);

  }

  private getStairHoles(
    floorY: number
  ): Array<{ x: number; z: number; width: number; depth: number }> {
    const defaultWidth = 5;
    const defaultDepth = 8;
    return this.getStairLayout()
      .filter(({ holeLevels }) => holeLevels.includes(floorY))
      .map(({ x, z, holeX, holeZ, holeWidth, holeDepth }) => ({
        x: holeX ?? x,
        z: holeZ ?? z,
        width: holeWidth ?? defaultWidth,
        depth: holeDepth ?? defaultDepth,
      }));
  }

  private createStaircases(): void {
    this.getStairLayout().forEach(
      ({ x, z, rotation, baseLevels, width, depth, steps, color }) => {
        baseLevels.forEach((baseY) => {
          const staircase = new Staircase(
            width ?? 5,
            this.wallHeight,
            depth ?? 6,
            steps ?? 12,
            color ?? 0xb5aa94
          );
          staircase.setPosition(x, baseY, z);
          staircase.setRotation(0, rotation, 0);
          this.group.add(staircase.getGroup());
        });
      }
    );
  }

  private getStairLayout(): Array<{
    x: number;
    z: number;
    rotation: number;
    baseLevels: number[];
    holeLevels: number[];
    occupiedLevels: number[];
    width?: number;
    depth?: number;
    steps?: number;
    color?: number;
    clearanceX?: number;
    clearanceZ?: number;
    holeX?: number;
    holeZ?: number;
    holeWidth?: number;
    holeDepth?: number;
  }> {
    type StairConfig = {
      x: number;
      z: number;
      rotation: number;
      baseLevels: number[];
      holeLevels: number[];
      occupiedLevels: number[];
      width?: number;
      depth?: number;
      steps?: number;
      color?: number;
      clearanceX?: number;
      clearanceZ?: number;
      holeX?: number;
      holeZ?: number;
      holeWidth?: number;
      holeDepth?: number;
    };
    const offsetX = this.totalWidth / 2 - 7;
    const sharedBaseLevels = [0, this.wallHeight];
    const sharedHoleLevels = [this.wallHeight, this.wallHeight * 2];
    const sharedOccupiedLevels = [0, this.wallHeight, this.wallHeight * 2];

    const layouts: StairConfig[] = [
      {
        x: -offsetX,
        z: 0,
        rotation: Math.PI / 2,
        baseLevels: sharedBaseLevels,
        holeLevels: sharedHoleLevels,
        occupiedLevels: sharedOccupiedLevels,
        clearanceX: 6,
        clearanceZ: 6,
      },
      {
        x: offsetX,
        z: 0,
        rotation: -Math.PI / 2,
        baseLevels: sharedBaseLevels,
        holeLevels: sharedHoleLevels,
        occupiedLevels: sharedOccupiedLevels,
        clearanceX: 6,
        clearanceZ: 6,
      },
    ];

    const externalWidth = 6;
    const externalDepth = 12;
    const externalSteps = 10;
    const stepDepth = externalDepth / externalSteps;
    const topOffset = externalDepth / 2 - stepDepth / 2;
    const connectOffset = 0.0;
    const buildingFront = -this.totalDepth / 2;
    const externalCenterZ = buildingFront + connectOffset - topOffset;
    layouts.push({
      x: 0,
      z: externalCenterZ,
      rotation: 0,
      baseLevels: [0],
      holeLevels: [],
      occupiedLevels: [0, this.wallHeight],
      width: externalWidth,
      depth: externalDepth,
      steps: externalSteps,
      clearanceX: 6,
      clearanceZ: 8,
    });

    return layouts;
  }

  getGroup(): THREE.Group {
    return this.group;
  }
}
