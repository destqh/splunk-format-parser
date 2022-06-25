from splunk_format_parser import SplunkFormatParser

# input = '( ( host="mylap\\"top" AND source="sy\x00slog.log" AND sourcetype="syslog" ) OR '\
#         '( host="bobslaptop" AND source="bob-syslog.log" AND sourcetype="syslog" ) )'
# input = '( ( ( source1="syslog.log.1" OR source2="syslog.log.2" ) ) )'

input = '( [ host="""mylaptop""" ] )'
actual = SplunkFormatParser().parse(input, "(", "[", "&&", "]", "||", ")", escape_char='"')
print(actual)
# print(actual[0]['host'])
# print(actual[0]['source'])


# a = None
# b = 1
# print(a == b)

# input = '\x00Testing test2'

# i = iter(input)
# print(next(i))
# print(next(i))
# print(next(i))

# def get_token(iterator):
#     return next(iterator, None)

# def get_keyword(iterator):
#     token = get_token(iterator)
#     while token and token == ' ':
#         token = get_token(iterator)
    
#     keyword_list = [token]
#     token = get_token(iterator)
#     while token and token != ' ':
#         keyword_list.append(token)
#         token = get_token(iterator)
    
#     return ''.join(keyword_list)

# print(repr(get_keyword(i)))
# print(repr(get_keyword(i)))

# encode_input = input.encode()

# tuple_input = unpack('{}c'.format(len(encode_input)), encode_input)
# print(tuple_input)

# byte_array = bytearray(encode_input)
# print(next(byte_array))