import importlib.resources
import pygame as pg


def load(module_path, name):
    return importlib.resources.path(module_path, name)


def import_image(asset_name: str):
    with load("dreamcenter.assets.gfx", asset_name) as resource:
        return pg.image.load(resource).convert_alpha()


def import_sound(asset_name: str):
    with load("dreamcenter.assets.audio", asset_name) as resource:
        return pg.mixer.Sound(resource)


def import_level(asset_name: str):
    with load("dreamcenter.assets.levels", asset_name) as resource:
        return resource.open()