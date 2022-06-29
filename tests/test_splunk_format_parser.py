import pytest

from splunk_format_parser import (
    SplunkFormatParser, 
    SplunkFormatParserException,
    Format
)

# Test parse flat json

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
    input = '( ( "host.dev"="mylaptop" ) )'
    expected = [{'host.dev': 'mylaptop'}]
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
    input = '[ [ host="mylaptop" && source="syslog.log" && sourcetype="syslog" ] || ' \
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

# Test parse json

def test_parse_json_basic():
    input = '( ( "host.src"="1.1.1.1" ) )'
    expected = [{'host': {'src': '1.1.1.1'}}]
    actual = SplunkFormatParser.parse(input, format=Format.JSON)
    assert actual == expected

def test_parse_json_multi_col():
    input = '( ( "host.src"="1.1.1.1" AND source="log" ) )'
    expected = [{'host': {'src': '1.1.1.1'}, 'source': 'log'}]
    actual = SplunkFormatParser.parse(input, format=Format.JSON)
    assert actual == expected

def test_parse_json_multi_row():
    input = '( ( "host.src"="1.1.1.1" AND source="log" ) OR ' \
              '( "host.src"="2.2.2.2" AND source="log" ) )'
    expected = [{'host': {'src': '1.1.1.1'}, 'source': 'log'},
                {'host': {'src': '2.2.2.2'}, 'source': 'log'}]
    actual = SplunkFormatParser.parse(input, format=Format.JSON)
    assert actual == expected

def test_parse_json_deep_nested():
    input = '( ( "host.src.ip"="1.1.1.1" ) )'
    expected = [{'host': {'src': {'ip': '1.1.1.1'}}}]
    actual = SplunkFormatParser.parse(input, format=Format.JSON)
    assert actual == expected

def test_parse_json_multi_key():
    input = '( ( "host.src.ip"="1.1.1.1" AND "host.dst.ip"="8.8.8.8" ) )'
    expected = [{'host': {'src': {'ip': '1.1.1.1'}, 'dst': {'ip': '8.8.8.8'}}}]
    actual = SplunkFormatParser.parse(input, format=Format.JSON)
    assert actual == expected

def test_parse_json_multivalue():
    input = '( ( ( "host.src.ip"="1.1.1.1" OR "host.src.ip"="2.2.2.2") AND '\
                '( "host.src.port"="1234" OR "host.src.port"="5678" ) AND ' \
                   '"host.dst.ip"="8.8.8.8" AND "host.dst.port"="53" ) )'
    expected = [{'host': {
                    'src': {
                        'ip': ['1.1.1.1', '2.2.2.2'], 
                        'port': ['1234', '5678']
                    },
                    'dst': {
                        'ip': '8.8.8.8',
                        'port': '53'
                    }}}]
    actual = SplunkFormatParser.parse(input, format=Format.JSON)
    assert actual == expected

# Test parse csv

def test_parse_csv_basic():
    input = '( ( "host.src"="1.1.1.1" ) )'
    expected = [['host.src'], ['1.1.1.1']]
    actual = SplunkFormatParser.parse(input, format=Format.CSV)
    assert actual == expected

def test_parse_csv_multi_col():
    input = '( ( "host.src"="1.1.1.1" AND source="log" ) )'
    expected = [['host.src', 'source'], ['1.1.1.1', 'log']]
    actual = SplunkFormatParser.parse(input, format=Format.CSV)
    assert actual == expected

def test_parse_csv_multi_row():
    input = '( ( "host.src"="1.1.1.1" AND source="log" ) OR ' \
              '( "host.src"="2.2.2.2" AND source="log" ) )'
    expected = [['host.src', 'source'], 
                ['1.1.1.1', 'log'], 
                ['2.2.2.2', 'log']]
    actual = SplunkFormatParser.parse(input, format=Format.CSV)
    assert actual == expected

def test_parse_csv_order():
    input = '( ( "host.src"="1.1.1.1" AND source="log" ) OR ' \
              '( source="log" AND "host.src"="2.2.2.2" ) )'
    expected = [['host.src', 'source'], 
                ['1.1.1.1', 'log'], 
                ['2.2.2.2', 'log']]
    actual = SplunkFormatParser.parse(input, format=Format.CSV)
    assert actual == expected

# Test exceptions

def test_raise_unsupported_format_exception():
    expected = 'unsupported format "unsupported"'
    
    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse('', format='unsupported')
    assert str(exc_info.value) == expected

def test_raise_row_prefix_exception():
    input = '[ ( host="mylaptop" ) )'
    expected = 'expecting keyword "(" but found "[" (char 0)'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_row_end_exception():
    input = '( ( host="mylaptop" ) ]'
    expected = 'expecting keyword ")" but found "]" (char 22)'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_col_prefix_exception():
    input = '( [ host="mylaptop" ) )'
    expected = 'expecting keyword "(" but found "[" (char 2)'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_col_end_exception():
    input = '( ( host="mylaptop" ] )'
    expected = 'expecting keyword ")" but found "]" (char 20)'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_value_prefix_exception():
    input = '( ( host=\'mylaptop\' ) )'
    expected = 'expecting token """ but found "\'" (char 9)'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_multivalue_end_exception():
    input = '( ( ( source="syslog.log.1" OR source="syslog.log.2" ] ) )'
    expected = 'expecting keyword ")" but found "]" (char 53)'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_multivalue_diff_key_exception():
    input = '( ( ( source1="syslog.log.1" OR source2="syslog.log.2" ) ) )'
    expected = 'multivalue contains different key string: "source1" != "source2" (char 53)'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_extra_data_exception():
    input = '( ( host="mylaptop" ) ) )'
    expected = 'extra data ")" (char 24)'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input)
    assert str(exc_info.value) == expected

def test_raise_escape_char_exception():
    input = '( ( host="&&"mylaptop&&"" ) )'
    expected = 'escape character can only be 1 character long: "&&"'

    with pytest.raises(SplunkFormatParserException) as exc_info:
        SplunkFormatParser.parse(input, escape_char='&&')
    assert str(exc_info.value) == expected