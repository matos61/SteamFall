# steamfall/game/story.py
class StoryState:
    def __init__(self):
        self.flags = set()

    def has(self, flag: str) -> bool:
        return flag in self.flags

    def set(self, flag: str):
        self.flags.add(flag)

    def clear(self, flag: str):
        self.flags.discard(flag)
