#!/usr/bin/env python3
"""
Playwright auto-pilot for wood beam simulation
Records a video of the auto-experiment running until fracture
"""
import asyncio
import os
import sys

import subprocess

async def main():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Installing playwright...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        from playwright.async_api import async_playwright

    output_dir = "/home/bons/repos/bridge-archetypes-100/output"
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            record_video_dir=output_dir,
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()

        # Navigate to the app
        await page.goto("http://localhost:8000/static/index.html", wait_until="networkidle")
        await asyncio.sleep(1)

        # Start autoplay
        await page.click("#autoplay")
        print("Autoplay started...")

        # Wait for fracture (up to 60 seconds)
        try:
            await page.wait_for_selector(".fracture.show", timeout=60000)
            print("Fracture detected!")
        except Exception:
            print("Timeout waiting for fracture")

        # Let fracture settle visually
        await asyncio.sleep(1.5)

        # Add overlay text to video? Not possible directly; we can screenshot the final state
        screenshot = await page.screenshot(path=os.path.join(output_dir, "final_frame.png"))

        # Close to save video
        await context.close()
        await browser.close()

    # Playwright saves video as .webm; convert to mp4
    webm_files = [f for f in os.listdir(output_dir) if f.endswith(".webm")]
    if webm_files:
        webm_path = os.path.join(output_dir, webm_files[0])
        mp4_path = os.path.join(output_dir, "bridge100_demo.mp4")
        ffmpeg = os.popen("which ffmpeg").read().strip()
        if ffmpeg:
            cmd = [
                ffmpeg, "-y", "-i", webm_path,
                "-pix_fmt", "yuv420p", "-c:v", "libx264",
                "-crf", "22", "-movflags", "+faststart", mp4_path
            ]
            subprocess.run(cmd, capture_output=True)
            print(f"MP4 saved: {mp4_path} ({os.path.getsize(mp4_path)} bytes)")
        else:
            print(f"No ffmpeg, webm saved: {webm_path}")
    else:
        print("No video file found")

if __name__ == "__main__":
    asyncio.run(main())
