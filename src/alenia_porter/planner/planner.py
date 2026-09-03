from alenia_porter.ffmpeg.resolver import default_resolver
from alenia_porter.ffmpeg.capabilities import default_registry

class OperationPlanner:
    def __init__(self, registry=default_registry):
        self.registry = registry

    def plan(self, intent: str, input_media, target: str, options: dict = None):
        plan = {
            "operation": intent,
            "backend": "ffmpeg",
            "input": input_media,
            "target": target,
            "stream_copy": False,
            "reencode": True,
            "warnings": []
        }
        
        # Minimal stream copy logic
        if intent == "remux" or (options and options.get("codec") == "copy"):
            plan["stream_copy"] = True
            plan["reencode"] = False

        if not self.registry.supports_format(target.split(".")[-1]):
            plan["warnings"].append(f"Format {target.split('.')[-1]} may not be fully supported")

        return plan
