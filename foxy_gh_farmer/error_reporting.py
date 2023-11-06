import sentry_sdk
from sentry_sdk import Hub
from sentry_sdk.integrations.logging import LoggingIntegration

from foxy_gh_farmer.foundation.sentry.filter_sentry_events import filter_sentry_events
from foxy_gh_farmer.version import version


def init_sentry():
    sentry_sdk.init(
        dsn="https://dd8679dd489b6fe597c1c30bfdecc5b4@o236153.ingest.sentry.io/4506149108252672",
        release=f"foxy-gh-farmer@{version}",
        integrations=[
            LoggingIntegration(event_level=None),
        ],
        before_send=filter_sentry_events,
    )


def close_sentry():
    client = Hub.current.client
    if client is not None:
        client.close(timeout=2.0)
