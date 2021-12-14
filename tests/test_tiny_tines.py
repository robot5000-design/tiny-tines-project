import unittest
import datetime
import json
import io
import sys
from tiny_tines_app import (
    convert_dot_notation,
    convert_string_literals,
    assemble_final_string,
    process_actions,
    main,
)


class TestUnitTesting(unittest.TestCase):

    def setUp(self):
        self.test_dict = {'foo': {'bar': 'baz'}}

    def tearDown(self):
        self.test_dict.clear()

    def test_convert_dot_notation(self):
        actual = convert_dot_notation('foo.bar ')
        expected = "request_results['foo']['bar']"
        self.assertEqual(actual, expected)

    def test_assemble_final_string_good(self):
        test_dict = self.test_dict
        actual = assemble_final_string([['hello '], [r'{}', 'foo.bar'], [' world!']], test_dict)
        expected = r'hello baz world!'
        self.assertEqual(actual, expected)

    def test_assemble_final_string_bad_key(self):
        # invokes KeyError
        test_dict = self.test_dict
        actual = assemble_final_string([['hello '], [r'{}', 'foo.bat'], [' world!']], test_dict)
        expected = r'hello  world!'
        self.assertEqual(actual, expected)

    def test_assemble_final_string_key_not_exist(self):
        # invokes TypeError
        test_dict = self.test_dict
        actual = assemble_final_string([['hello '], [r'{}', 'foo.bar.no_exist'], [' world!']], test_dict)
        expected = r'hello  world!'
        self.assertEqual(actual, expected)

    def test_assemble_final_string_uneven_braces(self):
        # invokes ValueError
        test_dict = self.test_dict
        actual = assemble_final_string([[r'hello {{}', 'foo.bar'], [' world!']], test_dict)
        expected = r'hello {{} world!'
        self.assertEqual(actual, expected)

    def test_assemble_final_string_extra_brace(self):
        test_dict = self.test_dict
        actual = assemble_final_string([[r'{he{llo '], [r'{}', 'foo.bar'], [' world!']], test_dict)
        expected = r'{he{llo baz world!'
        self.assertEqual(actual, expected)

    def test_convert_string_literals_plain_string(self):
        actual = convert_string_literals('fooBarbaz')
        expected = [["fooBarbaz"]]
        self.assertEqual(actual, expected)

    def test_convert_string_literals_string_with_variables_even_braces(self):
        actual = convert_string_literals(r'hello{{foo.bar}} world!')
        expected = [['hello'], [r'{}', 'foo.bar'], [' world!']]
        self.assertEqual(actual, expected)

    def test_convert_string_literals_string_with_variables_uneven_braces(self):
        actual = convert_string_literals(r'hello{{foo.bar}}} world!')
        expected = [['hello'], [r'{{foo.bar}}}'], [' world!']]
        self.assertEqual(actual, expected)

    def test_convert_string_literals_string_with_variables_extra_braces(self):
        actual = convert_string_literals(r'}}{{llo{{foo.bar}} one{{ {{ world! }} {')
        expected = [[r'}}'], [r'{{llo'], [r'{}', 'foo.bar'], [' one'], [r'{{ '], [r'{}', ' world! '], [' '], ['{']]
        self.assertEqual(actual, expected)

    def test_convert_string_literals_string_with_variables_empty_braces(self):
        actual = convert_string_literals(r'hello {} world! ')
        expected = [['hello '], [r'{}', ''], [' world! ']]
        self.assertEqual(actual, expected)

    def test_process_actions_good_data(self):
        with open('tests/fixtures/tiny-tines-test-data.json') as json_data_file:
            test_json_data = json.load(json_data_file)
        week = datetime.datetime.strftime(datetime.date.today(), '%W')
        actual = process_actions(test_json_data)
        expected = [f'Current week number : {week}', 'Result type: date']
        self.assertEqual(actual, expected)

    def test_process_actions_json_error(self):
        with open('tests/fixtures/tiny-tines-test-data-json-error.json') as json_data_file:
            test_json_data = json.load(json_data_file)
        actual = process_actions(test_json_data)[:18]
        expected = 'JSON Decode Error:'
        self.assertEqual(actual, expected)

    def test_process_actions_connection_error(self):
        with open('tests/fixtures/tiny-tines-test-data-connection-error.json') as json_data_file:
            test_json_data = json.load(json_data_file)
        actual = process_actions(test_json_data)[:17]
        expected = 'Connection Error:'
        self.assertEqual(actual, expected)

    def test_process_actions_connection_non_2XX_error(self):
        with open('tests/fixtures/tiny-tines-test-data-404.json') as json_data_file:
            test_json_data = json.load(json_data_file)
        actual = process_actions(test_json_data)[:18]
        expected = 'Error Status Code:'
        self.assertEqual(actual, expected)

    def test_process_actions_url_not_a_string_error(self):
        with open('tests/fixtures/tiny-tines-test-data-url-non-string.json') as json_data_file:
            test_json_data = json.load(json_data_file)
        actual = process_actions(test_json_data)
        expected = 'The option URL must be a string.'
        self.assertEqual(actual, expected)

    def test_process_actions_message_not_a_string_error(self):
        with open('tests/fixtures/tiny-tines-test-data-message-non-string.json') as json_data_file:
            test_json_data = json.load(json_data_file)
        actual = process_actions(test_json_data)
        expected = 'The option message must be a string.'
        self.assertEqual(actual, expected)


class TestIntegrationTesting(unittest.TestCase):

    def test_main_good_data(self):
        week = datetime.datetime.strftime(datetime.date.today(), '%W')
        captured_output = io.StringIO()
        sys.stdout = captured_output
        main('tests/fixtures/tiny-tines-test-data.json')
        sys.stdout = sys.__stdout__
        actual = captured_output.getvalue()
        expected = f'Current week number : {week}\nResult type: date\n'
        self.assertEqual(actual, expected)

    def test_main_json_error(self):
        captured_output = io.StringIO()
        sys.stdout = captured_output
        main('tests/fixtures/tiny-tines-test-data-json-error.json')
        sys.stdout = sys.__stdout__
        actual = captured_output.getvalue()[:18]
        expected = 'JSON Decode Error:'
        self.assertEqual(actual, expected)

    def test_main_file_not_found(self):
        captured_output = io.StringIO()
        sys.stdout = captured_output
        main('does-not-exist.json')
        sys.stdout = sys.__stdout__
        actual = captured_output.getvalue()[:45]
        expected = 'The JSON input file specified does not exist!'
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
