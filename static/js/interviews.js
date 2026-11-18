"use strict";
const interviews = document.getElementById("interviews");
document.getElementById("add-interview").addEventListener("click", () => {
  const row = document.getElementById("interview-template").content.cloneNode(true);
  interviews.appendChild(row);
  interviews.lastElementChild.querySelector("input").focus();
});
interviews.addEventListener("click", event => {
  if (event.target.classList.contains("remove-interview")) {
    event.target.closest(".interview-row").remove();
  }
});
