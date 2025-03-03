import argparse
import json
import os
import requests
import subprocess
import sys

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-f', '--source-file', help='Source file to test (takes precedence over source-list)')
arg_parser.add_argument('-l', '--source-list', default='test-source-1.json,test-source-2.json,test-source-3.json', help='Comma-separated list of source files to test')
arg_parser.add_argument('-t', '--test-url', default='https://tych0pbo2f.execute-api.us-west-2.amazonaws.com/default/sepio-transform', help='Service URL to generate test results (defaults to non-production service)')
arg_parser.add_argument('-c', '--control-url', default='https://a61m4glrmf.execute-api.us-west-2.amazonaws.com/default/sepio-transform', help='Service URL to generate control results (defaults to production service)')
args = arg_parser.parse_args()

source_file_list = []

# Determine source file(s) to test
try:
  if args.source_file:
    source_file_list.append(args.source_file)
  elif args.source_list:
    source_file_list = args.source_list.split(',')

except Exception as e:
  sys.exit('Failed to process source file(s) argument:\n{}'.format(e))

print('\nControl service: {}'.format(args.control_url))
print('Test service: {}'.format(args.test_url))

# Run test on each source file
for source_file in source_file_list:
  print('\nComparing SEPIO transformation results for {}:'.format(source_file))

  try:
    # Get request data from source file
    source_file_object = open(source_file, 'r')
    source_file_data = source_file_object.read()
    source_file_object.close()

    # Send request data to control service and if successful, save response in a temporary file
    service_result_control = requests.post('{}/vci2cgsepio'.format(args.control_url), headers={'Content-Type': 'application/json'}, data=source_file_data, timeout=10)
    service_result_control.raise_for_status()

    service_result_control_file = open('temp-sepio-transform-control-result.json', 'w')
    json.dump(service_result_control.json(), service_result_control_file, indent='  ', sort_keys=True)
    service_result_control_file.close()

    # Send request data to test service and if successful, save response in a temporary file
    service_result_test = requests.post('{}/vci2cgsepio'.format(args.test_url), headers={'Content-Type': 'application/json'}, data=source_file_data, timeout=10)
    service_result_test.raise_for_status()

    service_result_test_file = open('temp-sepio-transform-test-result.json', 'w')
    json.dump(service_result_test.json(), service_result_test_file, indent='  ', sort_keys=True)
    service_result_test_file.close()

    # Use diff to compare results
    service_result_comparison = subprocess.run('diff temp-sepio-transform-control-result.json temp-sepio-transform-test-result.json', shell=True, text=True)

    # Delete temporary files
    os.remove('temp-sepio-transform-control-result.json')
    os.remove('temp-sepio-transform-test-result.json')

  except Exception as e:
    print('Test failed:\n{}'.format(e))
    pass
