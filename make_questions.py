from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from io import BytesIO
from pathlib import Path
from shutil import rmtree
from time import time
from typing import List

from django.utils.text import slugify
from TTS.server.server import synthesizer

from inquisitive.open_trivia_db import (Answer, Question, QuestionFactory,
                                        QuestionTypes)

parser: ArgumentParser = ArgumentParser(
    formatter_class=ArgumentDefaultsHelpFormatter
)

parser.add_argument(
    '-n', '--number', type=int, help='The number of questions to gather',
    default=1000
)

wav: str = '.wav'
txt: str = '.txt'

sounds_dir: Path = Path('sounds')
questions_dir: Path = sounds_dir / 'questions'
categories_dir: Path = sounds_dir / 'categories'
difficulties_dir: Path = sounds_dir / 'difficulties'
question_filename: str = 'question'
correct_filename: str = 'correct'


def ensure_path(p: Path) -> None:
    """Ensure the path ``p`` exists."""
    if not p.is_dir():
        print(f'Creating directory {p}...')
        p.mkdir()


def dump_audio(path: Path, text: str) -> None:
    data: BytesIO = synthesizer.tts(text)
    with path.open('wb') as fb:
        fb.write(data.read())


def dump_speech(directory: Path, filename: str, text: str) -> None:
    """Write the given speech to 2 files: One which contains the pure text, and
    another which contains the audio data."""
    txt_file: Path = directory / (filename + txt)
    if not txt_file.is_file():
        print(f'Writing {txt_file}...')
        with txt_file.open('w') as fa:
            fa.write(text)
    wav_file: Path = directory / (filename + wav)
    if not wav_file.is_file():
        dump_audio(wav_file, text)


if __name__ == '__main__':
    args = parser.parse_args()
    n: int = 0
    ensure_path(sounds_dir)
    ensure_path(questions_dir)
    ensure_path(categories_dir)
    ensure_path(difficulties_dir)
    factory: QuestionFactory = QuestionFactory()
    print('Generating token...')
    factory.generate_token()
    while n < args.number:
        print('Getting more questions...')
        questions: List[Question] = factory.get_questions()
        q: Question
        for q in questions:
            started = time()
            category_slug = slugify(q.category_name)
            p: Path = questions_dir / category_slug
            ensure_path(p)
            try:
                dump_speech(
                    categories_dir, category_slug,
                    q.category_name.replace(':', ' and')
                )
                difficulty: str = q.difficulty.name
                p /= difficulty
                ensure_path(p)
                dump_speech(difficulties_dir, slugify(difficulty), difficulty)
                p /= slugify(q.text)
                if p.is_dir():
                    print('Skipping duplicate question.')
                    continue
                n += 1
                print(f'Question {n} / {args.number}:')
                p.mkdir()
                answers_dir: Path = p / 'answers'
                answers_dir.mkdir()
                if q.type == QuestionTypes.boolean:
                    q.text = f'True of false: {q.text}'
                dump_speech(p, question_filename, q.text)
                i: int
                a: Answer
                for i, a in enumerate(q.answers):
                    dump_speech(
                        p if a.correct else answers_dir,
                        'correct' if a.correct else str(i),
                        a.text
                    )
                print(
                    'Finished with question in %.2f seconds.' % (
                        time() - started
                    )
                )
            except Exception as e:
                rmtree(p)
                print('Removing directory because of an error:')
                if not isinstance(
                    e, (IndexError, RuntimeError, UnicodeEncodeError)
                ):
                    raise
