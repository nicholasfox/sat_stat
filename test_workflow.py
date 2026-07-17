"""End-to-end Playwright test for the Satellite TLE Analyzer."""

import json
import os
import signal
import subprocess
import sys
import time
import shutil

from playwright.sync_api import sync_playwright, expect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TLE_FILE = os.path.join(BASE_DIR, 'tle_data.json')
SERVER_SCRIPT = os.path.join(BASE_DIR, 'analysis.py')
TEST_TLE = os.path.join(BASE_DIR, 'test_tle_data.json')


PORT = os.environ.get('TEST_PORT', '15001')


def start_server():
    env = os.environ.copy()
    env['PORT'] = PORT
    proc = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
        env=env,
    )
    time.sleep(1)
    return proc


def stop_server(proc):
    if proc:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait()


def create_test_tle():
    test_sats = [
        {"name": "STARLINK-1008", "line1": "1 44713U 19074A   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 44713  53.0000 100.0000 0001000  90.0000 270.0000 15.06390000 00001"},
        {"name": "STARLINK-1063", "line1": "1 44714U 19074B   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 44714  53.0000 101.0000 0001000  90.0000 270.0000 15.06390000 00002"},
        {"name": "ONEWEB-0012", "line1": "1 50001U 21000A   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 50001  87.9000  50.0000 0002000 100.0000 260.0000 14.45000000 00001"},
        {"name": "ONEWEB-0007", "line1": "1 50002U 21000B   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 50002  87.9000  51.0000 0002000 100.0000 260.0000 14.45000000 00002"},
        {"name": "IRIDIUM 106", "line1": "1 43000U 17000A   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 43000  86.4000 200.0000 0002000 150.0000 210.0000 14.34210000 00001"},
        {"name": "IRIDIUM 103", "line1": "1 43001U 17000B   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 43001  86.4000 201.0000 0002000 150.0000 210.0000 14.34210000 00002"},
        {"name": "NAVSTAR 43 (USA 132)", "line1": "1 24876U 97035A   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 24876  55.0000 300.0000 0000000 200.0000 160.0000  2.00560000 00001"},
        {"name": "GLONASS 756", "line1": "1 32393U 07065A   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 32393  64.8000  50.0000 0000000 300.0000  60.0000  2.12560000 00001"},
        {"name": "GALILEO 14", "line1": "1 41175U 15050A   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 41175  56.0000 150.0000 0001000  20.0000 340.0000  2.00600000 00001"},
        {"name": "BEIDOU-3 M1", "line1": "1 43003U 17000C   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 43003  55.0000 100.0000 0000000  90.0000 270.0000  2.00050000 00001"},
        {"name": "ISS (ZARYA)", "line1": "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-4 0  9999", "line2": "2 25544  51.6423  50.0000 0001000 100.0000 260.0000 15.49222000 00001"},
        {"name": "NOAA 19", "line1": "1 33591U 09005A   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 33591  98.7000 250.0000 0012000  80.0000 280.0000 14.12610000 00001"},
        {"name": "GOES 16", "line1": "1 41866U 16071A   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 41866   0.0000 100.0000 0000000 200.0000 160.0000  1.00270000 00001"},
        {"name": "FLOCK 4Q-1", "line1": "1 50003U 21000C   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 50003  97.5000  30.0000 0005000  90.0000 270.0000 15.20000000 00001"},
        {"name": "FALCON 9 R/B", "line1": "1 50004U 21000D   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 50004  53.0000 200.0000 0001000 100.0000 260.0000 15.06390000 00001"},
        {"name": "COSMOS 2560", "line1": "1 50005U 22000A   24001.50000000  .00000000  00000-0  00000-0 0  9999", "line2": "2 50005  82.5000  50.0000 0010000  80.0000 280.0000 15.70000000 00001"},
    ]
    with open(TEST_TLE, 'w') as f:
        json.dump(test_sats, f)


def main():
    create_test_tle()
    backend = None

    try:
        if os.path.exists(TLE_FILE):
            shutil.copy2(TLE_FILE, TLE_FILE + '.bak')
        shutil.copy2(TEST_TLE, TLE_FILE)

        print("Starting server...")
        backend = start_server()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            base_url = "http://localhost:" + PORT

            # --- Step 1: Load the page ---
            print("1. Loading page...")
            page.goto(base_url)
            expect(page.locator('h1')).to_contain_text('Satellite Orbit Altitude Distribution')
            print("   OK")

            # --- Step 2: Check sidebar loaded ---
            print("2. Checking sidebar loaded...")
            page.wait_for_selector('.sidebar', timeout=10000)
            page.wait_for_selector('.sub-check', timeout=10000)
            cbs = page.locator('.sub-cb')
            cb_count = cbs.count()
            print(f"   {cb_count} checkboxes rendered")
            assert cb_count > 10, f"Expected >10 checkboxes, got {cb_count}"
            assert page.locator('.cat-section').count() >= 5

            # --- Step 3: Check default (only Starlink checked) ---
            print("3. Checking default selection...")
            checked = page.locator('.sub-cb:checked')
            checked_count = checked.count()
            print(f"   {checked_count} checkboxes pre-checked (expected: only Starlink)")
            assert checked_count == 1, "Expected exactly 1 pre-checked (Starlink)"

            # --- Step 4: Check metadata is displayed ---
            print("4. Checking metadata in subcategory labels...")
            first_meta = page.locator('.sub-check-meta').first
            expect(first_meta).to_be_visible()
            print(f"   Metadata text: {first_meta.text_content()}")

            # --- Step 5: Click Analyze ---
            print("5. Clicking Analyze...")
            page.click('#btnAnalyze')
            page.wait_for_timeout(2000)

            chart_canvas = page.locator('#histogramChart')
            expect(chart_canvas).to_be_visible()
            print("   Chart rendered")

            summary = page.locator('#summaryText')
            expect(summary).not_to_be_empty()
            summary_text = summary.text_content()
            print(f"   Summary: {summary_text}")

            chart_data = page.evaluate("""() => {
                const chart = Chart.getChart('histogramChart');
                if (!chart) return null;
                return {
                    labels: chart.data.labels.length,
                    datasets: chart.data.datasets.length,
                    totalBars: chart.data.datasets.reduce((s, ds) => s + ds.data.length, 0),
                    indexAxis: chart.options.indexAxis
                };
            }""")
            print(f"   Chart data: {chart_data}")
            assert chart_data['indexAxis'] == 'y', "Expected horizontal bar chart (indexAxis='y')"

            # --- Step 6: Test bin width dropdown ---
            print("6. Testing bin width selector...")
            bw_select = page.locator('#binWidth')
            bw_select.select_option('50')
            page.wait_for_timeout(2000)
            expect(chart_canvas).to_be_visible()
            print("   Bin width 50km OK (onchange triggered auto-analyze)")

            # --- Step 7: Uncheck Starlink, re-analyze should fail ---
            print("7. Testing no-selection error...")
            starlink_cb = page.locator('.sub-cb[data-sub="starlink"]')
            if starlink_cb.count() > 0:
                starlink_cb.uncheck()
            page.click('#btnAnalyze')
            page.wait_for_timeout(500)
            status_text = page.locator('#statusText')
            expect(status_text).to_contain_text('Select at least one')
            print("   No-selection error shown")

            # --- Step 8: Check Navigation via "all" toggle ---
            print("8. Testing Select All for Navigation...")
            cat_sections = page.locator('.cat-section')
            nav_section = cat_sections.nth(1)
            all_btn = nav_section.locator('.cat-toggle').nth(0)
            all_btn.click()
            page.wait_for_timeout(500)

            if starlink_cb.count() > 0:
                starlink_cb.check()

            page.click('#btnAnalyze')
            page.wait_for_timeout(2000)
            expect(chart_canvas).to_be_visible()
            print("   Analyze after Select All OK")

            # --- Step 9: Test dB mode toggle ---
            print("9. Testing dB mode toggle...")
            if starlink_cb.count() > 0 and not starlink_cb.is_checked():
                starlink_cb.check()
            page.click('#btnAnalyze')
            page.wait_for_timeout(2000)
            expect(chart_canvas).to_be_visible()

            db_cb = page.locator('#dbMode')
            db_cb.check()
            page.wait_for_timeout(2000)
            expect(chart_canvas).to_be_visible()
            print("   dB mode ON - chart rendered")

            summary_text = page.locator('#summaryText').text_content()
            assert 'dB' in summary_text, f"Expected 'dB scale' in summary: {summary_text}"
            print(f"   dB summary: {summary_text}")

            db_cb.uncheck()
            page.wait_for_timeout(2000)
            expect(chart_canvas).to_be_visible()
            print("   dB mode OFF - chart rendered OK")

            browser.close()
            print("\nAll tests passed!")

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        stop_server(backend)
        if os.path.exists(TLE_FILE + '.bak'):
            shutil.move(TLE_FILE + '.bak', TLE_FILE)
        if os.path.exists(TEST_TLE):
            os.remove(TEST_TLE)


if __name__ == '__main__':
    main()
