const form = document.querySelector("#chat-form");
const input = document.querySelector("#question");
const messages = document.querySelector("#messages");
const suggestionButtons = document.querySelectorAll("[data-question]");

function addMessage(text, sender, meta = "") {
  const article = document.createElement("article");
  article.className = `message ${sender}`;

  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.appendChild(paragraph);

  if (meta) {
    const small = document.createElement("small");
    small.textContent = meta;
    article.appendChild(small);
  }

  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

async function askQuestion(question) {
  addMessage(question, "user");
  input.value = "";
  input.disabled = true;

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const result = await response.json();
    const confidence = Math.round((result.confidence || 0) * 100);
    const matched = result.matched_question ? `Matched: ${result.matched_question} (${confidence}%)` : "";
    addMessage(result.answer, "bot", matched);
  } catch (error) {
    addMessage("The chatbot is unavailable. Please check that the Flask server is running.", "bot");
  } finally {
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (question) {
    askQuestion(question);
  }
});

suggestionButtons.forEach((button) => {
  button.addEventListener("click", () => askQuestion(button.dataset.question));
});
