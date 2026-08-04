"use strict";

/* HelloGitHub 展示站前端逻辑：加载 data/issues.json，默认展示最新一期，
   按分类渲染项目卡片，支持期号切换与分类快速定位。 */

const state = {
  data: null,        // { updatedAt, issues: [...] }
  currentId: null,   // 当前期号
  activeCategory: null,
};

const els = {
  select: document.getElementById("issueSelect"),
  prev: document.getElementById("prevBtn"),
  next: document.getElementById("nextBtn"),
  catNav: document.getElementById("catNav"),
  issueHead: document.getElementById("issueHead"),
  content: document.getElementById("content"),
  updatedAt: document.getElementById("updatedAt"),
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

function currentIssue() {
  return state.data.issues.find((i) => i.id === state.currentId);
}

function totalProjects(issue) {
  return issue.categories.reduce((n, c) => n + c.projects.length, 0);
}

/* ---------- 期号选择 ---------- */

function fillIssueSelect() {
  els.select.textContent = "";
  const sorted = [...state.data.issues].sort((a, b) => b.id - a.id);
  for (const issue of sorted) {
    const opt = document.createElement("option");
    opt.value = String(issue.id);
    const latest = issue.id === state.data.issues[state.data.issues.length - 1].id;
    opt.textContent = latest ? "第 " + issue.id + " 期（最新）" : "第 " + issue.id + " 期";
    els.select.appendChild(opt);
  }
  els.select.value = String(state.currentId);
}

function updateNavButtons() {
  const ids = state.data.issues.map((i) => i.id);
  const idx = ids.indexOf(state.currentId);
  els.prev.disabled = idx <= 0;
  els.next.disabled = idx >= ids.length - 1;
}

function setIssue(id) {
  state.currentId = id;
  els.select.value = String(id);
  state.activeCategory = null;
  updateNavButtons();
  renderIssue();
}

/* ---------- 渲染 ---------- */

function renderIssue() {
  const issue = currentIssue();
  if (!issue) return;

  // 头部
  els.issueHead.textContent = "";
  const h = el("h2", null, issue.title);
  const meta = el("p", "meta", "共 " + totalProjects(issue) + " 个项目 · " +
    issue.categories.length + " 个分类");
  els.issueHead.appendChild(h);
  els.issueHead.appendChild(meta);

  // 分类导航
  renderCatNav(issue);

  // 内容
  els.content.textContent = "";
  for (const cat of issue.categories) {
    const section = el("section", "category-section");
    section.id = "cat-" + sanitizeId(cat.name);

    const h3 = el("h3", null, cat.name);
    const badge = el("span", "count", String(cat.projects.length));
    h3.appendChild(badge);

    const grid = el("div", "grid");
    for (const proj of cat.projects) {
      grid.appendChild(renderCard(proj));
    }
    section.appendChild(h3);
    section.appendChild(grid);
    els.content.appendChild(section);
  }
}

function sanitizeId(name) {
  return name.replace(/[^a-zA-Z0-9\u4e00-\u9fff_-]/g, "").slice(0, 60);
}

function renderCatNav(issue) {
  els.catNav.textContent = "";
  for (const cat of issue.categories) {
    const chip = el("button", "cat-chip", cat.name + " · " + cat.projects.length);
    chip.type = "button";
    chip.dataset.cat = cat.name;
    chip.addEventListener("click", () => {
      document.getElementById("cat-" + sanitizeId(cat.name)).scrollIntoView({ behavior: "smooth", block: "start" });
      setActiveChip(chip);
    });
    els.catNav.appendChild(chip);
  }
}

function setActiveChip(chip) {
  for (const c of els.catNav.children) c.classList.remove("active");
  if (chip) chip.classList.add("active");
}

function renderCard(proj) {
  const card = el("article", "card");

  const h4 = el("h4");
  const link = el("a", null, proj.name);
  link.href = proj.url;
  link.target = "_blank";
  link.rel = "noopener";
  h4.appendChild(link);

  const desc = el("p", "desc", proj.description || "（暂无简介）");

  const foot = el("div", "card-foot");
  const author = el("span", "author", proj.author ? "来自 @" + proj.author : "");
  const btn = el("a", "view-btn", "查看项目 ↗");
  btn.href = proj.url;
  btn.target = "_blank";
  btn.rel = "noopener";
  foot.appendChild(author);
  foot.appendChild(btn);

  card.appendChild(h4);
  card.appendChild(desc);
  card.appendChild(foot);
  return card;
}

/* ---------- 事件绑定 ---------- */

els.select.addEventListener("change", () => setIssue(Number(els.select.value)));
els.prev.addEventListener("click", () => {
  const ids = state.data.issues.map((i) => i.id);
  const idx = ids.indexOf(state.currentId);
  if (idx > 0) setIssue(ids[idx - 1]);
});
els.next.addEventListener("click", () => {
  const ids = state.data.issues.map((i) => i.id);
  const idx = ids.indexOf(state.currentId);
  if (idx >= 0 && idx < ids.length - 1) setIssue(ids[idx + 1]);
});

/* ---------- 启动 ---------- */

async function init() {
  try {
    const resp = await fetch("data/issues.json");
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    state.data = await resp.json();
  } catch (err) {
    els.content.textContent = "";
    const msg = el("p", "error",
      "数据加载失败：" + err.message + "。请通过本地服务器访问（如 python -m http.server）。");
    els.content.appendChild(msg);
    return;
  }

  if (!state.data.issues || state.data.issues.length === 0) {
    els.content.textContent = "";
    els.content.appendChild(el("p", "error", "数据为空，请先运行 python scripts/build_data.py。"));
    return;
  }

  state.currentId = state.data.issues[state.data.issues.length - 1].id;
  els.updatedAt.textContent = state.data.updatedAt || "未知";
  fillIssueSelect();
  setIssue(state.currentId);
}

init();