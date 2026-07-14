import { voteForRanking, ApiError } from "../api/client.js";

export function setVoteButtonsEnabled(container, enabled) {
  container.querySelectorAll(".btn-vote").forEach((button) => {
    button.disabled = !enabled;
    if (!enabled) {
      button.title = "Weekly vote limit reached";
    }
  });
}

export function bindVoting(container, onVoteComplete, onVoteBlocked) {
  container.addEventListener("click", async (event) => {
    const button = event.target.closest(".btn-vote");
    if (!button || button.disabled) return;

    const rankingId = button.dataset.rankingId;
    if (!rankingId) return;

    button.disabled = true;
    const originalText = button.textContent;
    button.textContent = "Voting...";

    try {
      await voteForRanking(rankingId);
      button.classList.add("voted");
      button.textContent = "Voted!";
      setVoteButtonsEnabled(container, false);
      if (onVoteComplete) {
        await onVoteComplete();
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 429) {
        button.textContent = "Limit reached";
        setVoteButtonsEnabled(container, false);
        if (onVoteBlocked) {
          onVoteBlocked(error.data || { message: error.message });
        }
        return;
      }

      button.textContent = "Error";
      console.error("Vote failed:", error);
      setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
      }, 1500);
      return;
    }

    setTimeout(() => {
      button.textContent = originalText;
      button.classList.remove("voted");
    }, 1200);
  });
}
