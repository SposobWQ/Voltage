import subprocess
import sys

def check_ffmpeg():
    try:
        # Проверяем наличие ffmpeg
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ FFmpeg найден: {result.stdout.strip()}")
        else:
            print("❌ FFmpeg не найден в PATH")
        
        # Проверяем версию
        version_result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if version_result.returncode == 0:
            print("✅ FFmpeg работает:")
            print(version_result.stdout.split('\n')[0])
        else:
            print("❌ FFmpeg не работает")
            
    except Exception as e:
        print(f"❌ Ошибка проверки FFmpeg: {e}")

if __name__ == "__main__":
    check_ffmpeg()