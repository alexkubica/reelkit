"use strict";

const video = document.querySelector("#demo-video");
const fallback = document.querySelector("#video-fallback");
const source = video?.querySelector("source");
function showVideoFallback() {
  if (!video || !fallback) return;
  video.hidden = true;
  fallback.hidden = false;
}

video?.addEventListener("error", showVideoFallback);
source?.addEventListener("error", showVideoFallback);
if (video?.error) showVideoFallback();

const slider = document.querySelector("#scene-time");
const output = document.querySelector("#time-output");
const marker = document.querySelector("#scene-marker");
const caption = document.querySelector("#scene-caption");
const playhead = document.querySelector("#track-playhead");
const captionLines = [
  ["A chatbot can answer.", "An agent can act."],
  ["Give it a goal.", "Let it get to work."],
  ["A plan. The right tools.", "One step at a time."],
  ["Less busywork.", "More done."],
];

function updateScene() {
  if (!slider || !output || !marker || !caption || !playhead) return;
  const time = Number(slider.value);
  const lines = captionLines[Math.min(Math.floor(time / 2), captionLines.length - 1)];
  output.value = `${time.toFixed(1)}s`;
  marker.textContent = time.toFixed(1).padStart(4, "0");
  caption.children[0].textContent = lines[0];
  caption.children[1].textContent = lines[1];
  playhead.style.left = `${(time / 8) * 100}%`;
}

slider?.addEventListener("input", updateScene);
updateScene();

const copyButton = document.querySelector("#copy-command");
const copyStatus = document.querySelector("#copy-status");
const commands = document.querySelector("#quickstart-commands");

copyButton?.addEventListener("click", async () => {
  if (!commands) return;
  try {
    await navigator.clipboard.writeText(commands.textContent);
    copyButton.textContent = "Copied ✓";
    if (copyStatus) copyStatus.textContent = "Quickstart commands copied to clipboard.";
    window.setTimeout(() => { copyButton.textContent = "Copy ⧉"; }, 2200);
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(commands);
    selection?.removeAllRanges();
    selection?.addRange(range);
    copyButton.textContent = "Select + copy";
    if (copyStatus) copyStatus.textContent = "Commands selected. Use your device’s copy command.";
  }
});
