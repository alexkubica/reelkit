"use strict";

const cards = [...document.querySelectorAll(".reel-card")];
const videos = cards.map((card) => card.querySelector("video"));
const filters = document.querySelector("#library-filters");
const count = document.querySelector("#library-count");

filters?.removeAttribute("hidden");
filters?.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-category]");
  if (!button) return;
  const category = button.dataset.category;
  filters.querySelectorAll("button").forEach((item) => {
    item.setAttribute("aria-pressed", String(item === button));
  });
  let visible = 0;
  cards.forEach((card) => {
    const hide = category !== "all" && card.dataset.category !== category;
    if (hide) card.querySelector("video")?.pause();
    card.hidden = hide;
    if (!hide) visible += 1;
  });
  if (count) count.textContent = `${visible} ${visible === 1 ? "story" : "stories"}${category === "all" ? " to get lost in" : ` · ${category}`}`;
});

videos.forEach((video) => {
  if (!video) return;
  video.addEventListener("play", () => {
    videos.forEach((other) => { if (other !== video) other?.pause(); });
  });
  const showError = () => {
    const message = video.closest(".reel-card").querySelector(".reel-card-error");
    if (message) message.hidden = false;
  };
  video.addEventListener("error", showError);
  video.querySelector("source")?.addEventListener("error", showError);
  if (video.error) showError();
});
