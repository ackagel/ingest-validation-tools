#!/usr/bin/env python3

import argparse
import sys
import inspect

from ingest_validation_tools.error_report import ErrorReport
from ingest_validation_tools.cli_utils import ShowUsageException, exit_codes
from ingest_validation_tools.schema_loader import PreflightError
from ingest_validation_tools.validation_utils import (
    get_tsv_errors, get_schema_version
)


def make_parser():
    parser = argparse.ArgumentParser(
        description='Validate a HuBMAP TSV.',
        epilog=f'''
Exit status codes:
  {exit_codes.VALID}: Validation passed
  {exit_codes.BUG}: Unexpected bug
  {exit_codes.ERROR}: User error
  {exit_codes.INVALID}: Validation failed
''',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--path', required=True,
        help='TSV path')
    parser.add_argument(
        '--schema', required=True,
        choices=['sample', 'antibodies', 'contributors', 'metadata'])
    error_report_methods = [
        name for (name, type) in inspect.getmembers(ErrorReport)
        if name.startswith('as_')
    ]
    parser.add_argument('--output', choices=error_report_methods,
                        default='as_text')
    return parser


# We want the error handling inside the __name__ == '__main__' section
# to be able to show the usage string if it catches a ShowUsageException.
# Defining this at the top level makes that possible.
parser = make_parser()


def main():
    args = parser.parse_args()
    try:
        schema_name = (
            args.schema if args.schema != 'metadata'
            else get_schema_version(args.path, 'ascii').schema_name
        )
    except PreflightError as e:
        errors = {'Preflight': str(e)}
    else:
        errors = get_tsv_errors(args.path, schema_name=schema_name)
        errors = {f'{schema_name} TSV errors': errors} if errors else {}
    report = ErrorReport(errors)
    print(getattr(report, args.output)())
    return exit_codes.INVALID if errors else exit_codes.VALID


if __name__ == "__main__":
    try:
        exit_status = main()
    except ShowUsageException as e:
        print(parser.format_usage(), file=sys.stderr)
        print(e, file=sys.stderr)
        exit_status = exit_codes.ERROR
    sys.exit(exit_status)
