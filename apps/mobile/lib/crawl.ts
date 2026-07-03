import { resolveApiBaseUrl } from "@/lib/config";

export async function runCrawlAndWait(): Promise<{ ingested: number; discovered: number }> {
  const apiBaseUrl = await resolveApiBaseUrl();
  const start = await fetch(`${apiBaseUrl}/v1/crawl/run`, { method: "POST" });
  if (!start.ok) throw new Error(`Crawl failed: ${start.status}`);

  for (let i = 0; i < 120; i++) {
    const statusRes = await fetch(`${apiBaseUrl}/v1/crawl/status`);
    if (!statusRes.ok) {
      await sleep(2000);
      continue;
    }
    const status = await statusRes.json();
    if (status.running) {
      await sleep(2000);
      continue;
    }
    if (status.last_report) {
      await fetch(`${apiBaseUrl}/v1/crawl/seed-examples`, { method: "DELETE" });
      return status.last_report;
    }
    if (status.message?.startsWith("Fel:")) {
      throw new Error(status.message);
    }
    await sleep(2000);
  }
  throw new Error("Crawl timeout");
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
