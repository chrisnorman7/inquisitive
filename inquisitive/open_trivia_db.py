"""A small package for working with data from https://opentdb.com/."""

from enum import Enum
from html import unescape
from typing import Any, Dict, List, Optional, Union, cast

from attr import attrs
from requests import Response, get

token_request_url: str = 'https://opentdb.com/api_token.php?command=request'
get_questions_url: str = 'https://opentdb.com/api.php?token={}&amount={}'


class OpenTriviaDbError(Exception):
    """The base class for all exceptions raised as a result of errors in the
    Open Trivia DB API."""
    pass


class Success(OpenTriviaDbError):
    """A successful API call.

    This exception will never be raised, but simply exists to fill out the
    ``api_errors``` list.
    """
    pass


class NoResults(OpenTriviaDbError):
    """Could not return results. The API doesn't have enough questions for your
    query. (Ex. Asking for 50 Questions in a Category that only has 20).
    """
    pass


class InvalidParameter(OpenTriviaDbError):
    """Contains an invalid parameter. Arguements passed in aren't valid. (Ex.
    Amount = Five).
    """
    pass


class TokenNotFound(OpenTriviaDbError):
    """Session Token does not exist."""
    pass


class TokenEmpty(OpenTriviaDbError):
    """Session Token has returned all possible questions for the specified
    query. Resetting the Token is necessary.
    """
    pass


api_errors = [
    Success,
    NoResults,
    InvalidParameter,
    TokenNotFound,
    TokenEmpty
]


class QuestionError(OpenTriviaDbError):
    """There was an error parsing a question."""
    pass


class UnknownTypeError(QuestionError):
    """The question is of an unknown type."""
    pass


class UnknownDifficultyError(QuestionError):
    """The question has an unknown difficulty."""
    pass


@attrs(auto_attribs=True)
class Category:
    """A question category.

    While these objects can be tested for equality, instances will not be
    reused.

    :ivar id: The ID of this category in the Open Trivia DB database.

    :ivar name: The name of this category.
    """

    id: int
    name: str


@attrs(auto_attribs=True)
class QuestionCount:
    """A count of how many questions are in a given category."""

    category: Category

    total: int
    easy: int
    medium: int
    hard: int


@attrs(auto_attribs=True)
class Answer:
    """An answer to a Question."""

    text: str
    correct: bool


class QuestionTypes(Enum):
    """The type of a given question."""

    multiple = 'Multiple Choice'
    boolean = 'True / False'


class QuestionDifficulties(Enum):
    """The difficulty of a given question."""

    easy = 'Easy'
    medium = 'Medium'
    hard = 'Hard'


@attrs(auto_attribs=True)
class Question:
    """A question from Open Trivia DB."""

    category_name: str
    text: str
    type: QuestionTypes
    difficulty: QuestionDifficulties
    answers: List[Answer]

    def __str__(self) -> str:
        return f'{self.category_name}:\n{self.text}'


def get_url(url: str, *args, **kwargs) -> Dict[str, Any]:
    """Gets a URL from Open Trivia DB, and results the body as JSON.

    If the status code is not 0, the appropriate error from the ``api_errors``
    list will be raised.
    """
    r: Response = get(url, *args, **kwargs)
    d: Dict[str, Any] = r.json()
    error: Optional[int] = d.get('response_code', None)
    if error is not None and error != 0:
        if isinstance(error, int):
            try:
                raise api_errors[error]
            except IndexError:
                raise OpenTriviaDbError('Error code %d.' % error)
        else:
            raise OpenTriviaDbError('Error: %r.' % error)
    return d


def get_token() -> str:
    """This function retrieves and returns a token from Open Trivia DB. You
    should keep this token around, as you will need to provide it to various
    functions throughout this package."""
    return get_url(token_request_url)['token']


def get_categories() -> List[Category]:
    """This function returns all the categories in the Open Trivia Database."""
    r: Response = get('https://opentdb.com/api_category.php')
    d: Dict[str, Any] = r.json()
    data: Dict[str, Union[int, str]]
    categories: List[Category] = []
    for data in d['trivia_categories']:
        c: Category = Category(
            cast(int, data['id']), cast(str, data['name'])
        )
        categories.append(c)
    return categories


def get_question_count(category: Category) -> QuestionCount:
    """Returns the number of questions in the given category."""
    r: Response = get(
        f'https://opentdb.com/api_count.php?category={category.id}'
    )
    d: Dict[str, Any] = r.json()
    counts: Dict[str, int] = d['category_question_count']
    return QuestionCount(
        category, counts['total_question_count'],
        counts['total_easy_question_count'],
        counts['total_medium_question_count'],
        counts['total_hard_question_count']
    )


def get_questions(
    token: str, amount: int = 10,
    category: Optional[Category] = None,
    difficulty: Optional[QuestionDifficulties] = None,
    type: Optional[QuestionTypes] = None
) -> List[Question]:
    """Returns a list of questions."""
    u: str = get_questions_url.format(token, amount)
    if category is not None:
        u += f'&category={category.id}'
    if difficulty is not None:
        u += f'&difficulty={difficulty.name}'
    if type is not None:
        u += f'&type={type.name}'
    results: List[Dict[str, Any]] = get_url(u)['results']
    questions: List[Question] = []
    for r in results:
        answers: List[Answer] = [Answer(r['correct_answer'], True)]
        text: str
        for text in r['incorrect_answers']:
            answers.append(Answer(text, False))
        t: QuestionTypes
        for t in QuestionTypes:
            if t.name == r['type']:
                break
        else:
            raise UnknownTypeError(r['type'])
        d: QuestionDifficulties
        for d in QuestionDifficulties:
            if d.name == r['difficulty']:
                break
        else:
            raise UnknownDifficultyError(r['difficulty'])
        questions.append(
            Question(r['category'], unescape(r['question']), t, d, answers)
        )
    return questions
