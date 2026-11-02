"""Telemetry settings for this fork: collection is off and points nowhere.

Upstream keeps this module out of git (see .gitignore in upstream) because its
copy holds the Supabase endpoint and key the PyPI package reports to. The code
still imports `telemetry_config` from here, so a clean clone needs this file.
Ours disables telemetry outright, on top of DISABLE_TELEMETRY in .mcp.json,
and gives every field the code reads an empty value, so nothing is ever sent
even if the environment variable goes missing.
"""

from dataclasses import dataclass


@dataclass
class TelemetryConfig:
    enabled: bool = False
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_bucket: str = ""
    timeout: float = 5.0
    max_prompt_length: int = 1000


telemetry_config = TelemetryConfig()
