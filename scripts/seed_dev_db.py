"""Reset a local dev database. Never run in production."""
import subprocess
import sys

name = sys.argv[1] if len(sys.argv) > 1 else "marlow.db"
subprocess.run(f"rm -f {name}", shell=True, check=True)
subprocess.run(
    f"{sys.executable} -c 'from marlow import create_app; create_app(\"{name}\")'",
    shell=True,
    check=True,
)
print(f"reset {name}")
