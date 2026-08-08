/**
 * Aarogya API Client — Production-grade, Neon DB backed, no mocks.
 * All calls go to the real FastAPI backend at NEXT_PUBLIC_API_URL.
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const V1 = `${API_BASE_URL}/api/v1`;

// ─── Token Helpers ────────────────────────────────────
function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh_token");
}

async function tryRefresh(): Promise<boolean> {
  const rt = getRefreshToken();
  if (!rt) return false;
  try {
    const res = await fetch(`${V1}/auth/refresh?refresh_token=${encodeURIComponent(rt)}`, { method: "POST" });
    if (!res.ok) return false;
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

function clearTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
  localStorage.removeItem("role");
  localStorage.removeItem("selectedHospitalId");
  window.location.href = "/login";
}

// ─── Core Fetch ───────────────────────────────────────
/**
 * apiFetch — wraps fetch with:
 *  - Automatic Bearer token injection
 *  - Transparent token refresh on 401
 *  - No mock fallbacks — errors surface to the caller
 */
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers || {});

  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  // Don't set Content-Type for FormData (multipart), let browser handle it
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let finalUrl = url;
  if (typeof window !== "undefined") {
    const selectedHospitalId = localStorage.getItem("selectedHospitalId");
    if (selectedHospitalId && selectedHospitalId !== "undefined" && selectedHospitalId !== "null") {
      try {
        const urlObj = new URL(url);
        urlObj.searchParams.set("hospital_id", selectedHospitalId);
        finalUrl = urlObj.toString();
      } catch (e) {
        // Fallback for relative URLs if any
      }
    }
  }

  let res = await fetch(finalUrl, { ...options, headers });

  // Attempt token refresh on 401
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      const newToken = getToken();
      if (newToken) headers.set("Authorization", `Bearer ${newToken}`);
      res = await fetch(finalUrl, { ...options, headers });
    } else {
      clearTokens();
      throw new Error("Session expired. Please log in again.");
    }
  }

  return res;
}

// ─── Auth ────────────────────────────────────────────
export async function apiLogin(username: string, password: string): Promise<{ access_token: string; refresh_token: string; token_type: string }> {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);

  const res = await fetch(`${V1}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Invalid username or password");
  }
  return res.json();
}

export async function apiLogout(refreshToken: string) {
  await fetch(`${V1}/auth/logout?refresh_token=${encodeURIComponent(refreshToken)}`, { method: "POST" }).catch(() => {});
}

export async function apiGetMe(): Promise<ApiUser> {
  const res = await apiFetch(`${V1}/users/me`);
  if (!res.ok) throw new Error("Failed to fetch user profile");
  return res.json();
}

// ─── Types ───────────────────────────────────────────
export interface ApiUser {
  id: number;
  username: string;
  email: string;
  role: string;
  hospital_id: number | null;
  created_at: string;
}

export interface Patient {
  id: number;
  name: string;
  age: number;
  gender: string;
  contact: string | null;
  address: string | null;
  medical_history: string | null;
  hospital_id: number;
  status: string;         // "Outpatient" | "Admitted" | "Discharged"
  admitted_at: string;
  discharged_at: string | null;
}

export interface InventoryItem {
  id: number;
  name: string;
  category: string;
  quantity: number;
  unit: string;
  min_threshold: number;
  status: string;          // "Normal" | "Low Stock"
  expiry_date: string | null;
  batch_number: string | null;
  hospital_id: number;
}

export interface InventoryLog {
  id: number;
  inventory_id: number;
  change_type: string;
  change_amount: number;
  reason: string | null;
  performed_by_user_id: number;
  timestamp: string;
}

export interface Bed {
  id: number;
  hospital_id: number;
  bed_number: string;
  ward: string;
  status: string;           // "Available" | "Occupied" | "Maintenance"
  patient_id: number | null;
  admitted_at: string | null;
}

export interface DailyQRSession {
  id: number;
  hospital_id: number;
  date: string;
  qr_token: string;
  is_active: boolean;
}

export interface AttendanceRecord {
  id: number;
  doctor_id: number;
  session_id: number;
  status: string;
  scanned_via: string | null;
  timestamp: string;
}

export interface AttendanceDashboard {
  date: string;
  total_doctors: number;
  present_doctors: number;
  absent_doctors: number;
}

export interface HealthCentre {
  id: number;
  name: string;
  type: string;
  district: string;
  state: string;
  total_beds: number;
  available_beds: number;
  total_staff: number;
  latitude: number | null;
  longitude: number | null;
  contact_number: string | null;
  email: string | null;
}

export interface ResourceRequest {
  id: number;
  requesting_phc_id: number;
  item_name: string;
  quantity: number;
  urgency: string;
  status: string;
  notes: string | null;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}
