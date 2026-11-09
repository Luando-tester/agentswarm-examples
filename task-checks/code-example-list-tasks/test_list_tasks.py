"""Pinned offline acceptance check; candidate code never sees fixture files."""
import contextlib
import json
import os
from pathlib import Path
import secrets
import selectors
import shutil
import subprocess
import tempfile
import time

import pytest

HERE = Path(__file__).resolve().parent
IMAGES = {
    "php": "php:8.4-cli-bookworm@sha256:b3e907a1108629c562c4bb313ce3449e34d49991f6bb2487913f6146f47200fe",
    "dart": "dart:stable-sdk@sha256:854f3c50b1cbd4a5a54c9fa67d4f5b6702ac49b4a26d21a80e7712a72528b215",
    "go": "golang:1.23@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0",
    "typescript": "node:22@sha256:7702d8aa4d5910871692af4480eb3ba86f23047a6417a44d857d06c95d060d3f",
    "rust": "rust:1.89@sha256:57407b378b2b6e07b48a6135a20c87cc22ea6e249c0acf6cb1833ead3cf116e9",
    "python": "python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b",
    "ruby": "ruby:3.3-bookworm@sha256:ae098d019fd2995e6cb82e16a87529348ba26a7c83ad6189937decc2846b0730",
}
BUILD = {
    "php": ["php", "-l", "example.php"],
    "dart": ["dart", "compile", "exe", "example.dart", "-o", "/work/list-tasks"],
    "go": ["go", "build", "-o", "/work/list-tasks", "."],
    # Node 22 executes erasable TypeScript directly; no npm install or build.
    "typescript": ["node", "--version"],
    "rust": ["cargo", "build", "--offline", "--locked", "--release"],
    "python": ["python3", "--version"],
    "ruby": ["ruby", "--version"],
}
RUN = {
    "php": ["php", "example.php"],
    "dart": ["/work/list-tasks"],
    "go": ["/work/list-tasks"],
    "typescript": ["node", "--experimental-strip-types", "example.ts"],
    "rust": ["/work/target/release/list-tasks"],
    "python": ["python3", "example.py"],
    "ruby": ["ruby", "example.rb"],
}


def command(args, *, stop_container=None):
    """Bound host capture as well as container resources; kill on overflow."""
    output = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + 180
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        with selectors.DefaultSelector() as streams:
            streams.register(process.stdout, selectors.EVENT_READ, "stdout")
            streams.register(process.stderr, selectors.EVENT_READ, "stderr")
            while streams.get_map():
                assert time.monotonic() < deadline, "Command exceeded 180 second timeout"
                for key, _ in streams.select(timeout=0.1):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        streams.unregister(key.fileobj)
                        continue
                    output[key.data].extend(chunk)
                    assert sum(map(len, output.values())) <= 1024 * 1024, "Command exceeded output limit (1 MiB)"
        remaining = max(0.01, deadline - time.monotonic())
        process.wait(timeout=remaining)
    except BaseException:
        process.kill()
        process.wait(timeout=10)
        if stop_container:
            subprocess.run(["docker", "rm", "--force", stop_container],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        raise
    finally:
        process.stdout.close()
        process.stderr.close()
    return subprocess.CompletedProcess(args, process.returncode,
                                       output["stdout"].decode("utf-8", errors="replace"),
                                       output["stderr"].decode("utf-8", errors="replace"))


def docker(*args):
    result = command(["docker", *args])
    assert result.returncode == 0, f"Docker command failed: {result.stdout}\n{result.stderr}"
    return result.stdout.strip()


@contextlib.contextmanager
def container(name, args):
    try:
        docker("run", "--detach", "--name", name, *args)
        yield name
    finally:
        subprocess.run(["docker", "rm", "--force", name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)


@contextlib.contextmanager
def build_volume(name):
    try:
        docker("volume", "create", "--driver", "local", "--opt", "type=tmpfs",
               "--opt", "device=tmpfs", "--opt", "o=size=768m,mode=1777", name)
        yield name
    finally:
        subprocess.run(["docker", "volume", "rm", name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)


def cases():
    """Mutate a recorded public response: ids, text, order and open count vary."""
    recorded = json.loads((HERE / "feed.json").read_text())
    result = {}
    scenarios = ["mixed-one", "mixed-two", "closed", "empty", "http-error", "http-client", "http-server",
                 "bad-json", "bad-json-trailing", "bad-json-multiple"]
    secrets.SystemRandom().shuffle(scenarios)
    for scenario in scenarios:
        payload = json.loads(json.dumps(recorded))
        items = []
        count = 1 + secrets.randbelow(4)
        for index in range(count + 2):
            item = dict(recorded["items"][index % len(recorded["items"])])
            item.update(id=secrets.token_hex(16), title=f'{secrets.token_hex(6)} — café 東京 🐝 "quoted"',
                        status="open" if index < count else "closed")
            items.append(item)
        secrets.SystemRandom().shuffle(items)
        if scenario == "closed":
            for item in items:
                item["status"] = "closed"
        if scenario == "empty":
            items = []
        payload["items"] = items
        payload["nextCursor"] = None
        body = json.dumps(payload, ensure_ascii=False)
        if scenario == "bad-json":
            body = '{"items": ['
        elif scenario == "bad-json-trailing":
            body += " trailing garbage"
        elif scenario == "bad-json-multiple":
            body += '\n{"items": []}'
        status = {"http-error": 500, "http-client": secrets.choice([400, 403, 404, 429]),
                  "http-server": secrets.choice([502, 503, 504])}.get(scenario, 200)
        result["/" + secrets.token_hex(12)] = {
            "scenario": scenario, "status": status, "body": body, "items": items,
        }
    return result


@pytest.mark.parametrize("language", [os.environ.get("EXAMPLE_LANGUAGE", "go")])
def test_list_tasks(language):
    assert language in IMAGES, "EXAMPLE_LANGUAGE must be one of " + ", ".join(IMAGES)
    assert os.environ.get("BOUNTY_REPO"), "Export BOUNTY_REPO to the candidate checkout"
    source = Path(os.environ["BOUNTY_REPO"]).resolve() / language
    assert source.is_dir(), f"Missing example directory: {source}"
    assert not source.is_symlink(), "Example directory must not be a symlink"
    assert shutil.which("docker"), "Docker is required"
    image = IMAGES[language]
    fixture_image = IMAGES['python'] if language in ('php', 'dart') else image
    if fixture_image != image:
        docker("image", "inspect", fixture_image)
    docker("image", "inspect", image)  # No implicit network pull during checks.
    fixtures = cases()
    token = secrets.token_hex(8)
    fixture_name, builder_name = f"list-fixture-{token}", f"list-build-{token}"
    with tempfile.TemporaryDirectory(prefix="list-tasks-") as temporary:
        snapshot = Path(temporary) / "source"
        assert not any(p.is_symlink() for p in source.rglob("*")), "Example must not contain symlinks"
        shutil.copytree(source, snapshot, ignore=shutil.ignore_patterns("target", "node_modules", ".git"))
        snapshot.chmod(0o755)
        Path(temporary).chmod(0o755)
        fixture_path = Path(temporary) / "fixtures.json"
        fixture_path.write_text(json.dumps(fixtures))
        common = ["--pull", "never", "--read-only", "--cap-drop", "ALL",
                  "--security-opt", "no-new-privileges", "--pids-limit", "256",
                  "--memory", "1g", "--cpus", "2"]
        # The candidate shares only the fixture's loopback namespace;
        # its filesystem, processes and environment remain separate.
        fixture_args = [*common, "--log-driver", "local", "--log-opt", "max-size=1m",
                        "--log-opt", "max-file=1", "--log-opt", "compress=false"]
        # Keep the tmpfs volume mounted in the trusted fixture container while
        # builders/runtimes come and go; otherwise an unused tmpfs loses data.
        with build_volume(f"list-work-{token}") as volume, container(fixture_name, [*fixture_args, "--network", "none",
                       "--mount", f"type=volume,src={volume},dst=/build-volume,readonly,volume-nocopy",
                       "--mount", f"type=bind,src={fixture_path},dst=/fixtures.json,readonly",
                       "--mount", f"type=bind,src={HERE / 'fixture_server.py'},dst=/fixture_server.py,readonly",
                       "--user", f"{os.getuid()}:{os.getgid()}", fixture_image,
                       "python3", "-u", "/fixture_server.py"]):
            for _ in range(100):
                logs = docker("logs", fixture_name)
                if "READY" in logs:
                    break
                time.sleep(0.05)
            assert "READY" in logs, f"Fixture did not start: {logs}"
            work_mount = f"type=volume,src={volume},dst=/work,volume-nocopy"
            with container(builder_name, [*common, "--log-driver", "none", "--network", "none",
                           "--user", f"{os.getuid()}:{os.getgid()}",
                           "--mount", work_mount, "--tmpfs", "/tmp:rw,exec,mode=1777,size=768m",
                           "--mount", f"type=bind,src={snapshot},dst=/source,readonly",
                           "--env", "HOME=/tmp", "--env", "GOCACHE=/tmp/go-cache",
                           "--env", "GOPROXY=off", "--env", "GOTOOLCHAIN=local",
                           "--env", "GOMAXPROCS=2", "--env", "CARGO_HOME=/usr/local/cargo",
                           "--workdir", "/work", image, "sleep", "infinity"]):
                docker("exec", builder_name, "sh", "-c", "cp -R /source/. /work/")
                built = command(["docker", "exec", builder_name, *BUILD[language]], stop_container=builder_name)
                assert built.returncode == 0, f"Build failed:\n{built.stdout}\n{built.stderr}"
            # A fresh runtime per case gets the build tree read-only and private
            # tmpfs. No writable state or background process survives a case.
            ordered_cases = list(fixtures.items())
            for index, (prefix, case) in enumerate(ordered_cases + list(reversed(ordered_cases))):
                base = f"http://127.0.0.1:8765{prefix}"
                configured_base = base + ("/" if case["scenario"] == "mixed-two" else "")
                runner_name = f"list-run-{token}-{index}"
                execution = command(["docker", "run", "--rm", "--name", runner_name, *common, "--log-driver", "none",
                                     "--network", f"container:{fixture_name}",
                                     "--user", f"{os.getuid()}:{os.getgid()}",
                                     "--mount", work_mount + ",readonly",
                                     "--tmpfs", "/tmp:rw,exec,mode=1777,size=128m",
                                     "--env", "HOME=/tmp", "--env", f"AGENTSWARM_BASE_URL={configured_base}",
                                     "--workdir", "/work", image, *RUN[language]], stop_container=runner_name)
                label = f"{language}/{case['scenario']}"
                if case["status"] != 200 or case["scenario"].startswith("bad-json"):
                    assert execution.returncode != 0, f"{label}: must exit nonzero"
                    assert execution.stdout == "", f"{label}: no task output on failure"
                    diagnostic = execution.stderr.lower()
                    markers = ("http", str(case["status"])) if case["status"] != 200 else ("json", "parse", "decode", "syntax")
                    assert any(word in diagnostic for word in markers), f"{label}: clear stderr diagnostic required: {execution.stderr!r}"
                else:
                    expected = "".join(f"{item['id']}\t{item['title']}\t{base}/p/{item['id']}\n"
                                       for item in case["items"] if item["status"] == "open")
                    assert execution.returncode == 0, f"{label}: {execution.stderr}"
                    assert execution.stdout == expected, f"{label}: expected {expected!r}; got {execution.stdout!r}"
            logs = docker("logs", fixture_name)
            requests = [json.loads(line[8:]) for line in logs.splitlines() if line.startswith("REQUEST ")]
            expected_paths = {prefix + "/api/feed?type=task" for prefix in fixtures}
            assert {r["path"] for r in requests} == expected_paths, f"Wrong or missing feed requests: {requests}"
            assert all(r["method"] == "GET" and not r["authorization"] for r in requests), "Only key-free GET requests allowed"
