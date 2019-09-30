'''Tests for the :mod:`~.CompositionConversionMCNPToT4` module.'''

# pylint: disable=no-value-for-parameter

from math import isfinite, isclose, fabs

from hypothesis import given, note
from hypothesis.strategies import (floats, integers, text, composite, just,
                                   sampled_from, one_of)

from t4_geom_convert.Kernel.Composition.CompositionConversionMCNPToT4 \
    import str_fabs


@composite
def formats(draw):
    '''Generate a random Python format specification for floats.

    Examples:

    * ``{:8.14f}``
    * ``{:.13e}``
    * ``{:15.3g}``
    '''
    fmt_type = draw(sampled_from('efg'))
    first_field = draw(one_of(just(''), integers(1, 30).map(str)))
    second_field = draw(integers(1, 30).map(str))
    return '{:' + first_field + '.' + second_field + fmt_type + '}'


@given(number=floats())
def test_str_fabs_conversion(number):
    '''Test that :func:`~.str_fabs` correctly converts floats.'''
    fmt = '{:.15e}'
    number_str = fmt.format(number)
    result = str_fabs(number_str)
    note('result = ' + result)
    number_roundtrip = float(result)
    assert result in number_str
    if number > 0.:
        assert number_str.lstrip() == result
    elif number < 0.:
        assert number_str.lstrip() == '-' + result
    elif number == 0.:
        # this handles the case of negative zero, too
        assert result == fmt.format(0.0)
    if isfinite(number) and isfinite(number_roundtrip):
        assert isclose(fabs(number), number_roundtrip)


@given(number=floats(),
       spaces_before=text(' ', max_size=5),
       spaces_after=text(' ', max_size=5),
       fmt=formats())
def test_str_fabs_spaces(number, spaces_before, spaces_after, fmt):
    '''Test that :func:`~.str_fabs` is robust with respect to space and format
    specifications.'''
    number_str = spaces_before + fmt.format(number) + spaces_after
    result = str_fabs(number_str)
    note('result = ' + result)
    assert result in number_str
    if number > 0.:
        assert number_str.strip() == result
    elif number < 0.:
        assert number_str.strip() == '-' + result
    elif number == 0.:
        # this handles the case of negative zero, too
        assert result == fmt.format(0.0).lstrip()
