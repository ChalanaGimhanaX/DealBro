from typing import Dict, Type

from app.adapters.base import SourceAdapter
from app.adapters.hostingdiscussion import HostingDiscussionAdapter
from app.adapters.lowendtalk import LowEndTalkAdapter
from app.adapters.lowendbox import LowEndBoxAdapter
from app.adapters.webhostingtalk import WebHostingTalkAdapter
from app.adapters.serverhunter import ServerHunterAdapter


def get_adapter_class(source_name: str) -> Type[SourceAdapter]:
    """Get adapter class for a given source name."""
    adapters: Dict[str, Type[SourceAdapter]] = {
        "hostingdiscussion": HostingDiscussionAdapter,
        "lowendtalk": LowEndTalkAdapter,
        "lowendbox": LowEndBoxAdapter,
        "webhostingtalk": WebHostingTalkAdapter,
        "serverhunter": ServerHunterAdapter,
    }
    
    return adapters.get(source_name)


__all__ = [
    "SourceAdapter",
    "HostingDiscussionAdapter",
    "LowEndTalkAdapter",
    "LowEndBoxAdapter",
    "WebHostingTalkAdapter",
    "ServerHunterAdapter",
    "get_adapter_class",
]
