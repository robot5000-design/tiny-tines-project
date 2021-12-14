''' Tiny Tines is a command line program that takes the path to a
Tiny Tines Story JSON file as its only command line argument and
executes that Story.
'''

import json
import sys
import requests


def convert_dot_notation(dot_notation_variable):
    ''' Converts dot notation to square bracket notation
    and adds 'request_results' prefix as the base dictionary
    being accessed.
    '''
    variables_seperated = dot_notation_variable.split('.')

    for i in enumerate(variables_seperated):
        variables_seperated[i[0]] = "['" + variables_seperated[i[0]].strip() + "']"

    bracket_notation_variable = (
        'request_results' + ''.join(variables_seperated))

    return bracket_notation_variable


def convert_string_literals(string_input):
    ''' Converts string literal notations with matching quantities
    of curly braces, replaces them with a single pair and extracts
    the variable with dot notation.
    '''
    string_components = []
    count_openings = 0
    count_closings = 0
    start = 0
    last_opening = 0

    for i in enumerate(string_input):
        if string_input[i[0]] == '{' and not count_closings:
            if not count_openings and i[0] - start > 0:
                # 1st opening brace. Add string up to current index
                string_components.append([string_input[start:i[0]]])
                start = i[0]
            elif count_openings and i[0] - last_opening != 1:
                # If previous opening braces were not part of a set, add
                # string up to current index. Reset as 1st opening brace
                string_components.append([string_input[start:i[0]]])
                count_openings = 0
                start = i[0]
            count_openings += 1
            last_opening = i[0]
        elif string_input[i[0]] == '}' and count_openings:
            count_closings += 1

        # Handle what happens after finding a set of opening and closing braces
        if (i[0] == (len(string_input) - 1) or string_input[i[0] + 1] != '}'
               ) and (count_closings):
            # A matching set of braces
            if count_closings == count_openings:
                string_variable = string_input[last_opening + 1:i[0]
                                               - count_closings + 1]
                string_components.append([r'{}', string_variable])
            else:
                # Non-matching set of braces
                string_components.append([string_input[start:i[0] + 1]])
            # Reset parameters
            start = i[0] + 1
            count_openings = 0
            count_closings = 0

        # Add any remaining string
        if i[0] == len(string_input) - 1:
            string_components.append([string_input[start:i[0] + 1]])

    return string_components


def assemble_final_string(string_components, request_results):
    ''' Assembles the final usable string from string components for
    either http request url actions or print actions.
    '''
    string_final = ''

    for item in string_components:
        if len(item) > 1:
            bracket_notation_variable = convert_dot_notation(item[1])
            try:
                string_final += item[0].format(eval(bracket_notation_variable))
            except KeyError:
                string_final += item[0].format('')
            except TypeError:
                string_final += item[0].format('')
            except ValueError:
                string_final += item[0]
        else:
            string_final += item[0]

    return string_final


def process_actions(json_data):
    ''' Function for processing the JSON input file actions.
    '''
    request_results = {}
    results_array = []

    for action in json_data['actions']:
        if action['type'] == 'HTTPRequestAction':
            # Make url string literals python useable
            url = action['options']['url']
            if isinstance(url, str):
                http_string_components = convert_string_literals(url)
            else:
                return 'The option URL must be a string.'

            # Assemble the final string and assign to the http request
            string_final = assemble_final_string(
                http_string_components, request_results)
            try:
                request_results[action['name']] = requests.get(string_final)

            except requests.exceptions.ConnectionError as error:
                return f'Connection Error: {error}'

            # If a valid result is returned, decode to JSON and insert in
            # request_results
            if (request_results[action['name']].status_code >= 200
                    and request_results[action['name']].status_code <= 299):
                try:
                    request_results[action['name']] = request_results[
                        action['name']].json()

                except json.decoder.JSONDecodeError as error:
                    return f'JSON Decode Error: {error}'
            else:
                return f"Error Status Code: {request_results[action['name']].status_code}"

        elif action['type'] == 'PrintAction':
            message = action['options']['message']
            if isinstance(message, str):
                print_string_components = convert_string_literals(message)
            else:
                return 'The option message must be a string.'
            string_final = assemble_final_string(print_string_components,
                                                 request_results)
            results_array.append(string_final)

    return results_array


def main(json_file):
    ''' Opens the JSON file, handles JSON Decode or file not found exceptions
    and calls the process_actions function.
    '''
    try:
        with open(json_file) as json_data_file:
            try:
                json_input_data = json.load(json_data_file)

            except json.decoder.JSONDecodeError as err:
                print(f'JSON Decode Error: Input file is not valid JSON.\n{err}')
            else:
                results = process_actions(json_input_data)
                if isinstance(results, list):
                    for result in results:
                        print(result)
                else:
                    print(results)

    except FileNotFoundError as err:
        print('The JSON input file specified does not exist!', err)


if __name__ == '__main__':
    try:
        json_input_file = sys.argv[1]
    except IndexError:
        print('When you run this file you need to specify a JSON data input file as a 2nd command line argument.')
    else:
        main(json_input_file)
