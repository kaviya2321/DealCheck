"""
DealCheck Browser Automated Verification & Responsive Screenshot Script
Tests viewports:
- 360px (Mobile)
- 768px (Tablet)
- 1440px (Desktop)
In both light and dark mode, testing the full interactive flow.
"""

import os
import time
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

VIEWPORTS = [
    {"name": "mobile_360", "width": 360, "height": 780},
    {"name": "tablet_768", "width": 768, "height": 1024},
    {"name": "desktop_1440", "width": 1440, "height": 900}
]

def verify_and_capture():
    print("=" * 60)
    print("Starting DealCheck Browser Automated Verification & Screenshots")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for vp in VIEWPORTS:
            vp_name = vp["name"]
            width = vp["width"]
            height = vp["height"]
            print(f"\n--> Testing Viewport: {vp_name} ({width}x{height})...")

            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=2
            )
            page = context.new_page()

            # 1. Load Homepage
            page.goto("http://127.0.0.1:5173", wait_until="networkidle")
            page.wait_for_timeout(1000)

            # Screenshot: Step 1 (Input View)
            shot1 = os.path.join(SCREENSHOTS_DIR, f"{vp_name}_step1_input.png")
            page.screenshot(path=shot1, full_page=True)
            print(f"    [1/7] Saved Step 1 screenshot -> {shot1}")

            # 2. Click Sample Scam Chat
            scam_btn = page.locator("button:visible:has-text('Typical Scam')")
            scam_btn.click()
            page.wait_for_timeout(400)

            # 3. Click Analyze
            analyze_btn = page.locator("button:visible:has-text('Analyze Deal Safety')")
            analyze_btn.click()

            # Wait for Step 2 Analysis to load
            page.wait_for_selector("text=Deal Risk Analysis", timeout=15000)
            page.wait_for_timeout(1500)

            # Screenshot: Step 2 (Analysis & Custom SVG Gauge)
            shot2 = os.path.join(SCREENSHOTS_DIR, f"{vp_name}_step2_analysis.png")
            page.screenshot(path=shot2, full_page=True)
            print(f"    [2/7] Saved Step 2 screenshot -> {shot2}")

            # 4. Proceed to Step 3 (Protect)
            step3_btn = page.locator("button:visible:has-text('Step 3')")
            step3_btn.first.click()
            page.wait_for_selector("text=Step 3: Generate PayPal Protection", timeout=10000)
            page.wait_for_timeout(800)

            shot3 = os.path.join(SCREENSHOTS_DIR, f"{vp_name}_step3_protect.png")
            page.screenshot(path=shot3, full_page=True)
            print(f"    [3/7] Saved Step 3 screenshot -> {shot3}")

            # 5. Proceed to Step 4 (Seller Reaction)
            step4_btn = page.locator("button:visible:has-text('Step 4')")
            step4_btn.first.click()
            page.wait_for_selector("text=Step 4: Seller Reaction Litmus Test", timeout=10000)
            page.wait_for_timeout(800)

            # Click test reply simulation button in Step 4
            sim_btn = page.locator("button:visible:has-text('Seller Pushes F&F')")
            if sim_btn.count() > 0:
                sim_btn.first.click()
                page.wait_for_timeout(1500)

            shot4 = os.path.join(SCREENSHOTS_DIR, f"{vp_name}_step4_seller_reaction.png")
            page.screenshot(path=shot4, full_page=True)
            print(f"    [4/7] Saved Step 4 (Litmus test) screenshot -> {shot4}")

            # 6. Go to Model Card tab
            model_tab = page.locator("button:visible:has-text('Model')")
            model_tab.first.click()
            page.wait_for_selector("text=Machine Learning Model Card", timeout=10000)
            page.wait_for_timeout(1000)

            shot_model = os.path.join(SCREENSHOTS_DIR, f"{vp_name}_model_card.png")
            page.screenshot(path=shot_model, full_page=True)
            print(f"    [5/7] Saved Model Card screenshot -> {shot_model}")

            # 7. Toggle Dark Mode
            dark_btn = page.locator("button[aria-label='Toggle Dark Mode']:visible")
            dark_btn.first.click()
            page.wait_for_timeout(800)

            shot_dark = os.path.join(SCREENSHOTS_DIR, f"{vp_name}_dark_mode.png")
            page.screenshot(path=shot_dark, full_page=True)
            print(f"    [6/7] Saved Dark Mode screenshot -> {shot_dark}")

            # 8. Go to History tab in Dark Mode
            hist_tab = page.locator("button:visible:has-text('Deal History')")
            hist_tab.first.click()
            page.wait_for_selector("text=DealCheck History", timeout=10000)
            page.wait_for_timeout(800)

            shot_hist = os.path.join(SCREENSHOTS_DIR, f"{vp_name}_deal_history.png")
            page.screenshot(path=shot_hist, full_page=True)
            print(f"    [7/7] Saved Deal History screenshot -> {shot_hist}")

            context.close()

        browser.close()

    print("\n" + "=" * 60)
    print("All browser verifications & responsive screenshots completed successfully!")
    print(f"Screenshots directory: {SCREENSHOTS_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    verify_and_capture()
