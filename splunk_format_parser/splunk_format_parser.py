from enum import Enum

class Format(Enum):
    FLAT_JSON = 'flat.json'
    JSON = 'json'
    CSV= 'csv'

class SplunkFormatParserException(Exception):
    pass

class SplunkFormatParser:
    
    @classmethod
    def parse(cls,
              result: str,
              row_prefix: str = '(',
              column_prefix: str ='(',
              column_separator: str ='AND',
              column_end: str =')',
              row_separator: str ='OR',
              row_end: str =')',
              mvsep: str ='OR',
              emptystr: str ='NOT()',
              escape_char: str ='\\',
              format: Format = Format.FLAT_JSON) -> list:
        """Parse Splunk search result string from a format command into list.

        Example:
        Input: '( ( host="mylaptop" AND source="syslog.log" ) OR
                ( host="bobslaptop" AND source="bob-syslog.log" ) )'
        
        Output: [{'host': 'mylaptop','source': 'syslog.log'},
                 {'host': 'bobslaptop','source': 'bob-syslog.log'}]
        
        Assumptions:
        1. Field key string do not starts or ends with '"'.
        2. Field value string always starts and ends with '"'.
        3. Multivalue fields always starts with '(' and ends with ')'.
        4. Field key and value are separated by '=' without any spaces.
        5. All prefix, end and separator are separated by a single space.
        5. Escape character only escape itself or '"' in field value.

        Args:
            result (str): Splunk search result string to parse.
            row_prefix (str, optional): The value to use for the row prefix.
                Defaults to '('.
            column_prefix (str, optional): The value to use for the column prefix. 
                Defaults to '('.
            column_separator (str, optional): The value to use for the column separator.
                Defaults to 'AND'.
            column_end (str, optional): The value to use for the column end. 
                Defaults to ')'.
            row_separator (str, optional): The value to use for the row separator. 
                Defaults to 'OR'.
            row_end (str, optional): The value to use for the column end.
                Defaults to ')'.
            mvsep (str, optional): The separator to use for multivalue fields.
                Defaults to 'OR'.
            emptystr (str, optional): The value that the format command outputs instead 
                of the default empty string NOT( ) if the results generated up to that 
                point are empty and no fields or values other than internal fields are 
                returned. Defaults to 'NOT()'.
            escape_char (str, optional): The value to use to escape double quotes in
                values. Defaults to '\'.
            format (Format, optional): The format of the parsed Splunk search result.

        Returns:
            List: Parsed Splunk search result as a list.
        """

        if len(escape_char) != 1:
            raise SplunkFormatParserException(
                'escape character can only be 1 character long: "%s"'
                % escape_char)
        
        cls._mvsep = mvsep
        cls._row_prefix = row_prefix
        cls._column_prefix = column_prefix
        cls._column_separator = column_separator
        cls._column_end = column_end
        cls._row_separator = row_separator
        cls._row_end = row_end
        cls._emptystr = emptystr
        cls._escape_char = escape_char

        cls._token = None
        cls._keyword = None
        cls._iterator = iter(result)
        cls._char_index = -1
        cls._fields = set()
        
        if format == Format.FLAT_JSON:
            return cls._parse_flat_json()
        elif format == Format.CSV:
            return cls._parse_csv()
        elif format == Format.JSON:
            return cls._parse_json()
        else:
            raise SplunkFormatParserException('unsupported format "%s"' % format)


    @classmethod
    def _parse_csv(cls):
        results = cls._parse_flat_json()
        fields = sorted(cls._fields)
        res_lst = [fields]
        for res in results:
            values = []
            for field in fields:
                values.append(res.get(field, ''))
            res_lst.append(values)
        return res_lst


    @classmethod
    def _parse_json(cls):
        results = cls._parse_flat_json()
        for i in range(len(results)):
            results[i] = cls._unflatten_json(results[i])
        return results

    
    @classmethod
    def _unflatten_json(cls, flat_json):
        json = {}
        for k, v in flat_json.items():
            if not '.' in k:
                json[k] = v
                continue

            keys = k.split('.')
            nest_dict = json
            for key in keys[:-1]:
                nest_dict[key] = nest_dict.get(key, {})
                nest_dict = nest_dict[key]
            nest_dict[keys[-1]] = v
        return json


    @classmethod
    def _parse_flat_json(cls):
        cls._next_token()
        cls._next_keyword()
        if not cls._keyword:
            return []
        if cls._keyword == cls._emptystr:
            cls._match_token(None)
            return []
        results = cls._parse_row()
        
        cls._next_keyword()
        if cls._keyword:
            raise SplunkFormatParserException(
                'extra data "%s" (char %s)' % (cls._keyword, cls._char_index-1))
        return results
    

    @classmethod
    def _parse_row(cls):
        res_lst = []
        cls._match_keyword(cls._row_prefix)

        while cls._token:
            cls._next_keyword()
            col_dict = cls._parse_column()
            res_lst.append(col_dict)
            
            cls._next_keyword()
            if cls._keyword != cls._row_separator:
                break
        
        cls._match_keyword(cls._row_end)
        return res_lst

    
    @classmethod
    def _parse_column(cls):
        col_dict = {}
        cls._match_keyword(cls._column_prefix)
        
        while cls._token:
            while cls._token and cls._token == ' ':
                cls._next_token()
            
            if cls._token == '(':
                key, value = cls._get_key_multivalue()
            else:
                key, value = cls._get_key_value()
            col_dict[key] = value

            cls._next_keyword()
            if cls._keyword != cls._column_separator:
                break

        cls._match_keyword(cls._column_end)
        return col_dict


    @classmethod
    def _get_key_multivalue(cls):
        cls._match_token('(')
        cls._next_token()

        main_key, value = cls._get_key_value()
        values = [value]

        cls._next_keyword()
        while cls._keyword == cls._mvsep:
            key, value = cls._get_key_value()
            if key != main_key:
                raise SplunkFormatParserException(
                    'multivalue contains different key string: "%s" != "%s" (char %s)' 
                    % (main_key, key, cls._char_index-1))
            values.append(value)
            cls._next_keyword()
        
        cls._match_keyword(')')
        return key, values


    @classmethod
    def _get_key_value(cls):
        while cls._token and cls._token == ' ':
            cls._next_token()
        key = cls._get_key()
        value = cls._get_value()
        return  key, value


    @classmethod
    def _get_key(cls):       
        key_lst = [cls._token]
        cls._next_token()
        while cls._token and cls._token != '=':
            key_lst.append(cls._token)
            cls._next_token()
        
        cls._next_token()
        key = ''.join(key_lst).strip('"')
        cls._fields.add(key)
        return key


    @classmethod
    def _get_value(cls):
        cls._match_token('"')
        cls._next_token()

        value_lst = []
        while cls._token:
            cur_char = cls._token
            cls._next_token()
            
            if cur_char == cls._escape_char and \
               (cls._token == '"' or cls._token == cls._escape_char):
                value_lst.append(cls._token)
                cls._next_token()
                continue
            
            if cur_char == '"':
                break
            value_lst.append(cur_char)

        return ''.join(value_lst)


    @classmethod
    def _next_keyword(cls):
        while cls._token and cls._token == ' ':
            cls._next_token()
        if not cls._token:
            cls._keyword = None
            return
        
        keyword_lst = [cls._token]
        cls._next_token()
        while cls._token and cls._token != ' ':
            keyword_lst.append(cls._token)
            cls._next_token()
        
        cls._keyword = ''.join(keyword_lst)
   

    @classmethod
    def _next_token(cls):
        cls._token = next(cls._iterator, None)
        cls._char_index += 1


    @classmethod
    def _match_keyword(cls, expected):
        if cls._keyword != expected:
            raise SplunkFormatParserException(
                'expecting keyword "%s" but found "%s" (char %s)' 
                % (expected, cls._keyword, cls._char_index-1))


    @classmethod
    def _match_token(cls, expected):
        if cls._token != expected:
            raise SplunkFormatParserException(
                'expecting token "%s" but found "%s" (char %s)'
                % (expected, cls._token, cls._char_index))