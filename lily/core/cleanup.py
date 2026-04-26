import os
import time
from lily import logger

def auto_clean():
    """
    Deletes files in cache and downloads directories that are older than two weeks.
    """
    now = time.time()
    two_weeks_sec = 14 * 24 * 60 * 60
    
    for folder in ["cache", "downloads"]:
        if not os.path.exists(folder):
            continue
            
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            
            # Skip hidden files
            if filename.startswith("."):
                continue
                
            try:
                if os.path.isfile(file_path):
                    if os.stat(file_path).st_mtime < now - two_weeks_sec:
                        os.remove(file_path)
                        logger.info(f"Auto-deleted old file: {filename}")
            except Exception as e:
                logger.error(f"Error deleting {filename}: {e}")

if __name__ == "__main__":
    auto_clean()
