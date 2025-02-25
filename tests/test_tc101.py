"""
File tests TC101:
    Annotation is wrapped in unnecessary quotes
"""

import sys
import textwrap

import pytest

from flake8_type_checking.constants import TC101
from tests.conftest import _get_error

examples = [
    # No error
    ('', set()),
    ("x: 'int'", {'1:3 ' + TC101.format(annotation='int')}),
    ("from __future__ import annotations\nx: 'int'", {'2:3 ' + TC101.format(annotation='int')}),
    ("if TYPE_CHECKING:\n\timport y\nx: 'y'", set()),
    # this used to return an error, but it's prone to false positives
    ("x: 'dict[int]'", set()),
    ("if TYPE_CHECKING:\n\tfrom typing import Dict\nx: 'Dict[int]'", set()),
    ("if TYPE_CHECKING:\n\tFoo: TypeAlias = Any\nx: 'Foo'", set()),
    # Basic AnnAssign with type-checking block and exact match
    (
        "from __future__ import annotations\nif TYPE_CHECKING:\n\tfrom typing import Dict\nx: 'Dict'",
        {'4:3 ' + TC101.format(annotation='Dict')},
    ),
    # Nested ast.AnnAssign with quotes
    (
        "from __future__ import annotations\nfrom typing import Dict\nx: Dict['int']",
        {'3:8 ' + TC101.format(annotation='int')},
    ),
    (
        'from __future__ import annotations\nfrom typing import Dict\nx: Dict | int',
        set(),
    ),
    # ast.AnnAssign from type checking block import with quotes
    (
        textwrap.dedent(
            '''
            from __future__ import annotations

            if TYPE_CHECKING:
                import something

            x: "something"
            '''
        ),
        {'7:3 ' + TC101.format(annotation='something')},
    ),
    # No futures import and no type checking block
    ("from typing import Dict\nx: 'Dict'", {'2:3 ' + TC101.format(annotation='Dict')}),
    (
        textwrap.dedent(
            '''
        from __future__ import annotations

        if TYPE_CHECKING:
            import something

        def example(x: "something") -> something:
            pass
        '''
        ),
        {'7:15 ' + TC101.format(annotation='something')},
    ),
    (
        textwrap.dedent(
            '''
        from __future__ import annotations

        if TYPE_CHECKING:
            import something

        def example(x: "something") -> "something":
            pass
        '''
        ),
        {'7:15 ' + TC101.format(annotation='something'), '7:31 ' + TC101.format(annotation='something')},
    ),
    (
        textwrap.dedent(
            '''
        from __future__ import annotations

        def example(x: "something") -> "something":
            pass
        '''
        ),
        {'4:15 ' + TC101.format(annotation='something'), '4:31 ' + TC101.format(annotation='something')},
    ),
    (
        textwrap.dedent(
            '''
        if TYPE_CHECKING:
            import something

        def example(x: "something") -> "something":
            pass
        '''
        ),
        set(),
    ),
    (
        textwrap.dedent(
            '''
        class X:
            def foo(self) -> 'X':
                pass
        '''
        ),
        set(),
    ),
    (
        textwrap.dedent(
            '''
        from __future__ import annotations
        class X:
            def foo(self) -> 'X':
                pass
        '''
        ),
        {'4:21 ' + TC101.format(annotation='X')},
    ),
    (
        textwrap.dedent(
            '''
        from typing import Annotated

        x: Annotated[int, 42]
        '''
        ),
        set(),
    ),
    # Make sure we didn't introduce any regressions while solving #167
    # since we started to treat the RHS sort of like an annotation for
    # some of the use-cases
    (
        textwrap.dedent(
            '''
        from __future__ import annotations
        if TYPE_CHECKING:
            from foo import Foo

        x: TypeAlias = 'Foo'
        '''
        ),
        set(),
    ),
    (
        # Regression test for #186
        textwrap.dedent(
            '''
        def foo(self) -> None:
            x: Bar
        '''
        ),
        set(),
    ),
    (
        # Reverse regression test for #186
        textwrap.dedent(
            '''
        def foo(self) -> None:
            x: 'Bar'
        '''
        ),
        {'3:7 ' + TC101.format(annotation='Bar')},
    ),
]

if sys.version_info >= (3, 12):
    # PEP695 tests
    examples += [
        (
            textwrap.dedent(
                """
            def foo[T](a: 'T') -> 'T':
                pass

            class Bar[T](Set['T']):
                x: 'T'
            """
            ),
            {
                '2:14 ' + TC101.format(annotation='T'),
                '2:22 ' + TC101.format(annotation='T'),
                '6:7 ' + TC101.format(annotation='T'),
            },
        )
    ]


@pytest.mark.parametrize(('example', 'expected'), examples)
def test_TC101_errors(example, expected):
    assert _get_error(example, error_code_filter='TC101') == expected
