"""Provides various sound constants."""

from pathlib import Path

from earwax import BufferDirectory

sounds_directory: Path = Path('sounds').resolve()

music_directory: Path = sounds_directory / 'music'
music: BufferDirectory

icons_directory: Path = sounds_directory / 'icons'
icons: BufferDirectory

footsteps_directory: Path = sounds_directory / 'footsteps'
footsteps: BufferDirectory

lifelines_directory: Path = sounds_directory / 'lifelines'
lifelines: BufferDirectory

players_directory: Path = sounds_directory / 'players'
players: BufferDirectory

loading_sound: Path = sounds_directory / 'loading.mp3'


def load_sounds() -> None:
    """Load all sounds and music."""
    global music, icons, footsteps, players, lifelines
    music = BufferDirectory(music_directory)
    icons = BufferDirectory(icons_directory)
    footsteps = BufferDirectory(footsteps_directory)
    players = BufferDirectory(players_directory)
    lifelines = BufferDirectory(lifelines_directory)
