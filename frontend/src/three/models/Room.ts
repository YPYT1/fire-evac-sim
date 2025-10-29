import * as THREE from 'three';
import { Wall } from './Wall';

export interface DoorConfig {
  wall: 'front' | 'back' | 'left' | 'right';
  width: number;
  height: number;
  offset?: number;
}

/**
 * 四面墙围合的房间，支持在指定墙面开门洞。
 */
export class Room {
  private readonly group: THREE.Group;
  private readonly walls: Map<string, Wall>;

  constructor(
    width: number,
    depth: number,
    height: number,
    wallThickness: number = 0.2,
    wallColor: number = 0xd4c4a8,
    doorConfigs: DoorConfig[] = []
  ) {
    this.group = new THREE.Group();
    this.walls = new Map();
    this.createWalls(width, depth, height, wallThickness, wallColor, doorConfigs);
  }

  private createWalls(
    width: number,
    depth: number,
    height: number,
    thickness: number,
    color: number,
    doors: DoorConfig[]
  ): void {
    const frontDoor = doors.find((d) => d.wall === 'front');
    const backDoor = doors.find((d) => d.wall === 'back');
    const leftDoor = doors.find((d) => d.wall === 'left');
    const rightDoor = doors.find((d) => d.wall === 'right');

    const frontWall = new Wall(
      width,
      height,
      thickness,
      color,
      Boolean(frontDoor),
      frontDoor?.width ?? 2,
      frontDoor?.height ?? 4,
      frontDoor?.offset ?? 0
    );
    frontWall.setPosition(0, 0, depth / 2);
    this.walls.set('front', frontWall);
    this.group.add(frontWall.getMesh());

    const backWall = new Wall(
      width,
      height,
      thickness,
      color,
      Boolean(backDoor),
      backDoor?.width ?? 2,
      backDoor?.height ?? 4,
      backDoor?.offset ?? 0
    );
    backWall.setPosition(0, 0, -depth / 2);
    this.walls.set('back', backWall);
    this.group.add(backWall.getMesh());

    const leftWall = new Wall(
      depth,
      height,
      thickness,
      color,
      Boolean(leftDoor),
      leftDoor?.width ?? 2,
      leftDoor?.height ?? 4,
      leftDoor?.offset ?? 0
    );
    leftWall.setPosition(-width / 2, 0, 0);
    leftWall.setRotation(0, Math.PI / 2, 0);
    this.walls.set('left', leftWall);
    this.group.add(leftWall.getMesh());

    const rightWall = new Wall(
      depth,
      height,
      thickness,
      color,
      Boolean(rightDoor),
      rightDoor?.width ?? 2,
      rightDoor?.height ?? 4,
      rightDoor?.offset ?? 0
    );
    rightWall.setPosition(width / 2, 0, 0);
    rightWall.setRotation(0, Math.PI / 2, 0);
    this.walls.set('right', rightWall);
    this.group.add(rightWall.getMesh());
  }

  setPosition(x: number, y: number, z: number): void {
    this.group.position.set(x, y, z);
  }

  getGroup(): THREE.Group {
    return this.group;
  }
}
