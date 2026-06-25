import psutil

def list_python_procs():
    print("=== Running Python Processes ===")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = proc.info['cmdline']
            if cmd:
                cmd_str = " ".join(cmd).lower()
                if "python" in proc.info['name'].lower() or "python" in cmd_str:
                    print(f"PID: {proc.pid} | Name: {proc.info['name']} | Cmd: {proc.info['cmdline']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

if __name__ == "__main__":
    list_python_procs()
