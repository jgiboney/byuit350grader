# -----------------------------------------------------------------------------
#
# Copyright: Justin Scott Giboney, 2019
#
# This code is only to be used for testing IT 350 assignments at Brigham Young 
# University.
# 
# No permission is granted to redistribute, replicate, mimic, copy, or modify 
# this code.
#
# No warranty is given either. This may annihilate your computer, your files,
# your life, and/or humanity. Use at your own risk! 
#
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
#
# You will need:
# Python 3 and a connection to the server.
#
# How to use:
# > python3 byuit350grader.py -c <config_file> -i <ip_file> -m <multiplier> -v <verbose optional>
#
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
#
# Remember that this code is just for practice. Values will change for final
# grading.
#
# -----------------------------------------------------------------------------


import json, getopt, requests, sys


# -------------------- CONSTANTS --------------------
HOW_TO_USE_MESSAGE = "Three arguments are required: config_file, list_of_ips,"\
  " and multiplier (optionally verbose).\n"\
  "byuit350grader.py -c <config_file> -i <ip_file> -m <multiplier> -v "\
  "<verbose optional>"

VARIABLES = {
    "c": {"name":"config_file", "required":True, "value":None},
    "i": {"name":"ip_file", "required":True, "value":None},
    "m": {"name":"multiplier", "required":True, "value":None},
    "v": {"name":"verbose", "required":False, "value":None}
  }



def checkExpectedFormat (content, expected_format):
    if expected_format == 'text':
        return [1,'Format matches.']
    elif expected_format == 'json':
        try:
            json.loads(content)
            return [1,'Format matches.']
        except:
            return [0,'Not valid JSON.']
    else:
        return [0,'Unexpected format.']


def checkExpectedResults (content, expected_results):
    # This checks to see if we don't want the result to match
    #print(content)
    #print(expected_results)
    if expected_results == 'none' or expected_results.lower() in content.lower():
        #print('matched')
        return [1,'Results match.']
    else:
        #print('not matched')
        return [0,'Results do not match.']
        

def checkPHPError (content):
    if "line" in content.lower() or "php" in content.lower():
        if "example:" in content.lower():
            return [1,'No PHP error found.']
        else:
            return [0,'PHP error in file.']
    else:
        return [1,'No PHP error found.']


def checkStatusCode (url_request):
    code = url_request.status_code
    if code == 200 or 400:
        return [1,'File retrieval successful.']
    elif code == 404:
        return [0,'File not found.']
    elif code == 500:
        return [0,'Server error for file.']
    else:
        return [0,'Unknown error.']
    


def retrieve_page (url_with_parameters):
    url_request = requests.get(url_with_parameters)
    status_code = checkStatusCode(url_request)
    if status_code[0] == 1:
        return [1,url_request]
    else:
        return [status_code[0],status_code[1]]



def check_page (url_with_parameters, expected_format, expected_results, verbose=False):
    if verbose == True:
        print(url_with_parameters)
    status, page = retrieve_page(url_with_parameters)  
    # This tells us whether the page was retrieved properly     
    if status == 1:
        contents = page.text
        status, comment = checkPHPError(contents)
        # This tells us whether the page contains a PHP error
        if status == 1:
            # This tells us whether the page output matches the expected format
            status, comment = checkExpectedFormat(contents, expected_format)
            if status == 1:
                status, comment = checkExpectedResults(contents, expected_results)
                # This tells us whether the page was retrieved properly
                if status == 1:
                    return [1, 'Page passed!', contents]
                else:
                    return [0, 'Page failed: ' + comment, contents]
            else:
                return [0, 'Page failed: ' + comment, contents]
        else:
            return [status, comment]
    else:
        return [status, page]



def run_ouput_option_test (url, testFormat, testOutput, outputOption, verbose=False):
    output_specific_output = testOutput.replace("<output>",outputOption)
    test_result = check_page(url, testFormat, output_specific_output, verbose)
    return test_result



def run_column_option_test (url, testFormat, testOutput, columnOption, outputOptions, verbose=False):
    column_specific_url = url.replace("<column_name>",columnOption)
    column_specific_output = testOutput.replace("<column_name>",columnOption)
    successful_test_result = ''
    for outputOption in outputOptions:
        test_result = run_ouput_option_test(column_specific_url, testFormat, column_specific_output, outputOption, verbose)
        if test_result[0] == 1:
            successful_test_result = test_result
    if len(successful_test_result) > 0:
        return successful_test_result
    else:
        return test_result



def run_table_option_test (url, testFormat, testOutput, tableOption, columnOptions, outputOptions, verbose=False):
    table_specific_url = url.replace("<table>",tableOption)
    table_specific_ouput = testOutput.replace("<table>",tableOption)
    successful_test_result = ''
    for columnOption in columnOptions:
        test_result = run_column_option_test(table_specific_url, testFormat, table_specific_ouput, columnOption, outputOptions, verbose)
        if test_result[0] == 1:
            successful_test_result = test_result
    if len(successful_test_result) > 0:
        return successful_test_result
    else:
        return test_result



def run_test (url, test, tableOptions, columnOptions, outputOptions, verbose=False):
    passing_current_test = False
    is_reversed = False
    successful_test_result = ''
    
    for tableOption in tableOptions:
        table_url = url + test['url']
        test_result = run_table_option_test(table_url, test['format'], test['output'], tableOption, columnOptions, outputOptions, verbose)
        
        if test_result[0] == 1:
            successful_test_result = test_result
        else:
            if len(test_result) > 2 and verbose == True:
                print(test_result[2][0:60])

    if len(successful_test_result) > 0:
        return successful_test_result
    else:
        return test_result
    


def run_test_set (url, testSet, tableOptions, columnOptions, verbose=False):
    set_points = 0
    set_possible_points = 0
    for test in testSet['tests']:
        set_possible_points += testSet["value"]
        test_result = run_test(url, test, tableOptions, columnOptions, testSet['outputOptions'], verbose)
        if test_result[0] == 1 and test['reversed'] == 0 and (set_possible_points > 0 or verbose == True):
            print('\033[92m' + 'Passed  ' + '\033[0m' + test['name'])
            set_points += testSet["value"]
        elif test_result[0] == 0 and test['reversed'] == True and (set_possible_points > 0 or verbose == True):
            print('\033[92m' + 'Passed  ' + '\033[0m' + test['name'])
            set_points += testSet["value"]
        elif (set_possible_points > 0 or verbose == True):
            print('\033[91m' + 'Failed  ' + '\033[0m' + test['name'] + '  reason: ' + test_result[1])
    return [set_points, set_possible_points]



def run_tests_on_all_ips (ips, config, multiplier, verbose=False):
    ips_file = open(ips, 'r')

    for ip in ips_file:
        ip_params = ip.split(',')
        url = 'http://' + ip_params[0] + '/'
        if len(ip_params) > 2:
            url += ip_params[2] + '/'
        netid = ip_params[1]

        total_points = 0
        possible_points = 0

        with open(config) as jsonFile:
            testSets = json.load(jsonFile)

        for testSet in testSets['testSets']: 
            set_points, set_possible_points = run_test_set(url, testSet, testSets['tableOptions'], testSets['columnOptions'], verbose)
            total_points += set_points
            possible_points += set_possible_points

        print (netid.rstrip() + ' - ' + str(total_points*float(multiplier)) + ' / ' + str(possible_points*float(multiplier)))



""" This function takes the args that are passed in and a dictionary of 
  expected variables as dictionaries. The function connects the variables to  
  the dictionary.
  
  The dictionary should follow this format:
  {<identifier>: {"name":<name>, "required":<True/False>, "value":None}, ... }

  For example:
  {"c": {"name":"config_file", "required":True, "value":None}}

  The help parameter indicates whether -h is for help messages. If so, the
  function will exit exit and display the use message if -h is passed in as a 
  parameter.

  Args:
    argv:         The command line arguments.
    variables:    A dictionary of dictionaries defining the expected variables.
    use_message:  The help message to display if there is a problem.
    help:         Is -h a help message.

  Returns:
    A dictionary of dictionaries with updated variables.
  """
def parse_args (argv: dict, variables: dict, use_message: str, help: bool) -> dict:
  argstring = ':'.join(variables.keys())
  names = []
  for var, value in variables.items():
    names.append(value["name"]+"=")
  try:
    options, others = getopt.getopt(argv,argstring,names)
  except getopt.GetoptError:
    print(use_message)
    sys.exit()
  for opt, arg in options:
    opt = opt[1:]
    if help and opt == "-h":
      print(HOW_TO_USE_MESSAGE)
      sys.exit()
    else:
      if opt in variables:
        variables[opt]["value"] = arg
      else:
        print("Error trying to parse command-line arguments.")
        sys.exit()
  return variables



""" This function takes the expected command-line arguments and tells you
  whether the required arguments have values.

  Args:
    variables:  A dictionary of dictionaries defining the expected variables.

  Returns:
    A boolean whether all of the required variables have values.
  """
def validate_args (variables: dict) -> bool:
  passed = True
  for key, value in variables.items():
    if value["required"] == True and value["value"] == None:
      passed = False
      break
  return passed

            

def main (argv):
  parsed_variables = parse_args(argv, VARIABLES, HOW_TO_USE_MESSAGE, True)
  req_vars_exist = validate_args(parsed_variables)
  if not req_vars_exist:
    print(HOW_TO_USE_MESSAGE)
  else:
    if parsed_variables["v"]["value"] == "":
      parsed_variables["v"]["value"] = True
    run_tests_on_all_ips( parsed_variables["i"]["value"], 
                          parsed_variables["c"]["value"],
                          parsed_variables["m"]["value"], 
                          parsed_variables["v"]["value"] )



if __name__ == "__main__":
    main(sys.argv[1:])