import pygame as pg
from dataclasses import dataclass


@dataclass
class SpecialEffects:
    screen = pg.Surface
    image_list = []

    def screen_sync(self, screen):
        self.screen = screen

    def draw(self):
        for image in self.image_list:
            match image["type"]:
                case "polygon":
                    pg.draw.polygon(self.screen, image["color"], image["points"], image["width"])
                case "circle":
                    pg.draw.circle(self.screen, image["color"], image["center"], image["radius"])
                case "line":
                    pg.draw.line(self.screen, image["color"], image["start"], image["end"])
                case "image":
                    self.screen.blit(image["image"], image["top_left"])
            image["duration"] -= 1

        for image in self.image_list.copy():
            if image["duration"] <= 0:
                self.image_list.remove(image)

    def draw_polygon(self, duration, color, points, width):
        self.image_list.append({
            "type": "polygon",
            "duration": duration,
            "color": color,
            "points": points,
            "width": width,
        })

    def draw_circle(self, duration, color, center, radius):
        self.image_list.append({
            "type": "circle",
            "duration": duration,
            "color": color,
            "center": center,
            "radius": radius
        })

    def draw_line(self, duration, color, start, end):
        self.image_list.append({
            "type": "line",
            "duration": duration,
            "color": color,
            "start": start,
            "end": end
        })

    def draw_image(self, duration, top_left, image):
        self.image_list.append({
            "type": "image",
            "duration": duration,
            "top_left": top_left,
            "image": image,
        })