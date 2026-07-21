"""HTTP server for MathEvidence Agent API v1 (stdlib only)."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# Ensure repo root is importable when run as `python -m agent.api.server`.
_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from agent.api import service  # noqa: E402


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: dict[str, Any]) -> None:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(payload)


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    if length > 4_194_304:
        raise ValueError("request body too large")
    raw = handler.rfile.read(length)
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object")
    return data


class AgentAPIHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"{self.address_string()} - {fmt % args}\n")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)
        try:
            if path in ("/v1/health", "/health"):
                return _json_response(self, 200, service.health())
            if path == "/v1/operations":
                return _json_response(self, 200, service.op_list_operations())
            if path == "/v1/capabilities":
                status = qs.get("status", [None])[0]
                domain = qs.get("domain", [None])[0]
                return _json_response(
                    self,
                    200,
                    service.op_list_capabilities(status=status, domain=domain),
                )
            return _json_response(
                self,
                404,
                {
                    "error": {
                        "code": "backend_unsupported",
                        "message": f"unknown path: {path}",
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001
            return _json_response(
                self,
                500,
                {"error": {"code": "backend_crash", "message": str(exc)}},
            )

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        try:
            body = _read_json(self)
            if path == "/v1/check-support":
                return _json_response(self, 200, service.op_check_support(body))
            if path == "/v1/compute":
                return _json_response(self, 200, service.op_compute_evidence(body))
            if path == "/v1/bundles/open":
                return _json_response(self, 200, service.op_open_bundle(body))
            if path == "/v1/bundles/inspect":
                return _json_response(self, 200, service.op_inspect_bundle(body))
            if path == "/v1/bundles/replay":
                return _json_response(self, 200, service.op_replay_bundle(body))
            if path == "/v1/ttp/build-proof-plan":
                return _json_response(self, 200, service.op_build_proof_plan(body))
            if path == "/v1/ttp/reconstruct-plan":
                return _json_response(self, 200, service.op_reconstruct_plan(body))
            if path == "/v1/hypothesis/propose-conditions":
                return _json_response(self, 200, service.op_propose_conditions(body))
            if path == "/v1/hypothesis/prove-sufficient":
                return _json_response(self, 200, service.op_prove_sufficient(body))
            if path == "/v1/hypothesis/delete":
                return _json_response(self, 200, service.op_delete_hypothesis(body))
            if path == "/v1/hypothesis/find-counterexample":
                return _json_response(self, 200, service.op_find_counterexample(body))
            if path == "/v1/hypothesis/verify-counterexample":
                return _json_response(self, 200, service.op_verify_counterexample(body))
            if path == "/v1/hypothesis/build-lattice":
                return _json_response(self, 200, service.op_build_condition_lattice(body))
            if path == "/v1/conjecture/campaign":
                return _json_response(self, 200, service.op_conjecture_campaign(body))
            return _json_response(
                self,
                404,
                {
                    "error": {
                        "code": "backend_unsupported",
                        "message": f"unknown path: {path}",
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001
            return _json_response(
                self,
                400,
                {"error": {"code": "malformed_evidence", "message": str(exc)}},
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MathEvidence Agent API v1")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), AgentAPIHandler)
    print(
        f"MathEvidence Agent API listening on http://{args.host}:{args.port}",
        flush=True,
    )
    print("OpenAPI: agent/api/openapi.yaml", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutdown", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
