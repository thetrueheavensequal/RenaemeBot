import subprocess
import datetime
import os

def backup_database():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"dazai_bot_backup_{timestamp}"
    
    cmd = f"mongodump --db dazai_rename_bot --out ./backups/{backup_name}"
    subprocess.run(cmd, shell=True)
    print(f"Backup created: ./backups/{backup_name}")

if __name__ == "__main__":
    os.makedirs("backups", exist_ok=True)
    backup_database()
