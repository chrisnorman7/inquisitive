from typing import List

from pytest import raises

from inquisitive.open_trivia_db import (Answer, Category, InvalidTokenError,
                                        Question, QuestionCount,
                                        QuestionDifficulties, QuestionFactory,
                                        QuestionTypes, get_categories,
                                        get_question_count, get_questions,
                                        get_token)


def test_get_token() -> None:
    assert isinstance(get_token(), str)


def test_get_categories() -> None:
    categories: List[Category] = get_categories()
    assert isinstance(categories, list)
    assert len(categories) >= 5  # Shouldn't be any less than that.
    assert isinstance(categories[0], Category)


def test_question_count() -> None:
    c: Category = Category(99, 'Testing')
    counts: QuestionCount = QuestionCount(c, 10, 15, 20, 25)
    assert counts.category is c
    assert counts.total == 10
    assert counts.easy == 15
    assert counts.medium == 20
    assert counts.hard == 25


def test_get_question_count() -> None:
    c: Category = get_categories()[0]
    counts: QuestionCount = get_question_count(c)
    assert isinstance(counts, QuestionCount)
    assert counts.category is c
    assert isinstance(counts.total, int)
    assert isinstance(counts.easy, int)
    assert isinstance(counts.medium, int)
    assert isinstance(counts.hard, int)
    assert counts.total == (counts.easy + counts.medium + counts.hard)


def test_get_questions() -> None:
    t: str = get_token()
    questions: List[Question] = get_questions(t)
    assert isinstance(questions, list)
    assert len(questions) == 10
    q: Question = questions[0]
    assert isinstance(q, Question)
    assert isinstance(q.category_name, str)
    assert isinstance(q.text, str)
    assert isinstance(q.type, QuestionTypes)
    assert isinstance(q.difficulty, QuestionDifficulties)
    questions = get_questions(t, amount=15)
    assert len(questions) == 15
    assert isinstance(questions[0], Question)
    c: Category = get_categories()[0]
    questions = get_questions(t, amount=1, category=c)
    assert questions[0].category_name == c.name
    questions = get_questions(
        t, amount=1, difficulty=QuestionDifficulties.hard
    )
    assert questions[0].difficulty is QuestionDifficulties.hard
    questions = get_questions(t, type=QuestionTypes.boolean)
    assert questions[0].type is QuestionTypes.boolean
    assert len(questions[0].answers) == 2
    questions = get_questions(t, amount=1, type=QuestionTypes.multiple)
    q = questions[0]
    assert len(q.answers) >= 2
    a: Answer = q.answers[0]
    assert isinstance(a, Answer)
    assert a.correct is True
    assert isinstance(a.text, str)
    a = q.answers[1]
    assert isinstance(a.text, str)
    assert a.correct is False
    assert str(q) == '%s:\n%s' % (q.category_name, q.text)


def test_question_factory() -> None:
    f: QuestionFactory = QuestionFactory()
    assert f.token is None
    with raises(InvalidTokenError):
        f.get_questions()
    f.generate_token()
    assert isinstance(f.token, str)
    questions: List[Question] = f.get_questions()
    assert isinstance(questions, list)
    assert isinstance(questions[0], Question)
