"""Core utilities and constants."""

import re


CORE_EVENT_PREFIX = "acapy::CORE::"
STARTUP_EVENT_TOPIC = CORE_EVENT_PREFIX + "STARTUP"
STARTUP_EVENT_PATTERN = re.compile(f"^{STARTUP_EVENT_TOPIC}?$")
SHUTDOWN_EVENT_TOPIC = CORE_EVENT_PREFIX + "SHUTDOWN"
SHUTDOWN_EVENT_PATTERN = re.compile(f"^{SHUTDOWN_EVENT_TOPIC}?$")
