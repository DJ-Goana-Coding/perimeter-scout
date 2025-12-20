class ModuleInterface:
    async def get_intel(self):
        return None

    async def get_status(self):
        return None

    async def get_recommendations(self):
        return None

    def capabilities(self):
        return []

    def version(self):
        return "1.0.0"
