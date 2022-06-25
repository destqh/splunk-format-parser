import pytest

from splunk_format_parser import SplunkFormatParser, SplunkFormatParserException

def test_parse_basic():
    input = '( ( host="mylaptop" ) )'
    expected = [{'host': 'mylaptop'}]
    actual = SplunkFormatParser.parse(input)
    assert actual == expected

def test_parse_empty_res():
    input = 'NOT()'
    expected = []
    actual = SplunkFormatParser.parse(input)
    assert actual == expected

def test_parse_empty_str():
    input = ''
    expected = []
    actual = SplunkFormatParser.parse(input)
    assert actual == expected

def test_parse_multiple_col():
    input = '( ( host="mylaptop" AND source="syslog.log" AND sourcetype="syslog" ) )'
    expected = [{'host': 'mylaptop','source': 'syslog.log', 'sourcetype': 'syslog'}]
    actual = SplunkFormatParser.parse(input)
    assert actual == expected

def test_parse_multiple_row():
    input = '( ( host="mylaptop" AND source="syslog.log" AND sourcetype="syslog" ) OR '\
            '( host="bobslaptop" AND source="bob-syslog.log" AND sourcetype="syslog" ) )'
    expected = [{'host': 'mylaptop','source': 'syslog.log', 'sourcetype': 'syslog'},
                {'host': 'bobslaptop','source': 'bob-syslog.log', 'sourcetype': 'syslog'}]
    actual = SplunkFormatParser.parse(input)
    assert actual == expected

def test_parse_multivalue():
    input = '( ( host="mylaptop" AND ( source="syslog.log.1" OR source="syslog.log.2" ) AND sourcetype="syslog" ) )'
    expected = [{'host': 'mylaptop','source': ['syslog.log.1', 'syslog.log.2'], 'sourcetype': 'syslog'}]
    actual = SplunkFormatParser.parse(input)
    assert actual == expected

def test_quoted_key():
    input = '( ( "host.dev"="mylaptop" AND source="syslog.log" AND "source.type"="syslog" ) )'
    expected = [{'host.dev': 'mylaptop','source': 'syslog.log', 'source.type': 'syslog'}]
    actual = SplunkFormatParser.parse(input)
    assert actual == expected

def test_parse_null_char():
    input = '( ( host="my\x00laptop" ) )'
    expected = [{'host': 'my\x00laptop'}]
    actual = SplunkFormatParser.parse(input)
    assert actual == expected

def test_parse_escape_char():
    input = '( ( host="my\\"laptop\\"" ) )'
    expected = [{'host': 'my"laptop"'}]
    actual = SplunkFormatParser.parse(input)
    assert actual == expected

def test_parse_escape_escape_char():
    input = '( ( host="my\\laptop\\\\" ) )'
    expected = [{'host': 'my\\laptop\\'}]
    actual = SplunkFormatParser.parse(input)
    assert actual == expected

def test_parse_custom_escape_char():
    input = '( ( host="&my&"lap&&top&"" ) )'
    expected = [{'host': '&my"lap&top"'}]
    actual = SplunkFormatParser.parse(input, escape_char='&')
    assert actual == expected

def test_parse_custom_escape_char_double_quotes():
    input = '( ( host="my""laptop""" ) )'
    expected = [{'host': 'my"laptop"'}]
    actual = SplunkFormatParser.parse(input, escape_char='"')
    assert actual == expected

def test_parse_custom_sep():
    input = '[ [ host="mylaptop" && source="syslog.log" && sourcetype="syslog" ] || '\
            '[ host="bobslaptop" && source="bob-syslog.log" && sourcetype="syslog" ] ]'
    expected = [{'host': 'mylaptop','source': 'syslog.log', 'sourcetype': 'syslog'},
                {'host': 'bobslaptop','source': 'bob-syslog.log', 'sourcetype': 'syslog'}]
    actual = SplunkFormatParser.parse(input, "[", "[", "&&", "]", "||", "]")
    assert actual == expected

def test_parse_custom_mvsep():
    input = '( ( ( source="syslog.log.1" mvseparator source="syslog.log.2" ) ) )'
    expected = [{'source': ['syslog.log.1', 'syslog.log.2']}]
    actual = SplunkFormatParser.parse(input, mvsep='mvseparator')
    assert actual == expected

def test_parse_custom_empty():
    input = 'None'
    expected = []
    actual = SplunkFormatParser.parse(input, emptystr='None')
    assert actual == expected

def test_raise_row_prefix_exception():
    input = '[ ( host="mylaptop" ) )'
    expected = 'expected keyword "(" but found "["'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_row_end_exception():
    input = '( ( host="mylaptop" ) ]'
    expected = 'expected keyword ")" but found "]"'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_col_prefix_exception():
    input = '( [ host="mylaptop" ) )'
    expected = 'expected keyword "(" but found "["'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_col_end_exception():
    input = '( ( host="mylaptop" ] )'
    expected = 'expected keyword ")" but found "]"'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_value_prefix_exception():
    input = '( ( host=\'mylaptop\' ) )'
    expected = 'expected token """ but found "\'"'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_multivalue_end_exception():
    input = '( ( ( source="syslog.log.1" OR source="syslog.log.2" ] ) )'
    expected = 'expected keyword ")" but found "]"'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_multivalue_diff_key_exception():
    input = '( ( ( source1="syslog.log.1" OR source2="syslog.log.2" ) ) )'
    expected = 'multivalue contains different key value: "source1" != "source2"'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_escape_char_exception():
    input = '( ( host="&&"mylaptop&&"" ) )'
    expected = 'escape character have to be 1 character long: "&&"'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input, escape_char='&&')
    assert str(exc_info.value) == expected