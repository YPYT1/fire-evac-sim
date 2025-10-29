import * as THREE from 'three';

/**
 * 简化楼梯模型：连续台阶与扶手。
 */
export class Staircase {
  private readonly group: THREE.Group;

  constructor(
    width: number = 3,
    height: number = 4,
    depth: number = 6,
    steps: number = 12,
    color: number = 0xb5aa94
  ) {
    this.group = new THREE.Group();
    this.createSteps(width, height, depth, steps, color);
    this.createHandrails(width, height, depth, color);
  }

  private createSteps(width: number, height: number, depth: number, steps: number, color: number): void {
    const stepHeight = height / steps;
    const stepDepth = depth / steps;
    const material = new THREE.MeshStandardMaterial({ color });

    for (let i = 0; i < steps; i++) {
      const geometry = new THREE.BoxGeometry(width, stepHeight, stepDepth);
      const mesh = new THREE.Mesh(geometry, material);
      const currentHeight = stepHeight * (i + 1);
      const currentDepth = stepDepth * (i + 1);
      mesh.position.set(0, currentHeight - stepHeight / 2, -depth / 2 + currentDepth - stepDepth / 2);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      this.group.add(mesh);
    }
  }

  private createHandrails(width: number, height: number, depth: number, color: number): void {
    const material = new THREE.MeshStandardMaterial({ color, metalness: 0.3, roughness: 0.7 });
    const postGeometry = new THREE.CylinderGeometry(0.05, 0.05, height + 0.5, 8);

    const leftPost = new THREE.Mesh(postGeometry, material);
    leftPost.position.set(-width / 2, (height + 0.5) / 2, -depth / 2);
    leftPost.castShadow = true;
    this.group.add(leftPost);

    const leftPostEnd = leftPost.clone();
    leftPostEnd.position.z = depth / 2;
    this.group.add(leftPostEnd);

    const rightPost = leftPost.clone();
    rightPost.position.x = width / 2;
    this.group.add(rightPost);

    const rightPostEnd = leftPostEnd.clone();
    rightPostEnd.position.x = width / 2;
    this.group.add(rightPostEnd);

    const railLength = Math.sqrt(depth * depth + height * height);
    const railGeometry = new THREE.CylinderGeometry(0.04, 0.04, railLength, 8);
    const leftRail = new THREE.Mesh(railGeometry, material);
    leftRail.position.set(-width / 2, height / 2 + 0.25, 0);
    leftRail.rotation.x = Math.PI / 2 - Math.atan2(height, depth);
    this.group.add(leftRail);

    const rightRail = leftRail.clone();
    rightRail.position.x = width / 2;
    this.group.add(rightRail);
  }

  setPosition(x: number, y: number, z: number): void {
    this.group.position.set(x, y, z);
  }

  setRotation(x: number, y: number, z: number): void {
    this.group.rotation.set(x, y, z);
  }

  getGroup(): THREE.Group {
    return this.group;
  }
}
