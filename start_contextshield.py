import subprocess
import sys
import os
import signal
import time
import platform

def main():
    print("🚀 Starting ContextShield Unified Environment...")
    print("-" * 50)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    proxy_dir = os.path.join(base_dir, "proxy")
    dashboard_dir = os.path.join(base_dir, "dashboard")
    
    is_windows = platform.system().lower() == "windows"
    
    npm_exec = "npm.cmd" if is_windows else "npm"
    uvicorn_exec = "uvicorn.exe" if is_windows else "uvicorn"
    
    # Process Group Flags: This ensures that when we send a kill signal, it kills 
    # the entire process tree (e.g., node.exe spawning vite) rather than just the wrapper.
    kwargs = {}
    if is_windows:
        kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs['preexec_fn'] = os.setsid

    print("-> Launching FastAPI Proxy (Port 8000)")
    proxy_process = subprocess.Popen(
        [uvicorn_exec, "app.main:app", "--reload", "--port", "8000"], 
        cwd=proxy_dir,
        **kwargs
    )
    
    print("-> Launching Vite Dashboard (Port 5173)")
    dashboard_process = subprocess.Popen(
        [npm_exec, "run", "dev"],
        cwd=dashboard_dir,
        **kwargs
    )
    
    def cleanup(signum=None, frame=None):
        print("\n🛑 Shutting down ContextShield...")
        
        def kill_tree(proc, name):
            print(f"-> Terminating {name} Process Tree...")
            if proc.poll() is None:
                if is_windows:
                    try:
                        os.kill(proc.pid, signal.CTRL_BREAK_EVENT)
                    except Exception as e:
                        print(f"Failed graceful kill for {name}: {e}. Forcing terminate...")
                        proc.terminate()
                else:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    except Exception as e:
                        proc.terminate()
                        
        kill_tree(proxy_process, "Proxy")
        kill_tree(dashboard_process, "Dashboard")
        
        proxy_process.wait()
        dashboard_process.wait()
        print("Shutdown complete. No orphan processes left behind. Goodbye!")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("-" * 50)
    print("✅ Environment is live! Press Ctrl+C at any time to exit both servers cleanly.")
    
    try:
        # Keep the main thread alive waiting for an interrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
