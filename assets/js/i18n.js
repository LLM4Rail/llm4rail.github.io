(function () {
  "use strict";
  var lang = (document.documentElement.lang || "en").toLowerCase().indexOf("zh") === 0 ? "zh" : "en";
  var D = {
    en: {
      set: {
        "railway": "Railway", "railway-variant": "Railway variant",
        "tpl-network": "Network data sets", "tpl-pesplib": "PESPlib networks with routing",
        "dl-smi": "smi · Siemens Mobility Italy", "dl-swi": "swi · SBB open data", "dl-wab": "wab · Wabtec",
        "dl-nor1": "nor1 · SINTEF, Norway", "dl-nor2": "nor2 · SINTEF, Norway", "dl-nor3": "nor3 · SINTEF, Norway",
        "dl-nor4": "nor4 · SINTEF, Norway", "dl-nor5": "nor5 · SINTEF, Norway",
        "miplib-easy": "Easy", "miplib-hard": "Hard"
      },
      status: { open: "Not proven optimal", optimal: "Optimal", no_bound: "No published bound" },
      llm4rail: { pending: "No published result" },
      evidence: {
        library_reported: "Published by the benchmark library",
        library_optimum: "Marked optimal in the library’s solution file",
        official_checker: "Solution checked with the official DISPLIB verifier",
        paper_reported: "Value reported in the paper",
        publisher_unverified: "Lower bound listed as unverified by PESPlib",
        routing_relaxation: "Lower bound from the library’s routing relaxation",
        nonnegative_objective: "Lower bound from nonnegativity of the objective"
      },
      source: { upper: "UB", lower: "LB", both: "UB / LB" },
      size: { ev_act: [" events", " activities"], tr_op: [" trains", " ops"], var_con: [" variables", " constraints"] },
      allLibs: "All libraries", allSets: "All sets", allStatus: "All statuses",
      count: function (n, t) { return n + " of " + t + " instances"; },
      none: "No instance matches these filters.",
      th: ["Instance", "Library / set", "Set", "Size", "Best known", "Best lower bound", "Gap", "Status", "Record", "LLM4Rail"],
      tip: { best: "Best known", bound: "Best lower bound", gap: "Gap", record: "Record" },
      chartGroups: { PESPlib: ["railway", "railway-variant"], TimPassLib: ["tpl-network", "tpl-pesplib"] }
    },
    zh: {
      set: {
        "railway": "铁路", "railway-variant": "铁路变体",
        "tpl-network": "路网数据集", "tpl-pesplib": "PESPlib 路网（含客流路径）",
        "dl-smi": "smi · 西门子交通（意大利）", "dl-swi": "swi · 瑞士联邦铁路开放数据", "dl-wab": "wab · Wabtec",
        "dl-nor1": "nor1 · SINTEF（挪威）", "dl-nor2": "nor2 · SINTEF（挪威）", "dl-nor3": "nor3 · SINTEF（挪威）",
        "dl-nor4": "nor4 · SINTEF（挪威）", "dl-nor5": "nor5 · SINTEF（挪威）",
        "miplib-easy": "Easy", "miplib-hard": "Hard"
      },
      status: { open: "未证明最优", optimal: "已证明最优", no_bound: "无公开下界" },
      llm4rail: { pending: "尚无公开结果" },
      evidence: {
        library_reported: "问题库公布的值",
        library_optimum: "问题库解文件标记为最优",
        official_checker: "解已通过 DISPLIB 官方验证程序",
        paper_reported: "论文报告值",
        publisher_unverified: "PESPlib 注明该下界未经验证",
        routing_relaxation: "问题库的客流路径松弛下界",
        nonnegative_objective: "由目标值非负推出的下界"
      },
      source: { upper: "上界", lower: "下界", both: "上下界" },
      size: { ev_act: [" 事件", " 活动"], tr_op: [" 列车", " 作业"], var_con: [" 变量", " 约束"] },
      allLibs: "全部问题库", allSets: "全部集合", allStatus: "全部状态",
      count: function (n, t) { return "共 " + t + " 个实例，显示 " + n + " 个"; },
      none: "没有符合筛选条件的实例。",
      th: ["实例", "问题库 / 集合", "集合", "规模", "已知最好解", "最好下界", "差距", "状态", "纪录来源", "LLM4Rail"],
      tip: { best: "已知最好解", bound: "最好下界", gap: "差距", record: "纪录来源" },
      chartGroups: { PESPlib: ["railway", "railway-variant"], TimPassLib: ["tpl-network", "tpl-pesplib"] }
    }
  };
  window.LLM4RAIL_I18N = { lang: lang, t: D[lang] };
})();
