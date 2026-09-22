let workoutModal, mealModal;

document.addEventListener("DOMContentLoaded", () => {
  workoutModal = new bootstrap.Modal(document.getElementById("workoutModal"));
  mealModal = new bootstrap.Modal(document.getElementById("mealModal"));

  if (getToken()) {
    document.getElementById("nav").style.display = "flex";
    showPage("dashboard");
  } else {
    showPage("login");
  }
});

function showToast(message, type = "success") {
  const area = document.getElementById("toast-area");
  const div = document.createElement("div");
  div.className = `alert alert-${type} shadow-sm`;
  div.textContent = message;
  area.appendChild(div);
  setTimeout(() => div.remove(), 3500);
}

function showPage(name) {
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.getElementById(`page-${name}`).classList.add("active");
  document.querySelectorAll("#nav .nav-link[data-nav]").forEach((el) => {
    el.classList.toggle("current", el.dataset.nav === name);
  });

  if (name === "dashboard") loadDashboard();
  if (name === "workouts") loadWorkouts();
  if (name === "meals") loadMeals();
}

// Animates a stat number counting up from 0 — the one deliberate motion moment.
function countUp(el, target, suffix = "") {
  const duration = 700;
  const start = performance.now();
  const from = 0;
  function frame(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(from + (target - from) * eased) + suffix;
    if (progress < 1) requestAnimationFrame(frame);
  }
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    el.textContent = target + suffix;
  } else {
    requestAnimationFrame(frame);
  }
}

function renderStat(el, value, suffix = "") {
  if (value === null || value === undefined) {
    el.textContent = "—";
    return;
  }

  countUp(el, value, suffix);
}

async function handleLogin(e) {
  e.preventDefault();
  try {
    const data = await Api.login({
      email: document.getElementById("login-email").value,
      password: document.getElementById("login-password").value,
    });
    setSession(data.access_token, data.user);
    document.getElementById("nav").style.display = "flex";
    showPage("dashboard");
  } catch (err) {
    showToast(err.message, "danger");
  }
  return false;
}

async function handleRegister(e) {
  e.preventDefault();
  try {
    const data = await Api.register({
      full_name: document.getElementById("reg-name").value,
      email: document.getElementById("reg-email").value,
      password: document.getElementById("reg-password").value,
      age: numOrNull("reg-age"),
      gender: document.getElementById("reg-gender").value || null,
      weight: numOrNull("reg-weight"),
      height: numOrNull("reg-height"),
    });
    setSession(data.access_token, data.user);
    document.getElementById("nav").style.display = "flex";
    showPage("dashboard");
  } catch (err) {
    showToast(err.message, "danger");
  }
  return false;
}

function logout() {
  clearSession();
  document.getElementById("nav").style.display = "none";
  showPage("login");
}

function numOrNull(id) {
  const v = document.getElementById(id).value;
  return v === "" ? null : Number(v);
}

function emptyState(icon, message, ctaLabel, ctaFn) {
  return `
    <div class="empty-state">
      <i class="bi ${icon}"></i>
      <div>${message}</div>
      ${ctaLabel ? `<div class="cta mt-2" onclick="${ctaFn}">${ctaLabel}</div>` : ""}
    </div>`;
}

// --- Dashboard ---
async function loadDashboard() {
  try {
    const data = await Api.dashboard();
    document.getElementById("dash-name").textContent = data.user.full_name.split(" ")[0];
    const workoutAvailable = data.service_status?.workout?.available !== false;
    const mealAvailable = data.service_status?.meal?.available !== false;
    renderStat(document.getElementById("stat-in"), data.today.calories_consumed);
    renderStat(document.getElementById("stat-out"), data.today.calories_burned);
    renderStat(document.getElementById("stat-net"), data.today.net_calories);
    renderStat(document.getElementById("stat-minutes"), data.today.workout_minutes, " min");
    const wBox = document.getElementById("dash-recent-workouts");
    if (!workoutAvailable) {
	wBox.innerHTML = emptyState("bi-exclamation-triangle", "Workout data is temporarily unavailable.");
    } else { wBox.innerHTML = data.recent_workouts.length
      ? data.recent_workouts.map((w) => `
        <div class="row-item">
          <div class="row-icon ember"><i class="bi bi-fire"></i></div>
          <div class="flex-grow-1"><div class="row-title">${w.title}</div><div class="row-meta">${w.workout_date}</div></div>
          <div class="row-value">${w.calories_burned} kcal</div>
        </div>`).join("")
      : emptyState("bi-activity", "No workouts logged yet.", "Log your first workout", "showPage('workouts')");}

    const mBox = document.getElementById("dash-recent-meals");
    if(!mealAvailable) {
	mBox.innerHTML = emptyState("bi-exclamation-triangle", "Meal data is temporarily unavailable.");
    } else { mBox.innerHTML = data.recent_meals.length
      ? data.recent_meals.map((m) => `
        <div class="row-item">
          <div class="row-icon citrus"><i class="bi bi-egg-fried"></i></div>
          <div class="flex-grow-1"><div class="row-title">${m.name}</div><div class="row-meta">${m.meal_date}</div></div>
          <div class="row-value">${m.calories} kcal</div>
        </div>`).join("")
      : emptyState("bi-cup-straw", "No meals logged yet.", "Log your first meal", "showPage('meals')");}
  } catch (err) {
    showToast(err.message, "danger");
  }
}

// --- Workouts ---
async function loadWorkouts() {
  try {
    const workouts = await Api.listWorkouts();
    const list = document.getElementById("workout-list");
    list.innerHTML = workouts.length
      ? workouts.map((w) => `
        <div class="row-item">
          <div class="row-icon ember"><i class="bi bi-fire"></i></div>
          <div class="flex-grow-1">
            <div class="row-title">${w.title} <span class="row-badge">${w.type}</span></div>
            <div class="row-meta">${w.workout_date} · ${w.duration_minutes} min</div>
          </div>
          <div class="row-value">${w.calories_burned} kcal</div>
          <button class="btn btn-sm btn-outline-danger ms-2" onclick="deleteWorkout(${w.id})"><i class="bi bi-trash3"></i></button>
        </div>`).join("")
      : emptyState("bi-activity", "Nothing here yet — your workouts will show up as you log them.", "Add a workout", "openWorkoutModal(); new bootstrap.Modal(document.getElementById('workoutModal')).show()");
  } catch (err) {
    showToast(err.message, "danger");
  }
}

function openWorkoutModal() {
  document.getElementById("workout-form").reset();
  document.getElementById("workout-id").value = "";
}

async function handleWorkoutSubmit(e) {
  e.preventDefault();
  try {
    await Api.createWorkout({
      title: document.getElementById("w-title").value,
      type: document.getElementById("w-type").value,
      duration_minutes: Number(document.getElementById("w-duration").value),
      calories_burned: Number(document.getElementById("w-calories").value),
      workout_date: document.getElementById("w-date").value,
      description: document.getElementById("w-desc").value || null,
    });
    workoutModal.hide();
    showToast("Workout logged");
    loadWorkouts();
  } catch (err) {
    showToast(err.message, "danger");
  }
  return false;
}

async function deleteWorkout(id) {
  try {
    await Api.deleteWorkout(id);
    loadWorkouts();
  } catch (err) {
    showToast(err.message, "danger");
  }
}

// --- Meals ---
async function loadMeals() {
  try {
    const meals = await Api.listMeals();
    const list = document.getElementById("meal-list");
    list.innerHTML = meals.length
      ? meals.map((m) => `
        <div class="row-item">
          <div class="row-icon citrus"><i class="bi bi-egg-fried"></i></div>
          <div class="flex-grow-1">
            <div class="row-title">${m.name} <span class="row-badge">${m.meal_type}</span></div>
            <div class="row-meta">${m.meal_date} · P${m.protein}g · C${m.carbs}g · F${m.fat}g</div>
          </div>
          <div class="row-value">${m.calories} kcal</div>
          <button class="btn btn-sm btn-outline-danger ms-2" onclick="deleteMeal(${m.id})"><i class="bi bi-trash3"></i></button>
        </div>`).join("")
      : emptyState("bi-cup-straw", "Nothing here yet — your meals will show up as you log them.", "Add a meal", "openMealModal(); new bootstrap.Modal(document.getElementById('mealModal')).show()");
  } catch (err) {
    showToast(err.message, "danger");
  }
}

function openMealModal() {
  document.getElementById("meal-form").reset();
  document.getElementById("meal-id").value = "";
}

async function handleMealSubmit(e) {
  e.preventDefault();
  try {
    await Api.createMeal({
      name: document.getElementById("m-name").value,
      meal_type: document.getElementById("m-type").value,
      calories: Number(document.getElementById("m-calories").value),
      protein: numOrNull("m-protein") || 0,
      carbs: numOrNull("m-carbs") || 0,
      fat: numOrNull("m-fat") || 0,
      meal_date: document.getElementById("m-date").value,
    });
    mealModal.hide();
    showToast("Meal logged");
    loadMeals();
  } catch (err) {
    showToast(err.message, "danger");
  }
  return false;
}

async function deleteMeal(id) {
  try {
    await Api.deleteMeal(id);
    loadMeals();
  } catch (err) {
    showToast(err.message, "danger");
  }
}

// --- Calculators ---
function showCalcTab(tab) {
  document.getElementById("calc-bmi").style.display = tab === "bmi" ? "block" : "none";
  document.getElementById("calc-calorie").style.display = tab === "calorie" ? "block" : "none";
  document.getElementById("tab-bmi").classList.toggle("active", tab === "bmi");
  document.getElementById("tab-calorie").classList.toggle("active", tab === "calorie");
}

async function handleBmi(e) {
  e.preventDefault();
  try {
    const result = await Api.bmi({
      weight: Number(document.getElementById("bmi-weight").value),
      height: Number(document.getElementById("bmi-height").value),
    });
    document.getElementById("bmi-result").innerHTML = `
      <div class="calc-result-hero" style="background:${result.category_color}1A;border:1px solid ${result.category_color}44">
        <div class="num" style="color:${result.category_color}">${result.bmi} <span style="font-size:16px;font-weight:600">— ${result.category}</span></div>
        <div class="desc">${result.recommendation}</div>
      </div>`;
  } catch (err) {
    showToast(err.message, "danger");
  }
  return false;
}

async function handleCalorie(e) {
  e.preventDefault();
  try {
    const result = await Api.calorie({
      age: Number(document.getElementById("cal-age").value),
      gender: document.getElementById("cal-gender").value,
      weight: Number(document.getElementById("cal-weight").value),
      height: Number(document.getElementById("cal-height").value),
      activity_level: document.getElementById("cal-activity").value,
      goal: document.getElementById("cal-goal").value,
    });
    document.getElementById("calorie-result").innerHTML = `
      <div class="calc-result-hero" style="background:#FF4E331A;border:1px solid #FF4E3344">
        <div class="num" style="color:var(--ember-dark)">${result.daily_calories} <span style="font-size:15px;font-weight:600">kcal/day</span></div>
        <div class="desc">${result.goal_description}</div>
        <div class="desc mt-2">BMR ${result.bmr} · TDEE ${result.tdee}</div>
        <div class="desc">Protein ${result.protein_grams}g · Carbs ${result.carbs_grams}g · Fat ${result.fat_grams}g</div>
      </div>`;
  } catch (err) {
    showToast(err.message, "danger");
  }
  return false;
}
