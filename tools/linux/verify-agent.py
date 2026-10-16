#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise the native agent in disposable storage; never launch a browser."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument("agent", type=Path)
parser.add_argument("--persona", type=Path, required=True)
args = parser.parse_args()
agent = args.agent.resolve()
persona_path = args.persona.resolve()
persona = json.loads(persona_path.read_text())
assert persona["os"]["name"] == "Linux", "A native Linux persona is required"

with tempfile.TemporaryDirectory(prefix="fury-linux-qa-") as tmp:
    root = Path(tmp)
    own_personas = root / "personas"
    own_personas.mkdir()
    shutil.copyfile(persona_path, own_personas / "linux.json")
    env = dict(os.environ, FURY_HOME=str(root / "fury"),
               FURY_SOCKET=str(root / "agent.sock"), FURY_PERSONAS=str(own_personas))
    process = None
    log = (root / "agent.log").open("w")

    def start():
        child = subprocess.Popen([str(agent), "serve"], env=env, stdout=log, stderr=log)
        for _ in range(100):
            assert child.poll() is None, "Agent exited before IPC became ready"
            if (root / "agent.sock").exists():
                try:
                    with socket.socket(socket.AF_UNIX) as probe:
                        probe.connect(str(root / "agent.sock"))
                    return child
                except OSError:
                    pass
            time.sleep(0.1)
        child.terminate()
        child.wait(timeout=10)
        raise TimeoutError("Agent did not create its IPC socket")

    def call(method, params=None):
        with socket.socket(socket.AF_UNIX) as sock:
            sock.settimeout(15)
            sock.connect(str(root / "agent.sock"))
            sock.sendall((json.dumps({"id": 1, "method": method,
                                     "params": params or {}}) + "\n").encode())
            reply = json.loads(sock.makefile("rb").readline())
        assert "err" not in reply, f"{method} failed: {reply.get('err')}"
        return reply["ok"]

    def stop(child):
        child.terminate()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=10)

    try:
        process = start()
        assert call("vault.status")["available"], "Unlock a Secret Service keyring for this test session"
        assert call("profiles.list") == [], "Test storage was not empty"
        password = secrets.token_hex(16)
        proxy_id = call("proxies.upsert", {
            "id": "", "name": "Linux QA", "kind": "http", "host": "127.0.0.1",
            "port": 9, "username": "qa", "password": password,
        })["id"]
        profile_id = call("profiles.upsert", {
            "id": "", "name": "Linux QA", "notes": "Disposable test",
            "tags": ["qa"], "persona_id": persona["id"], "fp_seed": 17,
            "proxy_id": proxy_id, "start_urls": [],
        })["id"]
        assert call("profiles.list")[0]["persona_id"] == persona["id"]
        call("profiles.delete", {"id": profile_id})
        assert call("profiles.list") == []
        call("profiles.restore", {"id": profile_id})
        assert call("profiles.list")[0]["id"] == profile_id
        stop(process)
        process = None
        # Neither the database nor its WAL may contain the supplied secret.
        for file in (root / "fury").glob("fury.db*"):
            assert password.encode() not in file.read_bytes(), "A proxy secret reached disk in plaintext"
        process = start()
        restored = call("proxies.list")
        assert restored[0]["password"] == password, "Secret did not survive an agent restart"
        assert call("profiles.list")[0]["id"] == profile_id
        assert (root / "agent.sock").stat().st_mode & 0o777 == 0o600
        print(json.dumps({"ok": True, "checks": ["private IPC", "Linux profile create/trash/restore",
              "encrypted SQLite secrets", "keyring decryption after restart"]}))
    finally:
        if process is not None:
            stop(process)
        log.close()
