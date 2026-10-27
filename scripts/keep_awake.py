"""
Windows Sleep Prevention Utility for Long-Running Background Ingestion
Ushbu skript Windows'ni uyqu (Sleep/Suspend/Hibernate) rejimiga o'tib qolishini bloklaydi.
Ekran o'chishi mumkin (elektr tejash uchun), lekin protsessor, tarmoq va yuklashlar 24/7 ishlayveradi.
"""
import ctypes
import time
import sys

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_AWAYMODE_REQUIRED = 0x00000040

def run():
    print("[AWAKE] Tizim uyqu rejimiga ketishi to'liq bloklandi.")
    print("[AWAKE] Noutbuk qopqog'i yopilsa ham yoki uzoq vaqt tegmasangiz ham protsessor va tarmoq uxlamaydi.")
    sys.stdout.flush()
    flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED
    ctypes.windll.kernel32.SetThreadExecutionState(flags)
    try:
        while True:
            time.sleep(60)
            ctypes.windll.kernel32.SetThreadExecutionState(flags)
    except KeyboardInterrupt:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        print("[AWAKE] Uyqu blokirovkasi to'xtatildi.")

if __name__ == "__main__":
    run()
