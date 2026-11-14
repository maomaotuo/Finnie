const MIME_TYPES = ["audio/webm;codecs=opus", "audio/mp4", "audio/ogg;codecs=opus"];
const MAX_BYTES = 25_000_000;
const composers = new WeakMap();

export default function render(component) {
  const { parentElement, data, setTriggerValue } = component;
  const form = parentElement.querySelector("form");
  const input = form.querySelector("textarea");
  const mic = form.querySelector(".microphone");
  const send = form.querySelector(".send");
  const status = parentElement.querySelector(".status");

  // Keep the typed draft across Streamlit reruns, including an API error.
  const previous = composers.get(form) || {};
  let lastResult = previous.lastResult;
  if (data.result && data.result.id !== lastResult) {
    lastResult = data.result.id;
    status.textContent = data.result.error || "Review your transcript, then send.";
    if (data.result.text) input.value = data.result.text;
    input.focus();
  }
  composers.set(form, { lastResult });

  let phase = "idle";
  let active = true;
  let recorder;
  let stream;
  let reader;
  let chunks = [];
  let recordedBytes = 0;

  function releaseMicrophone() {
    stream?.getTracks().forEach(track => track.stop());
    stream = undefined;
  }

  function updateControls() {
    const recording = phase === "recording";
    input.readOnly = phase !== "idle";
    send.disabled = phase !== "idle" || !input.value.trim();
    mic.disabled = !["idle", "recording"].includes(phase);
    mic.classList.toggle("recording", recording);
    mic.querySelector(".mic-icon").hidden = recording;
    mic.querySelector(".stop-icon").hidden = !recording;
    const label = recording ? "Stop recording" : "Record voice question";
    mic.setAttribute("aria-label", label);
    mic.title = label;
  }

  function setPhase(next, message) {
    phase = next;
    status.textContent = message;
    updateControls();
  }

  function stopRecording() {
    setPhase("processing", "Transcribing…");
    recorder.stop();
    releaseMicrophone();
  }

  function sendRecording() {
    if (!active || phase !== "processing") return;
    if (!recordedBytes || recordedBytes > MAX_BYTES) {
      setPhase("idle", "Record a question with audio under 25 MB.");
      return;
    }
    reader = new FileReader();
    reader.onerror = () => setPhase("idle", "Couldn't read the recording. Try again.");
    reader.onload = () => {
      const audio = reader.result.split(",", 2)[1];
      setTriggerValue("recording", { audio, mime: recorder.mimeType });
    };
    reader.readAsDataURL(new Blob(chunks, { type: recorder.mimeType }));
  }

  mic.onclick = async () => {
    if (phase === "recording") {
      stopRecording();
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setPhase("idle", "Microphone recording is unavailable in this browser. You can type your question.");
      return;
    }
    setPhase("starting", "Opening microphone…");
    try {
      const captured = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!active) {
        captured.getTracks().forEach(track => track.stop());
        return;
      }
      stream = captured;
      const mimeType = MIME_TYPES.find(type => MediaRecorder.isTypeSupported(type));
      recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunks = [];
      recordedBytes = 0;
      recorder.ondataavailable = ({ data: chunk }) => {
        recordedBytes += chunk.size;
        if (recordedBytes <= MAX_BYTES) chunks.push(chunk);
        if (recordedBytes > MAX_BYTES && phase === "recording") stopRecording();
      };
      recorder.onstop = sendRecording;
      recorder.onerror = () => {
        releaseMicrophone();
        setPhase("idle", "Recording failed. Try again.");
      };
      recorder.start(1000);
      setPhase("recording", "Recording… Select the square to stop and transcribe.");
    } catch {
      releaseMicrophone();
      setPhase("idle", "Couldn't start the microphone. Check your browser permissions.");
    }
  };

  form.onsubmit = event => {
    event.preventDefault();
    const question = input.value.trim();
    if (phase !== "idle" || !question) return;
    input.value = "";
    setPhase("sending", "");
    setTriggerValue("question", question);
  };
  input.oninput = updateControls;
  input.onkeydown = event => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      form.requestSubmit();
    }
  };
  updateControls();

  return () => {
    active = false;
    if (reader?.readyState === FileReader.LOADING) reader.abort();
    if (recorder?.state === "recording") recorder.stop();
    releaseMicrophone();
    if (phase === "recording" || phase === "starting") status.textContent = "";
  };
}
