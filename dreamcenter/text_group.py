from dataclasses import dataclass
from dreamcenter.sprites import SpriteManager, Text


@dataclass
class TextGroup:
    sprite_manager: SpriteManager
    text_sprites = []

    def create_text(self, text, text_type, position, size=15, font=None, color=(0, 0, 0)):
        sprite = Text(
            groups=[],
            text_type=text_type,
            position=position,
            color=color,
            text=text,
            size=size,
            font=font,
        )
        self.text_sprites.append(sprite)

    def define_initial_texts(self):
        self.create_text("Fragments: 0", "money", size=50, position=(1431, 25))
