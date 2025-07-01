CodeRabbit
Fix hardcoded port in API docs URL

The docs URL is hardcoded to port 8000, but the actual port is configurable via the port parameter. This could mislead users when using a different port.

-        print("📚 API docs at: http://localhost:8000/docs")
+        print(f"📚 API docs at: http://localhost:{port}/docs")


CodeRabbit
Add port number validation

The port argument should be validated to ensure it's within the valid range (1-65535).

-    parser.add_argument("--port", type=int, default=8000, help="Server port")
+    parser.add_argument(
+        "--port", 
+        type=int, 
+        default=8000, 
+        help="Server port (1-65535)",
+        choices=range(1, 65536),
+        metavar="PORT"
+    )

CodeRabbit
Security consideration: --trust-remote-code is always enabled

The --trust-remote-code flag allows execution of arbitrary code from model repositories, which poses a security risk. Consider making this configurable or adding a warning.

Add a parameter to make this configurable:

-def start_vllm_server(model_path, port=8000, host="0.0.0.0"):
+def start_vllm_server(model_path, port=8000, host="0.0.0.0", trust_remote_code=False):
Then conditionally add the flag:

     cmd = [
         "python", "-m", "vllm.entrypoints.openai.api_server",
         "--model", model_path,
         "--host", host,
         "--port", str(port),
         "--tensor-parallel-size", "1",
         "--gpu-memory-utilization", "0.7",
-        "--trust-remote-code"
     ]
+    
+    if trust_remote_code:
+        cmd.append("--trust-remote-code")
+        print("⚠️  WARNING: Remote code execution is enabled!")

CodeRabbit
GPU VRAM specification is factually incorrect

The NVIDIA RTX 4070 Ti SUPER ships with 16 GB GDDR6X, not 32 GB. Over-stating VRAM may lead engineers to size models (e.g. 34 B parameters) that will not fit and will crash the server.

-**GPU**: RTX 4070 Ti SUPER (32GB VRAM)
+**GPU**: RTX 4070 Ti SUPER (16 GB VRAM)
Adjust the subsequent “Hardware Optimization Rationale” lines accordingly (61-64) to reflect realistic capacity or pick a GPU that genuinely has 24–48 GB if 34 B model support is a hard requirement.

CodeRabbit
Critical error: Missing sys import.

The script uses sys.exit() but doesn't import the sys module, which will cause a runtime NameError.

+import sys
 import requests
 import json
 import time
 import argparse
 from rich.console import Console

Improve virtual environment detection

The current virtual environment detection might not work correctly in all scenarios (e.g., conda environments). Consider using a more robust approach.

     # Check if in virtual environment
-    if not hasattr(sys, 'real_prefix') and not (
-        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
-    ):
+    in_virtualenv = (
+        hasattr(sys, 'real_prefix') or 
+        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
+        os.environ.get('VIRTUAL_ENV') is not None or
+        os.environ.get('CONDA_DEFAULT_ENV') is not None
+    )
+    

CodeRabbit
Make test model configurable

The test model is hardcoded. Consider making it configurable via environment variable for flexibility.

         # Use a small model for testing
-        model_name = "facebook/opt-125m"
+        model_name = os.environ.get("VLLM_TEST_MODEL", "facebook/opt-125m")
         
         # Initialize LLM
         llm = LLM(
             model=model_name,
             tensor_parallel_size=1,
             gpu_memory_utilization=0.3,
-            download_dir="/tmp/vllm_test_cache"
+            download_dir=os.environ.get("VLLM_CACHE_DIR", "/tmp/vllm_test_cache")
         )

CodeRabbit
Repeated tee -a ~/.bashrc causes unbounded duplication

Each script run appends the same block, bloating the user’s profile.
Guard with a sentinel comment or use sed -i replacement instead of blind append.

-tee -a ~/.bashrc << 'EOF'
+# Add once
+grep -q '# vLLM Compilation Environment' ~/.bashrc || tee -a ~/.bashrc <<'EOF'

Add a generated Table of Contents for easier navigation

At ~460 lines this report is sizeable. Inserting an auto-generated TOC under the Executive Summary dramatically improves accessibility when rendered on GitHub/GitLab.

CodeRabbit
Unify test-directory naming to avoid split test locations

Rules point developers to /validation/, yet the repository already contains /tasks/task-results/ and typical Python tooling (pytest, coverage) defaults to a tests/ package. Consider locking this down to a single canonical directory (e.g. tests/) and mapping “validation” as a semantic tag, not a separate tree, to prevent scattered test assets.


CodeRabbit
Improve virtual environment detection

The current virtual environment detection might not work correctly in all scenarios (e.g., conda environments). Consider using a more robust approach.

     # Check if in virtual environment
-    if not hasattr(sys, 'real_prefix') and not (
-        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
-    ):
+    in_virtualenv = (
+        hasattr(sys, 'real_prefix') or 
+        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
+        os.environ.get('VIRTUAL_ENV') is not None or
+        os.environ.get('CONDA_DEFAULT_ENV') is not None
+    )
+    
+    if not in_virtualenv:
         print("⚠️  Not in virtual environment")
         print("   Activate: source /opt/citadel/dev-env/bin/activate")
         return False
CodeRabbit
Fix hardcoded port in API docs URL

The docs URL is hardcoded to port 8000, but the actual port is configurable via the port parameter. This could mislead users when using a different port.

-        print("📚 API docs at: http://localhost:8000/docs")
+        print(f"📚 API docs at: http://localhost:{port}/docs")

CodeRabbit
Improve subprocess output handling for better debugging

The subprocess output is not captured, which makes debugging server issues difficult. Consider capturing and displaying the output.

-        process = subprocess.Popen(cmd)
+        process = subprocess.Popen(
+            cmd,
+            stdout=subprocess.PIPE,
+            stderr=subprocess.STDOUT,
+            universal_newlines=True,
+            bufsize=1
+        )
         print(f"✅ Server started with PID: {process.pid}")
         print(f"🌐 API will be available at: http://{host}:{port}")
         print("📚 API docs at: http://localhost:8000/docs")
         
-        # Wait for process
-        process.wait()
+        # Stream output in real-time
+        for line in process.stdout:
+            print(f"[vLLM] {line.rstrip()}")
+        
+        process.wait()


CodeRabbit
Make base directory configurable via environment variable

The base directory is hardcoded, which reduces flexibility. Consider using an environment variable with a fallback.

-    def __init__(self, base_dir: str = "/home/agent0/Citadel-Alpha-LLM-Server-1"):
+    def __init__(self, base_dir: str = None):
+        if base_dir is None:
+            base_dir = os.environ.get(
+                "CITADEL_BASE_DIR", 
+                "/home/agent0/Citadel-Alpha-LLM-Server-1"
+            )
         self.base_dir = Path(base_dir)

CodeRabbit
Critical error: Missing sys import.

The script uses sys.exit() but doesn't import the sys module, which will cause a runtime NameError.

+import sys
 import requests
 import json
 import time
 import argparse
 from rich.console import Console

CodeRabbit
GPU VRAM specification is factually incorrect

The NVIDIA RTX 4070 Ti SUPER ships with 16 GB GDDR6X, not 32 GB. Over-stating VRAM may lead engineers to size models (e.g. 34 B parameters) that will not fit and will crash the server.

-**GPU**: RTX 4070 Ti SUPER (32GB VRAM)
+**GPU**: RTX 4070 Ti SUPER (16 GB VRAM)
Adjust the subsequent “Hardware Optimization Rationale” lines accordingly (61-64) to reflect realistic capacity or pick a GPU that genuinely has 24–48 GB if 34 B model support is a hard requirement.

CodeRabbit
Add port number validation

The port argument should be validated to ensure it's within the valid range (1-65535).

-    parser.add_argument("--port", type=int, default=8000, help="Server port")
+    parser.add_argument(
+        "--port", 
+        type=int, 
+        default=8000, 
+        help="Server port (1-65535)",
+        choices=range(1, 65536),
+        metavar="PORT"
+    )

