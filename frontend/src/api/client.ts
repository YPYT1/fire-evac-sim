/**
 * REST 与 WebSocket 客户端封装。
 */
const BASE_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

export interface FireSource {
  position: [number, number, number];
  intensity: number;
}

export interface SimStartPayload {
  mode: 'floor1' | 'floor2' | 'floor3';
  fires?: FireSource[];
  agents?: {
    count: number;
    speed_mean: number;
    speed_std: number;
  };
  goals?: string[];
  time_scale?: number;
  avoidance_strategy?: 'rvo2' | 'rvo2_py' | 'simple';
  crowd?: {
    repulsion_radius?: number;
    repulsion_gain?: number;
    repulsion_push_strength?: number;
  };
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
    let errorMessage = `后端返回 ${res.status}: ${res.statusText}`;
    try {
      const errorData = await res.json();
      if (errorData.detail) {
        errorMessage += ` - ${JSON.stringify(errorData.detail)}`;
      }
    } catch {
      // 无法解析错误响应，使用默认消息
    }
    throw new Error(errorMessage);
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
      paths?: number[][][];
      stats?: SimStats;
    }
  | { type: 'end' | 'error'; reason?: string };

export function openSimulationSocket(sessionId: string, onMessage: (msg: WebSocketMessage) => void): WebSocket {
  const wsUrl = buildWebSocketUrl(`/ws/sim/${sessionId}`);
  const ws = new WebSocket(wsUrl);
  ws.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch (error) {
      console.error('WebSocket 消息解析失败：', error);
    }
  };
  ws.onerror = (event) => {
    console.error('WebSocket 连接错误：', event);
  };
  return ws;
}

function buildWebSocketUrl(path: string): string {
  try {
    const url = new URL(BASE_URL, window.location.origin);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.pathname = url.pathname.replace(/\/$/, '') + path;
    return url.toString();
  } catch (error) {
    // 回退方案：简单替换
    console.warn('WebSocket URL 构造失败，使用简单替换方案', error);
    return `${BASE_URL.replace(/^http/, 'ws').replace(/\/$/, '')}${path}`;
  }
}

export async function replanSimulation(payload: SimReplanPayload): Promise<void> {
  await fetch(`${BASE_URL}/sim/replan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
