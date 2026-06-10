// AIVisionRadar - minimal JS helpers
document.addEventListener("DOMContentLoaded", () => {
  // Show crawl result feedback from HTMX
  document.body.addEventListener("htmx:afterRequest", (evt) => {
    try {
      const data = JSON.parse(evt.detail.xhr.responseText);
      const url = evt.detail.requestConfig?.path || "";

      if (url.includes("/crawl/run")) {
        const el = document.getElementById("crawl-result");
        if (el && data.result) {
          el.textContent = `完成：新增 ${data.result.total_new} 条，已打分 ${data.result.scored} 条`;
        }
      } else if (url.includes("/translate/run")) {
        const el = document.getElementById("translate-result");
        if (el) el.textContent = data.message || `已翻译 ${data.translated} 条`;
      } else if (url.includes("/crawl/summarize")) {
        const el = document.getElementById("summarize-result");
        if (el) el.textContent = `已生成 ${data.summarized} 条摘要`;
      }
    } catch (_) {}
  });
});
