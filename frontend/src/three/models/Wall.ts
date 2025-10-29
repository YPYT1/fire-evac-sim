import * as THREE from 'three';

/**
 * 墙体：支持开门洞的拉伸几何。
 */
export class Wall {
  private readonly mesh: THREE.Mesh;

  constructor(
    width: number,
    height: number,
    thickness: number,
    color: number = 0xd4c4a8,
    hasDoor: boolean = false,
    doorWidth: number = 2,
    doorHeight: number = 4,
    doorOffset: number = 0
  ) {
    this.mesh = hasDoor
      ? this.createWallWithDoor(width, height, thickness, doorWidth, doorHeight, doorOffset, color)
      : this.createSolidWall(width, height, thickness, color);
    this.mesh.castShadow = true;
    this.mesh.receiveShadow = true;
  }

  private createSolidWall(width: number, height: number, thickness: number, color: number): THREE.Mesh {
    const geometry = new THREE.BoxGeometry(width, height, thickness);
    geometry.translate(0, height / 2, 0);
    const material = new THREE.MeshStandardMaterial({ color, side: THREE.DoubleSide });
    return new THREE.Mesh(geometry, material);
  }

  private createWallWithDoor(
    width: number,
    height: number,
    thickness: number,
    doorWidth: number,
    doorHeight: number,
    doorOffset: number,
    color: number
  ): THREE.Mesh {
    const shape = new THREE.Shape();
    shape.moveTo(-width / 2, 0);
    shape.lineTo(width / 2, 0);
    shape.lineTo(width / 2, height);
    shape.lineTo(-width / 2, height);
    shape.lineTo(-width / 2, 0);

    const hole = new THREE.Path();
    const left = doorOffset - doorWidth / 2;
    const right = doorOffset + doorWidth / 2;
    hole.moveTo(left, 0);
    hole.lineTo(right, 0);
    hole.lineTo(right, doorHeight);
    hole.lineTo(left, doorHeight);
    hole.lineTo(left, 0);
    shape.holes.push(hole);

    const extrudeSettings: THREE.ExtrudeGeometryOptions = {
      depth: thickness,
      bevelEnabled: false,
    };

    const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
    const material = new THREE.MeshStandardMaterial({ color, side: THREE.DoubleSide });
    return new THREE.Mesh(geometry, material);
  }

  setPosition(x: number, y: number, z: number): void {
    this.mesh.position.set(x, y, z);
  }

  setRotation(x: number, y: number, z: number): void {
    this.mesh.rotation.set(x, y, z);
  }

  getMesh(): THREE.Mesh {
    return this.mesh;
  }
}
