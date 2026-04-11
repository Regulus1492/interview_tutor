import os
import zipfile
import urllib.request
import shutil

def install_ffmpeg():
    print("Downloading FFmpeg (approx 70MB)...")
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = "ffmpeg.zip"
    
    try:
        urllib.request.urlretrieve(url, zip_path)
    except Exception as e:
        print(f"Download failed: {e}")
        return

    print("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Find the bin folder in the zip
        for file in zip_ref.namelist():
            if file.endswith("bin/ffmpeg.exe"):
                source = zip_ref.open(file)
                target = open("ffmpeg.exe", "wb")
                shutil.copyfileobj(source, target)
                source.close()
                target.close()
                print("Extracted ffmpeg.exe")
            elif file.endswith("bin/ffprobe.exe"):
                source = zip_ref.open(file)
                target = open("ffprobe.exe", "wb")
                shutil.copyfileobj(source, target)
                source.close()
                target.close()
                print("Extracted ffprobe.exe")
    
    print("Cleaning up...")
    os.remove(zip_path)
    print("Done! You can now run tutor.py")

if __name__ == "__main__":
    install_ffmpeg()