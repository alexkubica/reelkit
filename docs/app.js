"use strict";

const video = document.querySelector("#demo-video");
const fallback = document.querySelector("#video-fallback");
const source = video?.querySelector("source");
const playButton = document.querySelector("#play-with-sound");
const playLabel = document.querySelector("#play-with-sound-label");
const playbackStatus = document.querySelector("#demo-playback-status");
let mediaUnavailable = false;
let startingPlayback = false;

function setPlaybackStatus(message) {
  if (playbackStatus && playbackStatus.textContent !== message) {
    playbackStatus.textContent = message;
  }
}

function updatePlaybackControls() {
  if (!video || !playButton || !playLabel || mediaUnavailable) return;
  const playing = !video.paused && !video.ended;
  const audible = !video.muted && video.volume > 0;
  playButton.dataset.state = playing && audible ? "playing" : "paused";
  playButton.disabled = startingPlayback;

  if (video.ended) {
    playLabel.textContent = "Replay with sound";
    setPlaybackStatus("The end. Play it again?");
  } else if (playing) {
    playLabel.textContent = audible ? "Pause" : "Turn sound on";
    setPlaybackStatus(audible ? "Playing with sound." : "Playing muted. Turn sound on to hear the narration.");
  } else {
    playLabel.textContent = video.currentTime > 0 ? "Resume with sound" : "Play with sound";
    setPlaybackStatus(video.currentTime > 0 ? "Paused. Resume when you’re ready." : "Press play to hear the narration.");
  }
}

function showVideoFallback() {
  if (!video || !fallback) return;
  mediaUnavailable = true;
  video.hidden = true;
  fallback.hidden = false;
  if (playButton) playButton.hidden = true;
  setPlaybackStatus("The reel couldn’t load. Try the MP4 download below.");
}

video?.addEventListener("error", showVideoFallback);
source?.addEventListener("error", showVideoFallback);

if (video && playButton) {
  playButton.hidden = false;
  playButton.addEventListener("click", async () => {
    if (mediaUnavailable || startingPlayback) return;
    if (!video.paused && !video.ended && !video.muted && video.volume > 0) {
      video.pause();
      return;
    }

    if (video.ended) video.currentTime = 0;
    video.muted = false;
    if (video.volume === 0) video.volume = 1;
    startingPlayback = true;
    playButton.disabled = true;
    setPlaybackStatus("Starting the reel…");
    try {
      // This runs only after an explicit click, preserving audible playback permissions.
      await video.play();
      startingPlayback = false;
      updatePlaybackControls();
    } catch (error) {
      startingPlayback = false;
      playButton.disabled = false;
      if (error.name === "AbortError") {
        updatePlaybackControls();
      } else if (video.error) {
        showVideoFallback();
      } else {
        setPlaybackStatus("Playback couldn’t start. Try the Play button in the player.");
      }
    }
  });

  ["play", "pause", "ended", "volumechange", "seeked"].forEach((event) => {
    video.addEventListener(event, updatePlaybackControls);
  });
  video.addEventListener("waiting", () => {
    if (!video.paused) setPlaybackStatus("Loading the reel…");
  });
  video.addEventListener("playing", updatePlaybackControls);
  video.querySelector("track")?.addEventListener("error", () => {
    setPlaybackStatus("English captions couldn’t load. Hebrew narration is still available.");
  });
  updatePlaybackControls();
  if (video.error) showVideoFallback();
}

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
