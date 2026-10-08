"""
download_models.py - Asset & Model Weight Downloader.

Downloads the official MediaPipe models required for pose and hand tracking:
1. pose_landmarker.task (BlazePose Heavy model)
2. hand_landmarker.task (Hand Landmarker model)

Usage:
    python download_models.py
"""

import os
import sys
import urllib.request
import ssl

MODELS = {
    "pose_landmarker.task": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task",
    "hand_landmarker.task": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
}

def reporthook(block_num, block_size, total_size):
    """Print download progress with byte count and percentage."""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100.0, downloaded / total_size * 100.0)
        mb_down = downloaded / (1024 * 1024)
        mb_tot = total_size / (1024 * 1024)
        sys.stdout.write(f"\r  Progress: [{percent:5.1f}%] {mb_down:.2f} MB / {mb_tot:.2f} MB")
        sys.stdout.flush()
    else:
        mb_down = downloaded / (1024 * 1024)
        sys.stdout.write(f"\r  Downloaded: {mb_down:.2f} MB")
        sys.stdout.flush()

def download_models(force: bool = False) -> None:
    print("\n=======================================================")
    print("      BASKETBALL AI - MODEL ASSET DOWNLOADER")
    print("=======================================================\n")
    
    # Bypass local SSL verification issues if running behind strict proxies
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for filename, url in MODELS.items():
        if os.path.exists(filename) and not force:
            size_mb = os.path.getsize(filename) / (1024 * 1024)
            print(f"[EXISTS] '{filename}' ({size_mb:.2f} MB) already exists. Skipping download.")
            continue
        
        print(f"\n[DOWNLOADING] '{filename}' from:")
        print(f"  {url}")
        try:
            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(url, filename, reporthook=reporthook)
            print(f"\n[SUCCESS] '{filename}' downloaded successfully.")
        except Exception as e:
            print(f"\n[ERROR] Failed to download '{filename}': {e}")
            print(f"  Please download manually from: {url}")

    print("\n[DONE] Model assets verification complete.\n")

if __name__ == "__main__":
    force_download = "--force" in sys.argv
    download_models(force=force_download)
