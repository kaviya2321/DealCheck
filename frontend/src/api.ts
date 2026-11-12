import { DealData, HealthStatus, ModelMetricsReport, User, DealInvite } from './types';

const API_BASE = '';

// ---- Auth helpers ----
let _token: string | null = null;

export function setAuthToken(token: string | null) {
  _token = token;
  if (token) localStorage.setItem('dc_token', token);
  else localStorage.removeItem('dc_token');
}

export function getStoredToken(): string | null {
  return _token || localStorage.getItem('dc_token');
}

function authHeaders(): Record<string, string> {
  const token = getStoredToken();
  if (token) return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  return { 'Content-Type': 'application/json' };
}

function authHeadersNoContentType(): Record<string, string> {
  const token = getStoredToken();
  if (token) return { 'Authorization': `Bearer ${token}` };
  return {};
}

async function handleError(res: Response, fallback: string) {
  const data = await res.json().catch(() => ({ detail: fallback }));
  const msg = typeof data.detail === 'string' ? data.detail
    : typeof data.detail === 'object' ? data.detail?.message || fallback
    : fallback;
  throw new Error(msg);
}

// ---- Health ----
export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

// ---- Auth API ----
export async function signup(email: string, password: string, name: string): Promise<{ user: User; token: string }> {
  const res = await fetch(`${API_BASE}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
    credentials: 'include',
  });
  if (!res.ok) await handleError(res, 'Signup failed.');
  const data = await res.json();
  setAuthToken(data.token);
  return data;
}

export async function login(email: string, password: string): Promise<{ user: User; token: string }> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
    credentials: 'include',
  });
  if (!res.ok) await handleError(res, 'Login failed. Check your email and password.');
  const data = await res.json();
  setAuthToken(data.token);
  return data;
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST', credentials: 'include' });
  setAuthToken(null);
}

export async function getMe(): Promise<User | null> {
  const token = getStoredToken();
  if (!token) return null;
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: authHeaders(),
      credentials: 'include',
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.user;
  } catch {
    return null;
  }
}

// ---- Deals API ----
export async function createDeal(itemName: string, price: number, currency = 'USD'): Promise<DealData> {
  const res = await fetch(`${API_BASE}/api/deals`, {
    method: 'POST',
    headers: authHeaders(),
    credentials: 'include',
    body: JSON.stringify({ item_name: itemName, price, currency }),
  });
  if (!res.ok) await handleError(res, 'Failed to create deal.');
  return res.json();
}

export async function fetchMyDeals(): Promise<DealData[]> {
  const res = await fetch(`${API_BASE}/api/deals`, {
    headers: authHeaders(),
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to fetch deals.');
  return res.json();
}

export async function fetchDealById(id: string): Promise<DealData> {
  const res = await fetch(`${API_BASE}/api/deals/${id}`, {
    headers: authHeaders(),
    credentials: 'include',
  });
  if (!res.ok) throw new Error(`Deal ${id} not found.`);
  return res.json();
}

export async function getInvitePreview(token: string): Promise<DealInvite> {
  const res = await fetch(`${API_BASE}/api/invites/${token}`);
  if (!res.ok) await handleError(res, 'Invite link invalid or expired.');
  return res.json();
}

export async function joinDeal(token: string): Promise<{ deal_id: string; role: string }> {
  const res = await fetch(`${API_BASE}/api/deals/join/${token}`, {
    method: 'POST',
    headers: authHeaders(),
    credentials: 'include',
  });
  if (!res.ok) await handleError(res, 'Failed to join deal.');
  return res.json();
}

export async function agreeTerms(dealId: string, agreed = true): Promise<DealData> {
  const res = await fetch(`${API_BASE}/api/deals/${dealId}/agree`, {
    method: 'POST',
    headers: authHeaders(),
    credentials: 'include',
    body: JSON.stringify({ agreed }),
  });
  if (!res.ok) await handleError(res, 'Failed to confirm agreement.');
  return res.json();
}

export async function deleteDeal(dealId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/deals/${dealId}`, {
    method: 'DELETE',
    headers: authHeaders(),
    credentials: 'include',
  });
  if (!res.ok) await handleError(res, 'Failed to delete deal.');
}

export async function getDealMessages(dealId: string): Promise<import('./types').ChatMessage[]> {
  const res = await fetch(`${API_BASE}/api/deals/${dealId}/messages`, {
    headers: authHeaders(),
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to fetch messages.');
  return res.json();
}

export async function askDealCheckAi(dealId: string, question: string): Promise<{ question: string; answer: string }> {
  const res = await fetch(`${API_BASE}/api/deals/${dealId}/ask-ai`, {
    method: 'POST',
    headers: authHeaders(),
    credentials: 'include',
    body: JSON.stringify({ question }),
  });
  if (!res.ok) await handleError(res, 'DealCheck AI is unavailable right now.');
  return res.json();
}

// ---- Legacy / Direct API (kept for backward compat) ----
export async function extractChat(
  input: { file?: File; text?: string; item_name?: string; price?: number }
): Promise<{
  source_type: 'text_paste' | 'screenshot';
  chat_text: string;
  item_name: string;
  price: number;
  currency: string;
}> {
  const formData = new FormData();
  if (input.file) formData.append('file', input.file);
  if (input.text) formData.append('text', input.text);
  if (input.item_name) formData.append('item_name', input.item_name);
  if (input.price !== undefined) formData.append('price', String(input.price));

  const res = await fetch(`${API_BASE}/api/extract`, {
    method: 'POST',
    headers: authHeadersNoContentType(),
    body: formData,
  });
  if (!res.ok) await handleError(res, 'Failed to extract chat content.');
  return res.json();
}

export async function analyzeDeal(payload: {
  chat_text: string;
  item_name: string;
  price: number;
  currency?: string;
  source_type?: string;
}): Promise<DealData> {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) await handleError(res, 'Analysis failed.');
  return res.json();
}

export async function createProtectionLink(dealId: string): Promise<{
  deal_id: string;
  order_id: string;
  approval_url: string;
  status: string;
  amount: number;
  currency: string;
  drafted_message: string;
  sandbox_notice: string;
}> {
  const res = await fetch(`${API_BASE}/api/protect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ deal_id: dealId }),
  });
  if (!res.ok) await handleError(res, 'PayPal link creation failed.');
  return res.json();
}

export async function sendSellerReply(dealId: string, replyText: string): Promise<{
  deal_id: string;
  old_score: number;
  new_score: number;
  verdict: 'LOW' | 'MEDIUM' | 'HIGH';
  seller_classification: string;
  confidence: number;
  litmus_verdict: string;
  summary: string;
  probabilities: Record<string, number>;
}> {
  const res = await fetch(`${API_BASE}/api/seller-reply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ deal_id: dealId, reply_text: replyText }),
  });
  if (!res.ok) await handleError(res, 'Failed to evaluate seller reply.');
  return res.json();
}

export async function capturePayPalOrder(orderId: string, dealId?: string): Promise<{
  status: string;
  order_id: string;
  capture_id: string;
  deal_id?: string;
  sandbox_notice: string;
}> {
  const url = `${API_BASE}/api/paypal/return?token=${encodeURIComponent(orderId)}${dealId ? `&deal_id=${encodeURIComponent(dealId)}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) await handleError(res, 'Failed to capture PayPal order.');
  return res.json();
}

export async function fetchDeals(): Promise<DealData[]> {
  return fetchMyDeals();
}

export async function fetchModelMetrics(): Promise<ModelMetricsReport> {
  const res = await fetch(`${API_BASE}/api/model/metrics`);
  if (!res.ok) throw new Error('Failed to load model metrics');
  return res.json();
}

export async function clearAllData(): Promise<void> {
  const res = await fetch(`${API_BASE}/api/data`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to clear data');
}

// ---- WebSocket helper ----
export function createDealRoomSocket(dealId: string): WebSocket {
  const token = getStoredToken();
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const url = `${protocol}//${host}/ws/deals/${dealId}${token ? `?token=${encodeURIComponent(token)}` : ''}`;
  return new WebSocket(url);
}
