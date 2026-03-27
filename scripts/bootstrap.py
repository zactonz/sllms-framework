from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
WHISPER_RUNTIME_DIR = MODELS_DIR / "whisper-runtime"
LLAMA_RUNTIME_DIR = MODELS_DIR / "llama-runtime"
PIPER_RUNTIME_DIR = MODELS_DIR / "piper-runtime"
THIRD_PARTY_DIR = ROOT / "third_party"


WHISPER_MODEL_URLS = {
    "tiny.en": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin?download=true",
    "base.en": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin?download=true",
}

LLM_MODEL_URLS = {
    "phi-3-mini-q4": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf?download=true",
}

PIPER_VOICE_URLS = {
    "en_US-lessac-medium": {
        "model": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true",
    }
}

PIPER_ASSETS = {
    ("Windows", "AMD64"): "piper_windows_amd64.zip",
    ("Linux", "x86_64"): "piper_linux_x86_64.tar.gz",
    ("Linux", "aarch64"): "piper_linux_aarch64.tar.gz",
    ("Darwin", "arm64"): "piper_macos_aarch64.tar.gz",
    ("Darwin", "x86_64"): "piper_macos_x64.tar.gz",
}

BACKENDS = [
    {
        "name": "whisper.cpp",
        "repo": "https://github.com/ggml-org/whisper.cpp.git",
        "release_api": "https://api.github.com/repos/ggml-org/whisper.cpp/releases/latest",
        "repo_dir": THIRD_PARTY_DIR / "whisper.cpp",
        "binary_name": "whisper-cli.exe" if os.name == "nt" else "whisper-cli",
        "output_path": WHISPER_RUNTIME_DIR / ("whisper-cli.exe" if os.name == "nt" else "whisper-cli"),
    },
    {
        "name": "llama.cpp",
        "repo": "https://github.com/ggml-org/llama.cpp.git",
        "release_api": "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest",
        "repo_dir": THIRD_PARTY_DIR / "llama.cpp",
        "binary_name": "llama-cli.exe" if os.name == "nt" else "llama-cli",
        "output_path": LLAMA_RUNTIME_DIR / ("llama-cli.exe" if os.name == "nt" else "llama-cli"),
    },
]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not any([args.python_deps, args.backends, args.models, args.all]):
        args.all = True

    try:
        ensure_directories()
        if args.all or args.python_deps:
            install_python_dependencies()
        if args.all or args.backends:
            install_backends()
        if args.all or args.models:
            install_models(args.stt_model, args.llm_model, args.voice)
        print_status("done", "Bootstrap finished successfully.")
        return 0
    except Exception as exc:
        print_status("error", str(exc))
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap the offline assistant backends and models.")
    parser.add_argument("--all", action="store_true", help="Install Python dependencies, backends, and models.")
    parser.add_argument("--python-deps", action="store_true", help="Install Python dependencies from requirements.txt.")
    parser.add_argument("--backends", action="store_true", help="Clone/build whisper.cpp and llama.cpp, and install Piper.")
    parser.add_argument("--models", action="store_true", help="Download configured STT, LLM, and TTS models.")
    parser.add_argument("--stt-model", default="base.en", choices=sorted(WHISPER_MODEL_URLS.keys()))
    parser.add_argument("--llm-model", default="phi-3-mini-q4", choices=sorted(LLM_MODEL_URLS.keys()))
    parser.add_argument("--voice", default="en_US-lessac-medium", choices=sorted(PIPER_VOICE_URLS.keys()))
    return parser


def ensure_directories() -> None:
    for path in (
        MODELS_DIR,
        WHISPER_RUNTIME_DIR,
        LLAMA_RUNTIME_DIR,
        PIPER_RUNTIME_DIR,
        THIRD_PARTY_DIR,
        MODELS_DIR / "whisper",
        MODELS_DIR / "llm",
        MODELS_DIR / "piper",
    ):
        path.mkdir(parents=True, exist_ok=True)


def install_python_dependencies() -> None:
    print_status("python", "Installing Python dependencies from requirements.txt")
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=ROOT)


def install_backends() -> None:
    for backend in BACKENDS:
        installed = try_install_prebuilt_backend(backend)
        if not installed:
            require_command("git")
            require_command("cmake")
            clone_or_update_repo(backend["repo"], backend["repo_dir"])
            build_cpp_backend(backend)
    install_piper_runtime()


def install_models(stt_model: str, llm_model: str, voice: str) -> None:
    whisper_dest = MODELS_DIR / "whisper" / f"ggml-{stt_model}.bin"
    download_file(WHISPER_MODEL_URLS[stt_model], whisper_dest, f"Whisper model ({stt_model})")

    llm_filename = Path(LLM_MODEL_URLS[llm_model].split("/resolve/", 1)[1].split("?", 1)[0]).name
    llm_dest = MODELS_DIR / "llm" / llm_filename
    download_file(LLM_MODEL_URLS[llm_model], llm_dest, f"LLM model ({llm_model})")

    voice_urls = PIPER_VOICE_URLS[voice]
    voice_dest = MODELS_DIR / "piper" / f"{voice}.onnx"
    voice_config_dest = MODELS_DIR / "piper" / f"{voice}.onnx.json"
    download_file(voice_urls["model"], voice_dest, f"Piper voice ({voice})")
    download_file(voice_urls["config"], voice_config_dest, f"Piper voice config ({voice})")

    print_status(
        "models",
        json.dumps(
            {
                "stt_model": str(whisper_dest),
                "llm_model": str(llm_dest),
                "voice_model": str(voice_dest),
                "voice_config": str(voice_config_dest),
            },
            indent=2,
        ),
    )


def clone_or_update_repo(repo_url: str, repo_dir: Path) -> None:
    if repo_dir.exists() and (repo_dir / ".git").exists():
        print_status("git", f"Updating {repo_dir.name}")
        run_command(["git", "-C", str(repo_dir), "pull", "--ff-only"], cwd=ROOT)
        return
    print_status("git", f"Cloning {repo_url}")
    run_command(["git", "clone", "--depth", "1", repo_url, str(repo_dir)], cwd=ROOT)


def build_cpp_backend(backend: dict) -> None:
    build_dir = backend["repo_dir"] / "build-sllms"
    print_status("build", f"Configuring {backend['name']}")
    run_command(["cmake", "-S", str(backend["repo_dir"]), "-B", str(build_dir)], cwd=ROOT)

    build_cmd = ["cmake", "--build", str(build_dir), "--config", "Release"]
    if os.name != "nt":
        build_cmd.extend(["-j", str(os.cpu_count() or 4)])
    print_status("build", f"Building {backend['name']}")
    run_command(build_cmd, cwd=ROOT)

    binary_path = find_file(build_dir, backend["binary_name"])
    install_runtime_bundle(binary_path.parent, backend["output_path"].parent, backend["name"])
    print_status("install", f"Installed {backend['name']} to {backend['output_path']}")


def try_install_prebuilt_backend(backend: dict) -> bool:
    try:
        release = fetch_json(backend["release_api"])
        asset = select_backend_asset(backend["name"], release.get("assets", []))
        if asset is None:
            print_status("backend", f"No prebuilt asset match for {backend['name']}; falling back to source build.")
            return False

        archive_name = asset["name"]
        archive_path = ROOT / archive_name
        download_file(asset["browser_download_url"], archive_path, f"{backend['name']} runtime ({archive_name})")

        extract_dir = THIRD_PARTY_DIR / f"prebuilt-{backend['name']}"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True, exist_ok=True)
        unpack_archive(archive_path, extract_dir)
        archive_path.unlink(missing_ok=True)

        binary_path = find_file(extract_dir, backend["binary_name"])
        install_runtime_bundle(binary_path.parent, backend["output_path"].parent, backend["name"])
        print_status("install", f"Installed prebuilt {backend['name']} to {backend['output_path']}")
        return True
    except Exception as exc:
        print_status("backend", f"Prebuilt install failed for {backend['name']}: {exc}")
        return False


def install_piper_runtime() -> None:
    asset_name = select_piper_asset()
    release = fetch_json("https://api.github.com/repos/rhasspy/piper/releases/latest")
    release_url = None
    for asset in release.get("assets", []):
        if asset.get("name") == asset_name:
            release_url = asset.get("browser_download_url")
            break
    if not release_url:
        raise RuntimeError(f"Could not find Piper asset '{asset_name}' in the latest release.")
    archive_path = ROOT / asset_name
    download_file(release_url, archive_path, f"Piper runtime ({asset_name})")
    if PIPER_RUNTIME_DIR.exists():
        shutil.rmtree(PIPER_RUNTIME_DIR)
    PIPER_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    unpack_archive(archive_path, PIPER_RUNTIME_DIR)
    archive_path.unlink(missing_ok=True)

    piper_binary_name = "piper.exe" if os.name == "nt" else "piper"
    piper_binary = find_file(PIPER_RUNTIME_DIR, piper_binary_name)
    if os.name != "nt":
        piper_binary.chmod(0o755)
    print_status("install", f"Installed Piper runtime to {piper_binary.parent}")


def select_piper_asset() -> str:
    key = (platform.system(), platform.machine())
    asset_name = PIPER_ASSETS.get(key)
    if asset_name is None:
        raise RuntimeError(
            f"No Piper runtime asset mapping for platform={platform.system()} arch={platform.machine()}. "
            "Download it manually and place it under models/piper-runtime."
        )
    return asset_name


def select_backend_asset(backend_name: str, assets: list[dict]) -> dict | None:
    system = platform.system()
    machine = platform.machine()
    selectors = backend_asset_selectors(backend_name, system, machine)
    if not selectors:
        return None

    candidates = []
    for asset in assets:
        name = asset.get("name", "").lower()
        if not (name.endswith(".zip") or name.endswith(".tar.gz")):
            continue
        for required_tokens, excluded_tokens in selectors:
            if all(token in name for token in required_tokens) and all(token not in name for token in excluded_tokens):
                candidates.append(asset)
                break

    if not candidates:
        return None
    return sorted(candidates, key=lambda item: len(item.get("name", "")))[0]


def backend_asset_selectors(backend_name: str, system: str, machine: str) -> list[tuple[list[str], list[str]]]:
    if backend_name == "llama.cpp":
        mapping = {
            ("Windows", "AMD64"): [(["llama", "win", "cpu", "x64"], ["cuda", "vulkan", "opencl", "sycl", "hip"])],
            ("Windows", "ARM64"): [(["llama", "win", "cpu", "arm64"], ["cuda", "vulkan", "opencl", "sycl", "hip"])],
            ("Darwin", "arm64"): [(["llama", "macos", "arm64"], [])],
            ("Darwin", "x86_64"): [(["llama", "macos", "x64"], [])],
            ("Linux", "x86_64"): [(["llama", "ubuntu", "x64"], ["vulkan", "rocm", "openvino"])],
            ("Linux", "aarch64"): [(["llama", "openeuler", "aarch64"], ["aclgraph"])],
        }
        return mapping.get((system, machine), [])

    if backend_name == "whisper.cpp":
        mapping = {
            ("Windows", "AMD64"): [(["whisper", "bin", "x64"], ["blas", "cublas"])],
            ("Windows", "x86"): [(["whisper", "bin", "win32"], ["blas", "cublas"])],
        }
        return mapping.get((system, machine), [])

    return []


def unpack_archive(archive_path: Path, destination: Path) -> None:
    print_status("extract", f"Extracting {archive_path.name}")
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as zip_file:
            zip_file.extractall(destination)
        return
    if archive_path.name.endswith(".tar.gz"):
        with tarfile.open(archive_path, "r:gz") as tar_file:
            tar_file.extractall(destination)
        return
    raise RuntimeError(f"Unsupported archive format: {archive_path.name}")


def fetch_json(url: str) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "sllms-framework-bootstrap/1.0",
            "Accept": "application/vnd.github+json",
        },
    )
    with urlopen(request) as response:
        return json.load(response)


def download_file(url: str, destination: Path, label: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    print_status("download", f"{label} -> {destination.name}")
    request = Request(url, headers={"User-Agent": "sllms-framework-bootstrap/1.0"})
    with urlopen(request) as response, destination.open("wb") as handle:
        total = int(response.headers.get("Content-Length", "0"))
        downloaded = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
            downloaded += len(chunk)
            render_progress(label, downloaded, total)
    print()


def render_progress(label: str, downloaded: int, total: int) -> None:
    downloaded_mb = downloaded / (1024 * 1024)
    if total > 0:
        total_mb = total / (1024 * 1024)
        percent = min(downloaded / total, 1.0) * 100
        print(f"\r[{label}] {percent:6.2f}% {downloaded_mb:8.1f} / {total_mb:8.1f} MB", end="", flush=True)
    else:
        print(f"\r[{label}] {downloaded_mb:8.1f} MB", end="", flush=True)


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command '{name}' is not available on PATH.")


def run_command(command: list[str], cwd: Path) -> None:
    print(f"$ {' '.join(command)}")
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        print(line.rstrip())
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"Command failed with exit code {return_code}: {' '.join(command)}")


def find_file(root: Path, file_name: str) -> Path:
    matches = sorted(root.rglob(file_name))
    if not matches:
        raise RuntimeError(f"Could not find '{file_name}' under {root}")
    return matches[0]


def install_runtime_bundle(source_dir: Path, destination_dir: Path, backend_name: str) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)
    patterns = ["*.exe", "*.dll"] if os.name == "nt" else ["*"]
    copied = 0
    for pattern in patterns:
        for path in source_dir.glob(pattern):
            if path.is_dir():
                continue
            shutil.copy2(path, destination_dir / path.name)
            copied += 1
            if os.name != "nt" and os.access(path, os.X_OK):
                (destination_dir / path.name).chmod(0o755)
    if copied == 0:
        raise RuntimeError(f"No runtime files were copied for {backend_name} from {source_dir}")


def print_status(stage: str, message: str) -> None:
    print(f"[{stage.upper()}] {message}")


if __name__ == "__main__":
    raise SystemExit(main())
