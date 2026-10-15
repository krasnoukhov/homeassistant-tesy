"""Register the card as a Lovelace dashboard resource.

In storage mode (the default) the integration keeps one resource for its card
in Settings → Dashboards → Resources, with the card's content hash in the URL
(``/tesy_static/tesy-boiler-card.js?v=<hash>``): nothing to add by hand, and an
updated card gets a new URL, so browsers load it instead of a cached copy.
In YAML mode resources cannot be changed from an integration; the card is
added to every page with ``add_extra_js_url`` instead.

``plan_resource`` holds the decision and has no Home Assistant dependencies so
it can be unit tested alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

CARD_FILE = "tesy-boiler-card.js"


@dataclass
class ResourcePlan:
    """What to change in the resource list."""

    create: bool = False
    update_id: str | None = None
    delete_ids: list[str] = field(default_factory=list)
    # Hand-made resources for the same card file at another path (an old copy
    # in /local, say): left alone, but worth a warning.
    foreign_urls: list[str] = field(default_factory=list)

    @property
    def changes(self) -> bool:
        """Return True if the resource list has to change."""
        return self.create or self.update_id is not None or bool(self.delete_ids)


def _path(url: Any) -> str:
    return urlsplit(str(url or "")).path


def plan_resource(items: list[dict[str, Any]], url: str) -> ResourcePlan:
    """Plan the changes so the resources hold exactly one entry for url."""
    plan = ResourcePlan()
    own_path = _path(url)
    own = [item for item in items if _path(item.get("url")) == own_path]
    plan.foreign_urls = [
        str(item.get("url"))
        for item in items
        if _path(item.get("url")) != own_path
        and _path(item.get("url")).endswith("/" + CARD_FILE)
    ]
    if not own:
        plan.create = True
        return plan
    keep, *extra = own
    plan.delete_ids = [str(item["id"]) for item in extra if "id" in item]
    if keep.get("url") != url or keep.get("type", "module") != "module":
        plan.update_id = str(keep["id"])
    return plan


def plan_removal(items: list[dict[str, Any]], url: str) -> list[str]:
    """Ids of the integration's own resources (to remove with the integration)."""
    own_path = _path(url)
    return [
        str(item["id"])
        for item in items
        if "id" in item and _path(item.get("url")) == own_path
    ]
