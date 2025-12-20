class ModuleRegistry:
    def __init__(self):
        self.modules = {}

    def register(self, name: str, module_obj):
        self.modules[name] = module_obj

    def get(self, name: str):
        return self.modules.get(name)

    def list(self):
        return list(self.modules.keys())

    def capabilities(self):
        caps = {}
        for name, mod in self.modules.items():
            cap_fn = getattr(mod, "capabilities", lambda: [])
            ver_fn = getattr(mod, "version", lambda: "0.0.0")
            caps[name] = {
                "version": ver_fn(),
                "capabilities": cap_fn(),
            }
        return caps
