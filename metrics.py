"""Prometheus metrics for DNS Incident Timer.

Shared metrics module to avoid circular imports between dns_counter and web_server.
"""
import time

try:
    from prometheus_client import Counter, Gauge

    RESET_COUNTER = Counter(
        'dnsfail_resets_total',
        'Total number of timer resets',
        ['source']  # 'button' or 'web'
    )
    SECONDS_SINCE_RESET = Gauge(
        'dnsfail_seconds_since_reset',
        'Seconds elapsed since last reset'
    )
    UPTIME_SECONDS = Gauge(
        'dnsfail_uptime_seconds',
        'Seconds since the application started'
    )
    AUDIO_PLAYBACK_ERRORS = Counter(
        'dnsfail_audio_errors_total',
        'Total number of audio playback errors'
    )
    APP_START_TIME = time.time()
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    RESET_COUNTER = None
    SECONDS_SINCE_RESET = None
    UPTIME_SECONDS = None
    AUDIO_PLAYBACK_ERRORS = None
    APP_START_TIME = time.time()
