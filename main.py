"""Main entry point."""

from earwax import Game, ThreadedPromise
from pyglet.window import Window

from inquisitive import sounds
from inquisitive.open_trivia_db import QuestionDifficulties, QuestionFactory
from inquisitive.quiz_level import QuizLevel

game: Game = Game(name='Inquisitive')
factory: QuestionFactory = QuestionFactory()

easy_level: QuizLevel
medium_level: QuizLevel
hard_level: QuizLevel

promise: ThreadedPromise = ThreadedPromise(game.thread_pool)


@promise.register_func
def load() -> None:
    global easy_level, medium_level, hard_level
    game.output('Loading...', interrupt=True)
    sounds.load_sounds()
    factory.generate_token()
    easy_level = QuizLevel(
        game, factory.get_questions(difficulty=QuestionDifficulties.easy),
        sounds.music.paths['easy_level.mp3']
    )
    medium_level = QuizLevel(
        game, factory.get_questions(difficulty=QuestionDifficulties.medium),
        sounds.music.paths['medium_level.mp3']
    )
    hard_level = QuizLevel(
        game, factory.get_questions(difficulty=QuestionDifficulties.hard),
        sounds.music.paths['hard_level.mp3']
    )


@promise.event
def on_error(e: Exception) -> None:
    game.output('There was an error loading sounds.')


@promise.event
def on_done(value: None) -> None:
    game.interface_sound_player.generator.destroy()
    game.interface_sound_player.generator = None
    game.push_level(easy_level)


@game.event
def before_run() -> None:
    promise.run()
    game.interface_sound_player.play_path(sounds.loading_sound)


window: Window = Window(caption=game.name)

if __name__ == '__main__':
    game.run(window)
