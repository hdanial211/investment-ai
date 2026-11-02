"""Loopback-only, authenticated HTTP/JSON service launcher."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from investment_ai.learning.common import canonical, contract_hash
from investment_ai.services.inference import InferenceWorker
from investment_ai.registry.legacy import Registry
from investment_ai.learning.research import ResearchWorker
from investment_ai.services.multitf import MultiTfWorker
from investment_ai.learning.multitf_scheduler import Scheduler

MAX_BODY = 2 * 1024 * 1024


def make_server(host, port, role, data_dir, token, trusted_paths=(), *, scheduler=True, enable_training=False, enable_multitf=False):
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("worker must bind loopback")
    if not token or len(token) < 24:
        raise ValueError("worker token must contain at least 24 characters")
    root = Path(data_dir).resolve()
    if role not in ("inference", "research") or (enable_training and role != "research"):
        raise ValueError("training may only be enabled on the research worker")
    worker = InferenceWorker(Registry(root / "registry"), trusted_paths) if role == "inference" else ResearchWorker(root, scheduler=scheduler and not enable_multitf, enabled=enable_training and not enable_multitf)
    v2 = MultiTfWorker(root)
    v2_schedule = Scheduler(v2, enabled=enable_training and enable_multitf, start=scheduler) if role=="research" else None

    class Handler(BaseHTTPRequestHandler):
        server_version = "InvestmentLearning/1"

        def log_message(self, *_):
            pass  # Never log Authorization, request bodies, features or secrets.

        def send_json(self, status, payload):
            try:
                body = canonical(payload)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                pass

        def authorized(self):
            supplied = self.headers.get("Authorization", "")
            if not hmac.compare_digest(supplied, "Bearer " + token):
                self.send_json(401, {"status": "UNAUTHORIZED"})
                return False
            return True

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self.send_json(200, {"status": "OK", "role": role, "feature_contract_hash": contract_hash()})
                return
            if not self.authorized():
                return
            try:
                if role == "research" and parsed.path=="/v2/progress":
                    self.send_json(200,{coin:v2.jobs(coin) for coin in ("BTC","ETH","SOL","XRP","LTC")})
                elif role == "research" and parsed.path=="/v2/comparisons":
                    self.send_json(200,v2_schedule.comparisons.pending())
                elif role == "research" and parsed.path.startswith("/v2/coins/"):
                    parts = parsed.path.strip("/").split("/")
                    coin = parts[2]
                    if len(parts)==3:
                        summary=v2.summary(coin)
                        summary["training"]["enabled"]=bool(v2_schedule and v2_schedule.enabled)
                        self.send_json(200, summary)
                    elif len(parts)==5 and parts[3]=="experiences":
                        modes = parse_qs(parsed.query).get("mode", ["live", "paper", "shadow"])
                        result = next((r for m in modes if (r := v2.store.experience(coin,parts[4],m))),None)
                        self.send_json(200 if result else 404, result or {"status":"NOT_FOUND"})
                    else:
                        self.send_json(404,{"status":"NOT_FOUND"})
                elif role != "research":
                    self.send_json(404, {"status": "NOT_FOUND"})
                elif parsed.path == "/v1/stats":
                    self.send_json(200, worker.stats())
                elif parsed.path == "/v1/history":
                    self.send_json(200, worker.history(parse_qs(parsed.query).get("coin", [None])[0]))
                elif parsed.path == "/v1/comparisons":
                    if not enable_multitf:worker.comparisons.register_candidates()
                    self.send_json(200, {"comparisons": [] if enable_multitf else worker.comparisons.list_all()})
                elif parsed.path.startswith("/v1/jobs/"):
                    job_id = parsed.path.rsplit("/", 1)[1]
                    if not job_id or any(char not in "0123456789abcdef" for char in job_id):
                        raise ValueError("invalid job id")
                    path = root / "jobs" / (job_id + ".json")
                    self.send_json(200, json.loads(path.read_text(encoding="utf-8")))
                else:
                    self.send_json(404, {"status": "NOT_FOUND"})
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                return
            except (ValueError, OSError) as error:
                self.send_json(400, {"status": "INVALID_REQUEST", "error": str(error)})

        def do_POST(self):
            if not self.authorized():
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY:
                    raise ValueError("request body exceeds allowed size")
                payload = json.loads(self.rfile.read(length), parse_constant=lambda _: (_ for _ in ()).throw(ValueError("JSON NaN/Infinity forbidden")))
                if not isinstance(payload, dict):
                    raise ValueError("JSON object required")
                path = urlparse(self.path).path
                if role == "inference" and path == "/v2/decide":
                    self.send_json(200, v2.decide(payload))
                elif role == "research" and path == "/v2/experience":
                    self.send_json(200,v2.experience(payload))
                elif role == "research" and path == "/v2/market-evidence":
                    self.send_json(200,v2.store.quote_export(payload))
                elif role == "research" and path == "/v2/outcome":
                    self.send_json(200,v2.outcome(payload))
                elif role == "research" and path == "/v2/retrain":
                    self.send_json(202,v2_schedule.enqueue(payload.get("coin")))
                elif role == "inference" and path == "/v1/predict":
                    self.send_json(200, worker.predict(payload))
                elif role == "research" and path == "/v1/candles":
                    self.send_json(200, worker.store.append(payload))
                elif role == "research" and path == "/v1/retrain":
                    self.send_json(202, worker.enqueue(payload))
                elif role == "research" and path == "/v1/comparison-complete":
                    if set(payload) != {"run_id"}:
                        raise ValueError("only run_id accepted; paths and summary metrics are forbidden")
                    self.send_json(409, {"status":"LEGACY_PROMOTION_DISABLED"}) if enable_multitf else self.send_json(200, worker.comparisons.complete(payload["run_id"]))
                else:
                    self.send_json(404, {"status": "NOT_FOUND"})
            except (ValueError, KeyError, TypeError) as error:
                self.send_json(400, {"status": "INVALID_REQUEST", "error": str(error)})
            except Exception:
                self.send_json(500, {"status": "INTERNAL_ERROR"})

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    server.worker = worker
    server.v2_schedule = v2_schedule
    return server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=("inference", "research"), required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--token-env", default="INVESTMENT_WORKER_TOKEN")
    parser.add_argument("--trusted-joblib-path", action="append", default=[])
    parser.add_argument("--enable-training", action="store_true", help="Enable training only after migration gates pass (research role only).")
    parser.add_argument("--enable-multitf", action="store_true")
    arguments = parser.parse_args()
    server = make_server(arguments.host, arguments.port or (8001 if arguments.role == "inference" else 8002), arguments.role, arguments.data_dir, os.environ.get(arguments.token_env), arguments.trusted_joblib_path, enable_training=arguments.enable_training, enable_multitf=arguments.enable_multitf)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        if arguments.role == "research":
            server.v2_schedule.close()
            server.worker.close()
        server.server_close()


if __name__ == "__main__":
    main()
