from abc import ABC


class BaseApp(ABC):
    app_name: str = ""
    app_module: str = ""
    app_path: str = ""
    display_name: str = ""
    engine_class = None
    icon_name: str = ""
