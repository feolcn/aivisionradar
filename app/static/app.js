// AIVisionRadar - minimal JS helpers
document.addEventListener("DOMContentLoaded", () => {
  // Show crawl result feedback from HTMX
  document.body.addEventListener("htmx:afterRequest", (evt) => {
    const el = document.getElementById("crawl-result");
    if (el && evt.detail.successful) {
      try {
        const data = JSON.parse(evt.detail.xhr.responseText);
        if (data.result) {
          el.textContent = `完成：新增 ${data.result.total_new} 条，已打分 ${data.result.scored} 条`;
          el.style.color = "#16a34a";
        }
      } catch (_) {}
    }
  });
});
