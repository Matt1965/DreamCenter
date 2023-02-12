from dataclasses import dataclass
from dreamcenter.sprites import SpriteManager, Text, Menu


@dataclass
class TextGroup:
    sprite_manager: SpriteManager
    text_sprites = []
    menu = None

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
        self.create_text("Fragments: 0", "money", size=50, position=[1431, 25])
        self.create_text("Damage: 0", "damage", size=30, position=[-325, 280])
        self.create_text("Attack Speed: 0", "aspeed", size=30, position=[-303, 330])
        self.create_text("Move Speed: 0", "speed", size=30, position=[-312, 380])
        self.create_text("Range: 0", "range", size=30, position=[-329, 430])
        self.create_text("Shot Speed: 0", "sspeed", size=30, position=[-315, 480])
        self.create_text("Luck: 0", "luck", size=30, position=[-345, 530])

    def toggle_stat_display(self, toggle=bool):
        for text in self.text_sprites:
            if text.text_type in ("damage", "aspeed", "speed", "range", "sspeed", "luck"):
                print(text)
                if toggle:
                    text.position[0] -= 500
                    self.menu.position = [-500, 220]
                else:
                    text.position[0] += 500
                    self.menu.position = [80, 220]
                self.menu.move(self.menu.position, False)
            text.move(text.position)
