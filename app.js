"use strict";

/* HelloGitHub · 开源观测站 前端逻辑
   加载 data/issues.json，默认展示最新一期，
   按分类渲染项目卡片，支持期号切换、分类快速定位、入场动画与统计。 */

document.documentElement.classList.add("js");

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

function setText(id, text) {
  const node = document.getElementById(id);
  if (node) node.textContent = text;
}

function pad(n, width) {
  const s = String(n);
  return s.length >= width ? s : ("000" + s).slice(-width);
}

function currentIssue() {
  return state.data.issues.find((i) => i.id === state.currentId);
}

function totalProjects(issue) {
  return issue.categories.reduce((n, c) => n + c.projects.length, 0);
}

/* ---------- 入场动画 ---------- */

const revealObserver = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (entry.isIntersecting) {
      entry.target.classList.add("is-in");
      revealObserver.unobserve(entry.target);
    }
  }
}, { threshold: 0.1, rootMargin: "0px 0px -36px 0px" });

function observeReveals() {
  const nodes = document.querySelectorAll(".reveal:not(.is-in)");
  for (const n of nodes) revealObserver.observe(n);
}

function revealHero() {
  const nodes = document.querySelectorAll(".hero .reveal");
  for (const n of nodes) {
    n.style.setProperty("--d", String(Number(n.dataset.r || 0)));
    n.classList.add("is-in");
  }
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
  const label = el("p", "issue-label", "ISSUE / " + pad(issue.id, 3));
  const h = el("h2", null, issue.title);
  const meta = el("p", "meta", "共 " + totalProjects(issue) + " 个项目 · " +
    issue.categories.length + " 个分类");
  els.issueHead.appendChild(label);
  els.issueHead.appendChild(h);
  els.issueHead.appendChild(meta);

  // 分类导航
  renderCatNav(issue);

  // 内容
  els.content.textContent = "";
  let seq = 0;
  for (const cat of issue.categories) {
    seq += 1;
    const section = el("section", "category-section");
    section.id = "cat-" + sanitizeId(cat.name);

    const head = el("div", "category-head");
    const secNo = el("span", "sec-no", "SEC " + pad(seq, 2));
    const h3 = el("h3", null, cat.name);
    const badge = el("span", "count", cat.projects.length + " 个项目");
    head.appendChild(secNo);
    head.appendChild(h3);
    head.appendChild(badge);

    const grid = el("div", "grid");
    cat.projects.forEach((proj, i) => {
      grid.appendChild(renderCard(proj, issue.id, i + 1));
    });
    section.appendChild(head);
    section.appendChild(grid);
    els.content.appendChild(section);
  }
  observeReveals();
}

function hideLoading() {
  const loading = document.getElementById("loading");
  if (loading && loading.parentNode) loading.parentNode.removeChild(loading);
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
      const target = document.getElementById("cat-" + sanitizeId(cat.name));
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      setActiveChip(chip);
    });
    els.catNav.appendChild(chip);
  }
}

function setActiveChip(chip) {
  for (const c of els.catNav.children) c.classList.remove("active");
  if (chip) chip.classList.add("active");
}

function renderCard(proj, issueId, index) {
  const card = el("article", "card reveal");
  card.style.setProperty("--d", String(Math.min((index - 1) % 8, 7)));

  const idx = el("div", "card-index", "#" + issueId + "." + pad(index, 3));
  card.appendChild(idx);

  const h4 = el("h4");
  const link = el("a", null, proj.name);
  link.href = proj.url;
  link.target = "_blank";
  link.rel = "noopener";
  h4.appendChild(link);

  const desc = el("p", "desc", proj.description || "（暂无简介）");

  const foot = el("div", "card-foot");
  const author = el("span", "author", proj.author ? "来自 @" + proj.author : "");
  const btn = el("a", "view-btn", "");
  btn.href = proj.url;
  btn.target = "_blank";
  btn.rel = "noopener";
  btn.appendChild(document.createTextNode("查看项目 "));
  const arr = el("span", "arr", "→");
  btn.appendChild(arr);

  foot.appendChild(author);
  foot.appendChild(btn);

  card.appendChild(idx);
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

/* ---------- Hero 统计 ---------- */

function fillHeroStats() {
  const issues = state.data.issues;
  if (!issues || issues.length === 0) return;
  const total = issues.reduce((n, i) => n + totalProjects(i), 0);
  const catSet = new Set();
  for (const issue of issues) {
    for (const cat of issue.categories) catSet.add(cat.name);
  }
  setText("statIssues", String(issues.length));
  setText("statProjects", total.toLocaleString("en-US"));
  setText("statCats", String(catSet.size));
  setText("statUpdated", state.data.updatedAt || "未知");
}

/* ---------- 启动 ---------- */

async function init() {
  revealHero();

  try {
    const resp = await fetch("data/issues.json");
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    state.data = await resp.json();
  } catch (err) {
    hideLoading();
    const msg = el("p", "error",
      "数据加载失败：" + err.message + "。请通过本地服务器访问（如 python -m http.server）。");
    els.content.appendChild(msg);
    return;
  }

  if (!state.data.issues || state.data.issues.length === 0) {
    hideLoading();
    els.content.appendChild(el("p", "error", "数据为空，请先运行 python scripts/build_data.py。"));
    return;
  }

  state.currentId = state.data.issues[state.data.issues.length - 1].id;
  els.updatedAt.textContent = state.data.updatedAt || "未知";
  fillHeroStats();
  fillIssueSelect();
  hideLoading();
  setIssue(state.currentId);
}

init();
