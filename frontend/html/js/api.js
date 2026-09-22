const API_BASE = "/api";

function getToken() {
  return localStorage.getItem("ft_token");
}

function setSession(token, user) {
  localStorage.setItem("ft_token", token);
  localStorage.setItem("ft_user", JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem("ft_token");
  localStorage.removeItem("ft_user");
}

function getUser() {
  const raw = localStorage.getItem("ft_user");
  return raw ? JSON.parse(raw) : null;
}

async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  headers["Content-Type"] = "application/json";
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (resp.status === 401) {
    clearSession();
    showPage("login");
    throw new Error("Session expired, please log in again");
  }
  if (!resp.ok) {
    let detail = "Request failed";
    try {
      const body = await resp.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {}
    throw new Error(detail);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

const Api = {
  register: (data) => apiFetch("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data) => apiFetch("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  me: () => apiFetch("/auth/me"),
  updateMe: (data) => apiFetch("/auth/me", { method: "PUT", body: JSON.stringify(data) }),

  dashboard: () => apiFetch("/dashboard"),

  listWorkouts: () => apiFetch("/workouts"),
  createWorkout: (data) => apiFetch("/workouts", { method: "POST", body: JSON.stringify(data) }),
  updateWorkout: (id, data) => apiFetch(`/workouts/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteWorkout: (id) => apiFetch(`/workouts/${id}`, { method: "DELETE" }),
  exerciseOptions: () => apiFetch("/exercise-options"),

  listMeals: () => apiFetch("/meals"),
  createMeal: (data) => apiFetch("/meals", { method: "POST", body: JSON.stringify(data) }),
  updateMeal: (id, data) => apiFetch(`/meals/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteMeal: (id) => apiFetch(`/meals/${id}`, { method: "DELETE" }),
  mealOptions: (type) => apiFetch(`/meal-options${type ? `?meal_type=${type}` : ""}`),

  bmi: (data) => apiFetch("/calculator/bmi", { method: "POST", body: JSON.stringify(data) }),
  calorie: (data) => apiFetch("/calculator/calorie", { method: "POST", body: JSON.stringify(data) }),
};
