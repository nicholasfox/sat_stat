import { chromium } from 'playwright';

const browser = await chromium.connectOverCDP('http://localhost:9222');
const ctx = browser.contexts()[0];
const pages = ctx.pages();
const page = pages.length > 0 ? pages[0] : await ctx.newPage();

const BASE = 'http://localhost:15001';

try {
  // 1. Navigate
  await page.goto(BASE, { waitUntil: 'networkidle' });
  const title = await page.title();
  console.log('1. Page title:', title);
  console.assert(title.includes('Satellite'), 'Title check');

  // 2. Sidebar
  await page.waitForSelector('.sidebar', { timeout: 10000 });
  const cbCount = await page.locator('.sub-cb').count();
  console.log('2. Checkboxes:', cbCount);
  console.assert(cbCount > 10, 'Enough checkboxes');

  // 3. Default Starlink checked
  const checked = await page.locator('.sub-cb:checked').count();
  console.log('3. Pre-checked:', checked, '(expected 1)');
  console.assert(checked === 1, 'Only Starlink checked');

  // 4. Metadata
  const metaText = await page.locator('.sub-check-meta').first().textContent();
  console.log('4. Metadata:', metaText);

  // 5. Analyze
  await page.click('#btnAnalyze');
  await page.waitForTimeout(2000);
  const canvas = page.locator('#histogramChart');
  const canvasVisible = await canvas.isVisible();
  console.log('5. Chart visible:', canvasVisible);
  console.assert(canvasVisible, 'Chart rendered');

  // 6. Summary
  const summary = await page.locator('#summaryText').textContent();
  console.log('6. Summary:', summary);
  console.assert(summary.length > 0, 'Summary not empty');

  // 7. Chart JS data
  const chartData = await page.evaluate(() => {
    const chart = Chart.getChart('histogramChart');
    if (!chart) return null;
    return {
      labels: chart.data.labels.length,
      datasets: chart.data.datasets.length,
      totalBars: chart.data.datasets.reduce((s, ds) => s + ds.data.length, 0),
      indexAxis: chart.options.indexAxis,
    };
  });
  console.log('7. Chart data:', JSON.stringify(chartData));
  console.assert(chartData?.indexAxis === 'y', 'Horizontal bars');

  // 8. TLE epoch
  const epoch = await page.locator('#tleEpoch').textContent();
  console.log('8. TLE epoch:', epoch);

  console.log('\n=== All checks passed with Edge CDP ===');
} catch (e) {
  console.error('FAILED:', e.message);
  process.exit(1);
} finally {
  await browser.close();
}
