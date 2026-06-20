import os
import platform


# Generate the executable name based on OS.
system = platform.system().lower()
# print("libc:", platform.libc_ver())

# need to correspond to ".github/workflows/build.yml"
match os.getenv("RUNNER_MACHINE"):
    case "windows-latest" | "ubuntu-22.04":
        pass  # default - nothing to do
    case "ubuntu-latest":
        # Differentiate between old glibc (above, for maximum compatibility)
        # and newer glibc (here, just for testing).
        system += "-new-glibc"
    case "ubuntu-22.04-arm":
        system += "-" + platform.machine().lower()
    case "macos-latest" | "macos-15-intel":
        # Differentiate between ARM and Intel based Macs.
        system += "-" + platform.machine().lower()
executable_name = f"jimmy-{system}"
print(executable_name)
