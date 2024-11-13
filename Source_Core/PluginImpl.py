import sys
import os
import importlib.util
from pathlib import Path

class PluginBase:

    PluginList = []

    def __init__(self):
        self.MyCore = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.PluginList.append(cls)

    def InitPlugin(self, InCore):
        self.MyCore = InCore

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def SendDataToPlugin(self, Data):
        pass

    def SendDataToServer(self, Data):
        pass


def LoadPluginModule(Path):

    Name = os.path.split(Path)[-1].replace(".py", '')
    Spec = importlib.util.spec_from_file_location(Name, Path)
    Module = importlib.util.module_from_spec(Spec)
    sys.modules[Name] = Module
    Spec.loader.exec_module(Module)

    return Module


def LoadPlugins(InLogger):

    Path("Plugins").mkdir(parents=True, exist_ok=True)

    for File in os.listdir("Plugins"):
        if File.endswith(".py"):
            try:
                LoadPluginModule(os.getcwd() + "/Plugins/" + File)
                InLogger.LogStatus(f"PLUGIN {File} loaded")

            except Exception as e:
                InLogger.LogError(f"PLUGIN {File} failed to load: {e}")