/**
 * REST 与 WebSocket 客户端封装。
 */
const BASE_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

export interface FireSource {
  position: [number, number, number];
  intensity: number;
}

export interface SimStartPayload {
  mode: 'fixed' | 'random' | 'manual';
  fires?: FireSource[];
  agents?: {
    count: number;
    speed_mean: number;
    speed_std: number;
  };
  goals?: string[];
}

export interface SimStartResponse {
  session_id: string;
  tick_hz: number;
}

export interface SimReplanPayload {
  session_id: string;
  fires: FireSource[];
  reason?: string;
}

export interface SimStats {
  agent_count: number;
  active_agents: number;
  average_speed: number;
  congestion_ratio: number;
  speed_mean?: number;
  speed_std?: number;
  fire_decay?: number;
}

export async function startSimulation(payload: SimStartPayload): Promise<SimStartResponse> {
  const res = await fetch(`${BASE_URL}/sim/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`startSimulation failed: ${res.statusText}`);
  }
  return res.json();
}

export async function stopSimulation(sessionId: string): Promise<void> {
  await fetch(`${BASE_URL}/sim/stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export type WebSocketMessage =
  | { type: 'hello'; session_id: string }
  | {
      type: 'state';
      tick: number;
      tick_hz?: number;
      agents: unknown[];
      fires: unknown[];
      goals?: unknown[];
      stats?: SimStats;
    }
  | { type: 'end' | 'error'; reason?: string };

export function openSimulationSocket(sessionId: string, onMessage: (msg: WebSocketMessage) => void): WebSocket {
  const ws = new WebSocket(`${BASE_URL.replace('http', 'ws')}/ws/sim/${sessionId}`);
  ws.onmessage = (event) => {
    onMessage(JSON.parse(event.data));
  };
  return ws;
}

export async function replanSimulation(payload: SimReplanPayload): Promise<void> {
  await fetch(`${BASE_URL}/sim/replan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
