const runsNode = document.querySelector("#runs");
const detailsNode = document.querySelector("#details");
const comparisonNode = document.querySelector("#comparison");

function card(run) {
  const node = document.createElement("article");
  node.className = "run-card";
  node.innerHTML = `
    <div class="muted">${run.status}</div>
    <h3>${run.name}</h3>
    <div class="metric">${Math.round((run.metrics.accuracy || 0) * 100)}%</div>
    <p>${run.dataset}</p>
  `;
  node.addEventListener("click", async () => {
    const response = await fetch(`/api/runs/${run.id}`);
    detailsNode.textContent = JSON.stringify((await response.json()).run, null, 2);
  });
  return node;
}

async function boot() {
  const response = await fetch("/api/runs");
  const { runs } = await response.json();
  runs.forEach((run) => runsNode.appendChild(card(run)));

  const compare = await fetch(`/api/compare?left=${runs[0].id}&right=${runs[1].id}`);
  const result = await compare.json();
  comparisonNode.textContent = `${result.right.name} is ${Math.round(result.metric_deltas.accuracy * 1000) / 10} points more accurate.`;
}

boot();
