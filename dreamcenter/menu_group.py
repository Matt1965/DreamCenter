from pygame import Vector2 as Vector
from dataclasses import dataclass, field
from typing import Optional, List
from dreamcenter.sprites import Text


@dataclass
class MenuGroup:
    render_position: Vector = Vector(0, 0)
    selected_color: str = "red"
    not_selected_color: str = "black"
    selected: Optional[int] = 0
    items: List[Text] = field(default_factory=list)

    def set_selected(self, index):
        """
        Sets the selected item to `index`. All menu group items
        are re-rendered and their selected colors changed to match the
        new index.
        """
        for idx, menu_item in enumerate(self.items):
            if idx == index:
                menu_item.color = self.selected_color
                self.selected = idx
            else:
                menu_item.color = self.not_selected_color
            menu_item.render_text()

    def move(self, direction):
        """
        Moves the selection in `direction`, which is either a
        positive or negative number, indicating down or up, respectively.
        """
        if self.selected is None:
            self.selected = 0
        self.selected += direction
        self.selected %= len(self.items)
        self.set_selected(self.selected)

    def forward(self):
        """
        Moves the selected menu item forward one position
        """
        self.move(1)

    def backward(self):
        """
        Moves the selected menu item backward one position
        """
        self.move(-1)

    def add_menu_item(self, *menu_items):
        """
        Adds `menu_items` to the end of the menu items list.
        """
        self.items.extend(menu_items)

    def get_menu_item_position(self):
        """
        Calculates a menu item's *center* position on the screen,
        taking into account all the other menu items' font sizes and
        line height spacing.
        """
        offset = Vector(
            0,
            sum(
                menu_item.font.get_height() + menu_item.font.get_linesize()
                for menu_item in self.items
            ),
        )
        return self.render_position + offset

    def clear(self):
        self.items.clear()

    def add(self, text, size, action):
        sprite = Text(
            groups=[],
            color=self.not_selected_color,
            text=text,
            size=size,
            action=action,
        )
        self.add_menu_item(sprite)
        v = self.get_menu_item_position()
        sprite.move(v)
        # Set the selected item to the top-most item.
        self.move(0)

    def execute(self):
        """
        Executes the action associated with the selected menu
        item. Requires that a callable is associated with the menu
        item's `action`.
        """
        assert self.selected is not None, "No menu item is selected"
        menu = self.items[self.selected]
        assert callable(
            menu.action
        ), f"Menu item {menu} does not have a callable action"
        menu.action()