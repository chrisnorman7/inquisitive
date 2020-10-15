"""Provides the QuizLevel class."""

from pathlib import Path
from random import shuffle
from typing import Callable, List, Optional

from attr import attrib, attrs
from earwax import Level, StaggeredPromise, Track, hat_directions
from earwax.types import StaggeredPromiseGeneratorType
from pyglet.window import key

from . import sounds
from .open_trivia_db import Answer, Question, QuestionTypes

letters: List[str] = ['A', 'B', 'C', 'D']


@attrs(auto_attribs=True)
class AnswerContainer:
    """Holds a list of possible answers, and the correct answer."""

    answers: List[Answer]
    correct: Answer = attrib()

    @correct.default
    def get_correct_answer(instance: 'AnswerContainer') -> Answer:
        return instance.answers[0]

    def __attrs_post_init__(self) -> None:
        if len(self.answers) != 2:
            shuffle(self.answers)


@attrs(auto_attribs=True)
class QuizLevel(Level):
    """A level that holds questions."""

    questions: List[Question]
    music_path: Path
    question: Optional[Question] = attrib(default=None, init=False)
    answers: Optional[AnswerContainer] = attrib(default=None, init=False)
    position: int = attrib(default=-1, init=False)
    guess_promise: Optional[StaggeredPromise] = attrib(
        default=None, init=False
    )

    def __attrs_post_init__(self) -> None:
        self.tracks.append(
            Track(
                self.music_path, gain=self.game.config.sound.music_volume.value
            )
        )
        super().__attrs_post_init__()
        self.action('Repeat the question', symbol=key.R)(self.repeat_question)
        i: int
        letter: str
        for i, letter in enumerate(('a', 'b', 'c', 'd')):
            self.action(
                f'Guess answer {letter}', symbol=getattr(key, letter.upper())
            )(self.guess(i))
        self.action(
            'Read next information', symbol=key.DOWN,
            hat_direction=hat_directions.DOWN
        )(self.move_down)
        self.action(
            'Read previous information', symbol=key.UP,
            hat_direction=hat_directions.UP
        )(self.move_up)
        self.action('Guess', symbol=key.RETURN)(self.enter_guess)

        @self.event
        def on_push() -> None:
            self.next_question()

    def next_question(self) -> None:
        """Get the next question, and speak its text."""
        self.position = -1
        self.question = self.questions.pop()
        self.answers = AnswerContainer(self.question.answers.copy())
        self.repeat_question()

    def question_string(self) -> str:
        """Return the current question as a string, suitable for speaking by
        the arrows, or the r key.
        """
        q: Optional[Question] = self.question
        assert q is not None
        prefix: str = ''
        if q.type is QuestionTypes.boolean:
            prefix = 'True or false: '
        return prefix + q.text

    def repeat_question(self) -> None:
        """Repeat the current question."""
        q: Optional[Question] = self.question
        assert q is not None
        assert self.answers is not None
        strings: List[str] = []
        i: int
        a: Answer
        for i, a in enumerate(self.answers.answers):
            strings.append(f'{letters[i]}: {a.text}')
        strings.insert(-1, 'or')
        self.game.output(
            f'{q.category_name}: {self.question_string()}'
            '\n\n' + ','.join(strings)
        )

    def guess(self, i: int) -> Callable[[], None]:
        """Returns a function that performs a guess.

        :param i: The desired position in the list of answers.
        """

        def inner() -> None:
            if self.guess_promise is not None:
                return

            @StaggeredPromise.decorate
            def promise() -> StaggeredPromiseGeneratorType:
                assert self.answers is not None
                try:
                    a: Answer = self.answers.answers[i]
                except IndexError:
                    return  # There are not that many possible answers.
                p: Path = sounds.icons.paths[
                    'correct.mp3' if a.correct else 'wrong.mp3'
                ]
                self.game.interface_sound_player.play_path(p)
                yield 0.5
                ci: int = self.answers.answers.index(self.answers.correct)
                self.game.output(
                    f'{"Correct!" if a.correct else "Sorry, but"} '
                    f'the answer was {letters[ci]}: '
                    f'{self.answers.correct.text}'
                )
                yield 2.0
                self.next_question()

            @promise.event
            def on_finally() -> None:
                self.guess_promise = None

            self.guess_promise = promise
            promise.run()

        return inner

    def speak_answer(self) -> None:
        """Speak the currently focussed answer."""
        assert self.answers is not None
        a: Answer = self.answers.answers[self.position]
        i: int = self.answers.answers.index(a)
        letter: str = letters[i]
        self.game.output(f'{letter}: {a.text}', interrupt=True)

    def move_down(self) -> None:
        """Read the next bit of information."""
        assert self.question is not None
        assert self.answers is not None
        self.position = min(self.position + 1, len(self.answers.answers) - 1)
        self.speak_answer()

    def move_up(self) -> None:
        """Read the previous bit of information."""
        assert self.question is not None
        assert self.answers is not None
        self.position = max(-1, self.position - 1)
        if self.position == -1:
            self.game.output(self.question_string(), interrupt=True)
        else:
            self.speak_answer()

    def enter_guess(self) -> None:
        """Allows guessing with the enter key."""
        if self.position != -1:
            return self.guess(self.position)()
