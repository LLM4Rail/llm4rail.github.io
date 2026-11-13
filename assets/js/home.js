(function () {
  "use strict";
  var I = window.LLM4RAIL_I18N, T = I.t;
  var data = (window.LLM4RAIL_DATA && window.LLM4RAIL_DATA.instances) || [];
  var fmtInt = function (n) { return Math.round(n).toLocaleString("en-US"); };
  var fmtPct = function (g, d) { return (g * 100).toFixed(d == null ? 1 : d) + "%"; };
  var NS = "http://www.w3.org/2000/svg";
  var state = { lib: "PESPlib", view: "chart" };

  function el(tag, attrs, text) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function rowsFor(lib) {
    return data.filter(function (d) { return d.library === lib && d.status === "open" && d.gap != null; });
  }

  var host = document.getElementById("gap-chart");
  var tableBox = document.getElementById("gap-table");
  var tip = document.createElement("div");
  tip.className = "tip";
  tip.setAttribute("role", "status");

  function draw() {
    if (!host) return;
    var rows = rowsFor(state.lib);
    host.innerHTML = "";
    host.appendChild(tip);
    var W = Math.max(320, host.clientWidth);
    var narrow = W < 560, left = narrow ? 128 : 150, right = narrow ? 44 : 60, top = 28, rowH = 22, barH = 12, grpH = 30;
    var maxGap = Math.max.apply(null, rows.map(function (r) { return r.gap; }));
    var step = maxGap > 0.2 ? 0.1 : 0.01;
    var xMax = Math.ceil((maxGap + 1e-9) / step) * step;
    var plotW = W - left - right;
    var X = function (v) { return left + (v / xMax) * plotW; };
    var groups = T.chartGroups[state.lib];

    var layout = [], y = top;
    groups.forEach(function (key) {
      var items = rows.filter(function (r) { return r.set === key; });
      if (!items.length) return;
      layout.push({ type: "group", label: T.set[key], y: y + 18 });
      y += grpH;
      items.forEach(function (r) { layout.push({ type: "row", r: r, y: y }); y += rowH; });
      y += 6;
    });
    var H = y + 8;
    var svg = el("svg", { viewBox: "0 0 " + W + " " + H, width: W, height: H, "aria-hidden": "true" });
    var gg = el("g", {});
    var nTicks = Math.round(xMax / step);
    for (var i = 0; i <= nTicks; i++) {
      var t = i * step, x = X(t);
      gg.appendChild(el("line", { class: "grid", x1: x, x2: x, y1: top - 6, y2: H - 6 }));
      var every = plotW / nTicks < 40 ? 2 : 1;
      if (i % every === 0) gg.appendChild(el("text", { x: x, y: top - 12, "text-anchor": "middle" }, Math.round(t * 100) + "%"));
    }
    svg.appendChild(gg);

    var maxR = rows.reduce(function (a, b) { return b.gap > a.gap ? b : a; }, rows[0]);
    var minR = rows.reduce(function (a, b) { return b.gap < a.gap ? b : a; }, rows[0]);
    var dec = step < 0.1 ? 2 : 1;

    layout.forEach(function (item) {
      if (item.type === "group") { svg.appendChild(el("text", { class: "grp", x: 0, y: item.y }, item.label)); return; }
      var r = item.r, cy = item.y + rowH / 2;
      var g = el("g", { class: "row", tabindex: "0" });
      var w = Math.max(2, X(r.gap) - X(0)), x0 = X(0), y0 = cy - barH / 2, rad = Math.min(4, w / 2);
      var d = "M" + x0 + " " + y0 + "H" + (x0 + w - rad) + "Q" + (x0 + w) + " " + y0 + " " + (x0 + w) + " " + (y0 + rad) +
              "V" + (y0 + barH - rad) + "Q" + (x0 + w) + " " + (y0 + barH) + " " + (x0 + w - rad) + " " + (y0 + barH) + "H" + x0 + "Z";
      g.appendChild(el("rect", { x: 0, y: item.y, width: W, height: rowH, fill: "transparent" }));
      g.appendChild(el("path", { class: "bar", d: d }));
      g.appendChild(el("text", { class: "ylab", x: left - 8, y: cy + 4, "text-anchor": "end", style: narrow ? "font-size:11px" : "" }, r.instance));
      if (r === maxR || r === minR) g.appendChild(el("text", { class: "val", x: x0 + w + 6, y: cy + 4 }, fmtPct(r.gap, dec)));
      var show = function (evt) {
        tip.innerHTML = "<b>" + esc(r.instance) + "</b> · " + esc(T.set[r.set]) + "<br>" +
          "<span class='k'>" + T.tip.best + "</span> " + fmtInt(r.best_known) + "<br>" +
          "<span class='k'>" + T.tip.bound + "</span> " + fmtInt(r.best_bound) + "<br>" +
          "<span class='k'>" + T.tip.gap + "</span> " + fmtPct(r.gap, dec) + "<br>" +
          "<span class='k'>" + T.tip.record + "</span> " + esc(r.record);
        var box = host.getBoundingClientRect();
        var px = evt && evt.clientX ? evt.clientX - box.left : x0 + w;
        tip.style.left = Math.min(Math.max(8, px + 14), box.width - tip.offsetWidth - 8) + "px";
        tip.style.top = (item.y + rowH + 6) + "px";
        tip.classList.add("on");
      };
      var hide = function () { tip.classList.remove("on"); };
      g.addEventListener("mousemove", show);
      g.addEventListener("mouseleave", hide);
      g.addEventListener("focus", function () { show(null); });
      g.addEventListener("blur", hide);
      svg.appendChild(g);
    });
    host.insertBefore(svg, tip);
  }

  function table() {
    if (!tableBox) return;
    var rows = rowsFor(state.lib), dec = state.lib === "TimPassLib" ? 2 : 1;
    var h = "<table><thead><tr><th>" + T.th[0] + "</th><th>" + T.th[2] + "</th><th class='num'>" + T.th[4] + "</th><th class='num'>" +
            T.th[5] + "</th><th class='num'>" + T.th[6] + "</th><th>" + T.th[8] + "</th></tr></thead><tbody>";
    rows.forEach(function (r) {
      h += "<tr><td class='mono'>" + esc(r.instance) + "</td><td class='nw'>" + esc(T.set[r.set]) + "</td><td class='num'>" + fmtInt(r.best_known) +
           "</td><td class='num'>" + fmtInt(r.best_bound) + "</td><td class='num'>" + fmtPct(r.gap, dec) + "</td><td>" + esc(r.record) + "</td></tr>";
    });
    tableBox.innerHTML = h + "</tbody></table>";
  }

  function press(group, value) {
    document.querySelectorAll("[data-" + group + "]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-" + group) === value));
    });
  }
  function apply() {
    press("lib", state.lib); press("view", state.view);
    var isChart = state.view === "chart";
    host.hidden = !isChart; tableBox.hidden = isChart;
    document.querySelectorAll("[data-src]").forEach(function (s) { s.hidden = s.getAttribute("data-src") !== state.lib; });
    var leg = document.getElementById("gap-legend"); if (leg) leg.hidden = state.lib !== "PESPlib";
    if (isChart) draw(); else table();
  }
  document.querySelectorAll("[data-lib]").forEach(function (b) { b.addEventListener("click", function () { state.lib = b.getAttribute("data-lib"); apply(); }); });
  document.querySelectorAll("[data-view]").forEach(function (b) { b.addEventListener("click", function () { state.view = b.getAttribute("data-view"); apply(); }); });

  var copy = document.getElementById("copy-bib");
  if (copy) {
    var label = copy.textContent;
    copy.addEventListener("click", function () {
      var text = document.getElementById("bibtex").textContent;
      var ok = copy.getAttribute("data-ok"), fail = copy.getAttribute("data-fail");
      var done = function () { copy.textContent = ok; setTimeout(function () { copy.textContent = label; }, 1600); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, function () { copy.textContent = fail; });
      else copy.textContent = fail;
    });
  }

  if (host) {
    apply();
    var tm;
    window.addEventListener("resize", function () { clearTimeout(tm); tm = setTimeout(function () { if (state.view === "chart") draw(); }, 120); });
  }
})();
