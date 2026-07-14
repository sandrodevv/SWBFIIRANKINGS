export function clearElement(element) {
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
}

export function showLoading(container, message = "Loading...") {
  clearElement(container);
  const loading = document.createElement("div");
  loading.className = "loading";
  loading.textContent = message;
  container.appendChild(loading);
}

export function showError(container, message) {
  clearElement(container);
  const error = document.createElement("div");
  error.className = "error-message";
  error.textContent = message;
  container.appendChild(error);
}

export function createElement(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text) el.textContent = text;
  return el;
}
