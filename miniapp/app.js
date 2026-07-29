// ===== Telegram WebApp init =====
const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

const USER_ID = String(
  tg?.initDataUnsafe?.user?.id || "test_" + Math.floor(Math.random() * 1000000)
);

// ===== Screens =====
const screens = {
  intro: document.getElementById("screen-intro"),
  test: document.getElementById("screen-test"),
  loading: document.getElementById("screen-loading"),
  result: document.getElementById("screen-result"),
};
function showScreen(name) {
  Object.values(screens).forEach((s) => s.classList.remove("active"));
  screens[name].classList.add("active");
}

// ===== Elements =====
const btnStart = document.getElementById("btn-start");
const btnListen = document.getElementById("btn-listen");
const btnRecord = document.getElementById("btn-record");
const btnNext = document.getElementById("btn-next");
const btnRestart = document.getElementById("btn-restart");

const partLabel = document.getElementById("part-label");
const stepLabel = document.getElementById("step-label");
const progressFill = document.getElementById("progress-fill");
const questionText = document.getElementById("question-text");
const feedbackCard = document.getElementById("feedback-card");
const recStatus = document.getElementById("rec-status");
const recTimer = document.getElementById("rec-timer");
const loadingText = document.getElementById("loading-text");

const PART_NAMES = { part1: "PART 1", part2: "PART 2", part3: "PART 3" };

// ===== State =====
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let recSeconds = 0;
let recTimerHandle = null;
let currentAudioEl = null;

// ===== Intro -> Start test =====
btnStart.addEventListener("click", async () => {
  btnStart.disabled = true;
  btnStart.textContent = "Yuklanmoqda…";
  try {
    const form = new FormData();
    form.append("user_id", USER_ID);
    const res = await fetch("/api/mock/start", { method: "POST", body: form });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    renderQuestion(data);
    showScreen("test");
  } catch (err) {
    alert("Boshlashda xatolik: " + err.message + "\nQaytadan urinib ko'ring.");
    btnStart.disabled = false;
    btnStart.textContent = "Testni boshlash";
  }
});

function renderQuestion(data) {
  partLabel.textContent = PART_NAMES[data.part] || data.part;
  stepLabel.textContent = `${data.step + 1} / ${data.total}`;
  progressFill.style.width = `${((data.step) / data.total) * 100}%`;
  questionText.textContent = data.question || data.next_question;
  feedbackCard.classList.add("hidden");
  recStatus.textContent = "Javob berishga tayyor bo'lganingizda bosing";
  recTimer.textContent = "00:00";
}

// ===== Listen to question (TTS) =====
btnListen.addEventListener("click", async () => {
  btnListen.disabled = true;
  btnListen.textContent = "⏳ Tayyorlanmoqda…";
  try {
    const form = new FormData();
    form.append("text", questionText.textContent);
    const res = await fetch("/api/tts", { method: "POST", body: form });
    if (!res.ok) throw new Error("audio olishda xatolik");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    if (currentAudioEl) currentAudioEl.pause();
    currentAudioEl = new Audio(url);
    currentAudioEl.play();
  } catch (err) {
    console.error(err);
  } finally {
    btnListen.disabled = false;
    btnListen.textContent = "🔊 Savolni tinglash";
  }
});

// ===== Recording =====
btnRecord.addEventListener("click", async () => {
  if (!isRecording) {
    await startRecording();
  } else {
    stopRecording();
  }
});

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.onstop = onRecordingStop;
    mediaRecorder.start();

    isRecording = true;
    btnRecord.classList.add("recording");
    recStatus.textContent = "Yozilmoqda… tugatish uchun bosing";
    recSeconds = 0;
    recTimer.textContent = "00:00";
    recTimerHandle = setInterval(() => {
      recSeconds += 1;
      const m = String(Math.floor(recSeconds / 60)).padStart(2, "0");
      const s = String(recSeconds % 60).padStart(2, "0");
      recTimer.textContent = `${m}:${s}`;
      // Xavfsizlik uchun 3 daqiqadan keyin avtomatik to'xtatish
      if (recSeconds >= 180) stopRecording();
    }, 1000);
  } catch (err) {
    alert("Mikrofonga ruxsat berilmadi. Iltimos, brauzer sozlamalaridan ruxsat bering.");
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach((t) => t.stop());
  }
  isRecording = false;
  btnRecord.classList.remove("recording");
  clearInterval(recTimerHandle);
}

async function onRecordingStop() {
  const blob = new Blob(audioChunks, { type: "audio/webm" });
  showScreen("loading");
  loadingText.textContent = "Javobingiz tahlil qilinmoqda…";

  try {
    const form = new FormData();
    form.append("user_id", USER_ID);
    form.append("audio", blob, "answer.webm");
    const res = await fetch("/api/mock/answer", { method: "POST", body: form });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    if (data.finished) {
      renderResult(data.final_report);
      showScreen("result");
    } else {
      showScreen("test");
      renderFeedback(data.evaluation);
      // Keyingi savol ma'lumotini "Keyingi savol" tugmasi uchun saqlab qo'yamiz
      btnNext.dataset.next = JSON.stringify({
        question: data.next_question,
        part: data.part,
        step: data.step,
        total: data.total,
      });
    }
  } catch (err) {
    showScreen("test");
    alert("Xatolik yuz berdi: " + err.message);
  }
}

function renderFeedback(ev) {
  document.getElementById("fb-band").textContent = ev.band_estimate || "—";
  document.getElementById("fb-strengths").textContent = ev.strengths || "—";
  document.getElementById("fb-errors").textContent = ev.errors || "—";
  document.getElementById("fb-improved").textContent = ev.improved_version || "—";
  document.getElementById("fb-tip").textContent = ev.tip || "—";
  feedbackCard.classList.remove("hidden");
  recStatus.textContent = "Tayyor bo'lsangiz keyingi savolga o'ting";
}

btnNext.addEventListener("click", () => {
  const next = JSON.parse(btnNext.dataset.next || "{}");
  renderQuestion({
    question: next.question,
    next_question: next.question,
    part: next.part,
    step: next.step,
    total: next.total,
  });
});

// ===== Result screen =====
function renderResult(report) {
  if (!report) {
    document.getElementById("result-band-num").textContent = "N/A";
    return;
  }
  document.getElementById("result-band-num").textContent = report.overall_band || "—";
  document.getElementById("res-fluency").textContent = report.fluency_coherence || "—";
  document.getElementById("res-lexical").textContent = report.lexical_resource || "—";
  document.getElementById("res-grammar").textContent = report.grammar_range_accuracy || "—";
  document.getElementById("res-pron").textContent = report.pronunciation_note || "—";

  const adviceList = document.getElementById("res-advice");
  adviceList.innerHTML = "";
  (report.top_advice || []).forEach((a) => {
    const li = document.createElement("li");
    li.textContent = a;
    adviceList.appendChild(li);
  });
}

btnRestart.addEventListener("click", () => {
  btnStart.disabled = false;
  btnStart.textContent = "Testni boshlash";
  showScreen("intro");
});
