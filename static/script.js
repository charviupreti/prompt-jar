const form = document.getElementById("prompt-form");
const emptyState = document.getElementById("empty-state");
const resultCard = document.getElementById("result-card");
const resultPrompt = document.getElementById("result-prompt");
const saveBtn = document.getElementById("save-btn");
const savedPrompts = document.getElementById("saved-prompts");

let latestPrompt = null;

function readFormData(intensityOverride = null) {
  const data = new FormData(form);
  return {
    what: data.get("what") || "Surprise me",
    topic: data.get("topic") || "Surprise me",
    colors: data.get("colors") || "Surprise me",
    supplies: data.get("supplies") || "Surprise me",
    time: data.get("time") || "30 minutes",
    intensity: intensityOverride || "default",
  };
}

function renderPrompt(prompt) {
  latestPrompt = { prompt: prompt.prompt };
  emptyState.classList.add("hidden");
  resultCard.classList.remove("hidden");
  resultPrompt.textContent = prompt.prompt;
}

async function generatePrompt(intensity = "default") {
  const body = readFormData(intensity);

  const response = await fetch("/api/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error("Could not generate a idea right now.");
  }

  const prompt = await response.json();
  renderPrompt(prompt);
}

async function savePrompt() {
  if (!latestPrompt) {
    return;
  }

  const response = await fetch("/api/prompts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(latestPrompt),
  });

  if (!response.ok) {
    throw new Error("Could not save this prompt.");
  }

  await loadSavedPrompts();
}

async function loadSavedPrompts() {
  const response = await fetch("/api/prompts");
  const prompts = await response.json();

  savedPrompts.innerHTML = "";
  if (!Array.isArray(prompts) || prompts.length === 0) {
    savedPrompts.innerHTML =
      "<p>No saved prompts yet. Make a few and your jar will fill up.</p>";
    return;
  }

  prompts.slice(0, 6).forEach((prompt) => {
    const item = document.createElement("article");
    item.className = "saved-item";
    const text = document.createElement("p");
    text.textContent = prompt.prompt;
    const openButton = document.createElement("button");
    openButton.type = "button";
    openButton.className = "open-btn";
    openButton.textContent = "Open";
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "delete-btn";
    deleteButton.textContent = "Delete";
    item.append(text, openButton, deleteButton);
    openButton.addEventListener("click", () => {
      renderPrompt(prompt);
      resultCard.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    deleteButton.addEventListener("click", async () => {
      if (!prompt.id) return;
      await fetch("/api/prompts", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: prompt.id }),
      });
      await loadSavedPrompts();
    });
    savedPrompts.appendChild(item);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await generatePrompt("default");
  } catch (error) {
    console.error(error);
  }
});

document.getElementById("reroll-btn").addEventListener("click", async () => {
  try {
    await generatePrompt("default");
  } catch (error) {
    console.error(error);
  }
});

document.getElementById("easier-btn").addEventListener("click", async () => {
  try {
    await generatePrompt("easier");
  } catch (error) {
    console.error(error);
  }
});

document.getElementById("weirder-btn").addEventListener("click", async () => {
  try {
    await generatePrompt("weirder");
  } catch (error) {
    console.error(error);
  }
});

saveBtn.addEventListener("click", async () => {
  try {
    await savePrompt();
    saveBtn.textContent = "💾 Saved!";
    setTimeout(() => {
      saveBtn.textContent = "💾 Save it";
    }, 1100);
  } catch (error) {
    console.error(error);
  }
});

loadSavedPrompts();
