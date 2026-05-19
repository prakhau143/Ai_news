"""
Background agent loop. Runs forever in a daemon thread.
Started automatically by AgentConfig.ready().
"""
import threading
import time
from datetime import datetime

AGENT_STATUS = {
    'running': False,
    'last_run': None,
    'last_count': 0,
    'cycles': 0,
    'errors': 0,
}

_agent_thread = None
_stop_event = threading.Event()

FETCH_INTERVAL = 60   # seconds between fetch cycles


def agent_loop():
    """Main loop — fetches news every FETCH_INTERVAL seconds."""
    AGENT_STATUS['running'] = True
    print(f"[{_ts()}] Agent started — fetching every {FETCH_INTERVAL}s")

    while not _stop_event.is_set():
        try:
            from apps.agent.fetcher import run_fetch_cycle
            count = run_fetch_cycle()
            AGENT_STATUS['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            AGENT_STATUS['last_count'] = count
            AGENT_STATUS['cycles'] += 1
            print(f"[{_ts()}] Cycle #{AGENT_STATUS['cycles']} complete — {count} new articles")
        except Exception as exc:
            AGENT_STATUS['errors'] += 1
            print(f"[{_ts()}] Agent error: {exc}")

        _stop_event.wait(FETCH_INTERVAL)

    AGENT_STATUS['running'] = False
    print(f"[{_ts()}] Agent stopped")


def start_agent():
    global _agent_thread
    if _agent_thread and _agent_thread.is_alive():
        return  # already running

    _stop_event.clear()
    _agent_thread = threading.Thread(target=agent_loop, name="AINewsAgent", daemon=True)
    _agent_thread.start()


def _ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
