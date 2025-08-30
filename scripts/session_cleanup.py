from utils.session_store import cleanup_expired

if __name__ == "__main__":
    removed = cleanup_expired()
    print(f"removed {removed} session files")
