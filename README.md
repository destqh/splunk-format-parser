# Splunk Format Parser
A parser for Splunk search result string with [format](https://docs.splunk.com/Documentation/SplunkCloud/latest/SearchReference/Format) command.

## Example
Suppose that you have results in the **search** field that look like this:
```
( ( host="mylaptop" AND source="syslog.log" AND sourcetype="syslog" ) OR ( host="bobslaptop" AND source="bob-syslog.log" AND sourcetype="syslog" ) ) 
```
This parser can be used to extract the fields and values from the string above into a list of dictionaries in python.
```json
[
    {
        'host': 'mylaptop',
        'source': 'syslog.log',
        'sourcetype': 'syslog'
    },
    {
        'host': 'bobslaptop',
        'source': 'bob-syslog.log',
        'sourcetype': 'syslog'
    }
]
```
## Usage
1. Copy [splunk_format_parser.py](splunk_format_parser/splunk_format_parser.py) into your project.
2. Import `SplunkFormatParser` and use the static method `parse`.
    ```python
    from splunk_format_parser import SplunkFormatParser

    result_str = '( ( host="mylaptop" AND source="syslog.log" AND sourcetype="syslog" ) OR ( host="bobslaptop" AND source="bob-syslog.log" AND sourcetype="syslog" ) )'

    result = SplunkFormatParser.parse(input)
    ```

## Note
Depending on the `output_mode` you specified in Splunk search API, the escape character could defer. For example, `output_mode='json'` uses `\` while `output_mode='csv'` uses `"` as the escape character. This parser uses `\` as the escape character by default and it can be changed by passing a character to the `escape_char` argument.
```python
result = SplunkFormatParser.parse(input, escape_char='"')
```

## Assumptions
1. Field key string do not starts or ends with `"`.
2. Field value string always starts and ends with `"`.
3. Multivalue fields always starts with `(` and ends with `)`.
4. Field key and value are separated by `=` without any spaces.
5. All prefix, end and separator are separated by a single space.
5. Escape character only escape itself or `"` in field value.