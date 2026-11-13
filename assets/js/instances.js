(function () {
  "use strict";
  var T = window.LLM4RAIL_I18N.t;
  var all = (window.LLM4RAIL_DATA && window.LLM4RAIL_DATA.instances) || [];
  var q = document.getElementById("q"), lib = document.getElementById("lib"), set = document.getElementById("set"), st = document.getElementById("status");
  var body = document.getElementById("rows"), count = document.getElementById("count");
  var libs = ["PESPlib", "TimPassLib", "DISPLIB", "MIPLIB 2017"];

  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function num(n) {
    if (n == null || n === "") return "–";
    return Number.isInteger(n) ? n.toLocaleString("en-US") : n.toLocaleString("en-US", { maximumFractionDigits: 2 });
  }
  function opt(value, label) { var o = document.createElement("option"); o.value = value; o.textContent = label; return o; }
  function recordLink(label, record, source, evidence) {
    return esc(label) + " · <a href='" + esc(source) + "' title='" + esc(T.evidence[evidence]) + "'>" + esc(record) + "</a>";
  }

  lib.appendChild(opt("", T.allLibs)); libs.forEach(function (l) { lib.appendChild(opt(l, l)); });
  st.appendChild(opt("", T.allStatus)); ["open", "optimal", "no_bound"].forEach(function (s) { st.appendChild(opt(s, T.status[s])); });
  function fillSets() {
    var keep = set.value; set.innerHTML = ""; set.appendChild(opt("", T.allSets));
    var seen = {};
    all.forEach(function (r) { if ((!lib.value || r.library === lib.value) && !seen[r.set]) { seen[r.set] = 1; set.appendChild(opt(r.set, T.set[r.set])); } });
    set.value = seen[keep] ? keep : "";
  }

  // read initial filters from the hash, e.g. #DISPLIB
  function fromHash() {
    var h = decodeURIComponent((location.hash || "").slice(1));
    lib.value = libs.indexOf(h) !== -1 ? h : "";
    fillSets();
  }
  fromHash();

  function render() {
    var term = q.value.trim().toLowerCase();
    var rows = all.filter(function (r) {
      if (lib.value && r.library !== lib.value) return false;
      if (set.value && r.set !== set.value) return false;
      if (st.value && r.status !== st.value) return false;
      if (term && [r.instance, r.library, T.set[r.set], r.record, r.bound_record, r.family].join(" ").toLowerCase().indexOf(term) === -1) return false;
      return true;
    });
    body.innerHTML = rows.map(function (r) {
      var u = r.size_kind ? T.size[r.size_kind] : null;
      var size = u ? "<span class='lib'>" + num(r.n1) + esc(u[0]) + "</span><span class='sub'>" + num(r.n2) + esc(u[1]) + "</span>" : "–";
      var gap = r.gap == null ? "–" : r.gap === 0 ? "0%" : (r.gap * 100).toFixed(r.gap < 0.1 ? 2 : 1) + "%";
      var sharedRecord = r.source === r.bound_source && r.record === r.bound_record && r.upper_evidence === r.bound_evidence;
      var records = recordLink(sharedRecord ? T.source.both : T.source.upper, r.record, r.source, r.upper_evidence);
      if (r.bound_source && !sharedRecord) {
        records += "<br>" + recordLink(T.source.lower, r.bound_record, r.bound_source, r.bound_evidence);
      }
      return "<tr>" +
        "<td class='mono'>" + esc(r.instance) + "</td>" +
        "<td><span class='lib'>" + esc(r.library) + "</span><span class='sub'>" + esc(T.set[r.set]) + "</span></td>" +
        "<td class='num'>" + size + "</td>" +
        "<td class='num'>" + num(r.best_known) + "</td>" +
        "<td class='num'>" + num(r.best_bound) + "</td>" +
        "<td class='num'>" + gap + "</td>" +
        "<td class='nw'><span class='status s-" + r.status + "'>" + esc(T.status[r.status]) + "</span></td>" +
        "<td class='rec'>" + records + "</td>" +
        "<td>" + esc(T.llm4rail[r.llm4rail]) + "</td>" +
        "</tr>";
    }).join("") || "<tr><td colspan='9'>" + T.none + "</td></tr>";
    count.textContent = T.count(rows.length, all.length);
  }

  lib.addEventListener("input", function () {
    fillSets(); render();
    history.replaceState(null, "", lib.value ? "#" + encodeURIComponent(lib.value) : location.pathname + location.search);
  });
  window.addEventListener("hashchange", function () { fromHash(); render(); });
  [q, set, st].forEach(function (e) { e.addEventListener("input", render); });
  render();
})();
