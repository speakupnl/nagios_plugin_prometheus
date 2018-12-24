#!/usr/bin/python

"""Nagios/Icinga plugin to check values from Prometheus."""

import sys
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

import requests
import argparse
import logging
import nagiosplugin
import json
import urllib3

_log = logging.getLogger('nagiosplugin')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Data acquisition.

class Prometheus(nagiosplugin.Resource):
    """Collect metrics from Prometheus."""

    def __init__(self, args):
        self.args = args

    def probe(self):
        _log.debug("Got these arguments: '{}'".format(self.args))
        _log.info("Starting check: '{}'".format(self.args.name))
        _log.info("On host: '{}'".format(self.args.host))
        _log.info("Sending query: '{}'".format(self.args.query))
        _log.info("To server: '{}'".format(self.args.url))
        _log.info("With username / password: '{}' / '{}'".format(
                  self.args.username, len(self.args.password) * '*'))

        # Send the query to Prometheus.
        try:
            query_output = requests.get(
                self.args.url, params={'query': self.args.query}, 
                auth=(self.args.username, self.args.password),
                verify=(not self.args.insecure))
        except requests.exceptions.RequestException as e:
            raise ValueError("Unable to connect to Prometheus server at: '{}'\n"
                             "With Exception: {}".format(self.args.url, e))

        # For status other than 200 OK throw an exception.
        query_output.raise_for_status()

        _log.debug("Got this output from Prometheus:")
        try:
            _log.debug(json.dumps(query_output.json(), indent=4))
        except Exception:
            _log.debug("{}".format(query_output.text))

        results = {}

        # We expect a nested dict containing results, analyse the dict
        # and put the values we need into the results dict.  We assume
        # the metrics are unique.  If they're not, no error is given
        # and earlier values get over written by later values.
        try:
            result_type = query_output.json()['data']['resultType']
            result_set = query_output.json()['data']['result']
        except Exception:
            raise ValueError(
                "Unable to parse result: {}".format(query_output.text))
        else:
            if result_type == 'vector':
                for result in result_set:
                    _log.debug("Found a vector result: {}".format(result))
                    value = 'NaN'
                    item = ''
                    # The value we're looking for is the second item in
                    # the "value" list.
                    try:
                        value = result['value'][1]
                    except Exception:
                        _log.warning("No 'value' in {}".format(result))
                    # Whack the "metric" dict into a human readable
                    # string to use for identifying the value.
                    try:
                        item = json.dumps(result['metric']).replace('"',
                                          '').replace('{', '').replace('}', '')
                    except Exception:
                        _log.warning("No 'metric' in {}".format(result))
                    # The above can render an empty string, if so, we
                    # use the service name as a key.
                    if not item:
                        item = self.args.name
                    results[item] = value
            elif result_type == 'scalar':
                _log.debug("Found a scalar result: {}".format(result_set))
                # The value we're looking for is the second item in the
                # "result" list, use the service name as the key.
                try:
                    value = result_set[1]
                except Exception:
                    _log.warning("No second item in {}".format(result_set))
                else:
                    results[self.args.name] = value
            else:
                _log.warning("Could not parse result: {}".format(result_set))

        # Process the collected results and yield them to Nagios.  Don't
        # worry about not having any results to show, Nagios will alert
        # about empty result sets.
        for item, value in results.iteritems():
            # Cast value to float if we can cast it to int.  We do this
            # to ensure correct handling of 'NaN' results and still
            # getting detailed values in Nagios.
            try:
                int(float(value))
                value = float(value)
            except Exception:
                _log.debug("Could not cast value to float: {}".format(value))

            # Yield the results to Nagios.
            if value == 'NaN' and self.args.ignorenan:
                _log.debug("Found a NaN value and ignorenan=True")
            else:
                yield nagiosplugin.Metric(item, value, min=0,
                                          context=self.args.name)


class PrometheusSummary(nagiosplugin.Summary):
    """Status line conveying eveything is OK."""

    def ok(self, results):
        return "all values within parameters"


# Runtime environment and data evaluation.

@nagiosplugin.guarded
def main():

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-u', '--url', metavar='URL', required=True,
        default='https://prometheus/api/v1/query',
        help='URL for the Prometheus API, i.e.: %(default)s')
    parser.add_argument(
        '-q', '--query', metavar='QUERY', required=True,
        help='Prometheus query that returns one or more floats or ints')
    parser.add_argument(
        '-w', '--warning', metavar='RANGE', default='',
        help="""Warning level range "[@][start:][end]". "start:" may be omitted
        if start==0. "~:" means that start is negative infinity. If end is
        omitted, infinity is assumed. To invert the match condition, prefix the
        range expression with "@".""")
    parser.add_argument(
        '-c', '--critical', metavar='RANGE', default='',
        help="""Critical level range "[@][start:][end]". "start:" may be
        omitted if start==0. "~:" means that start is negative infinity. If end
        is omitted, infinity is assumed. To invert the match condition, prefix
        the range expression with "@".""")
    parser.add_argument(
        '-U', '--username', metavar='USERNAME', default='', 
        help='Username to authenticate to Prometheus')
    parser.add_argument(
        '-P', '--password', metavar='PASSWORD', default='', 
        help='Password to authenticate to Prometheus')
    parser.add_argument(
        '-H', '--host', metavar='HOSTNAME', default='prometheus',
        help='Hostname as known in Nagios/Icinga, default: %(default)s')
    parser.add_argument(
        '-n', '--name', metavar='SERVICENAME', default='prometheus', 
        help='A name for the metric being checked, default: %(default)s')
    parser.add_argument(
        '-I', '--ignorenan', action='store_true',
        help='Ignore NaN results')
    parser.add_argument(
        '-k', '--insecure', action='store_true',
        help='Allow insecure connections')
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Increase output verbosity (use up to 3 times)')

    args = parser.parse_args()

    check = nagiosplugin.Check(
        Prometheus(args),
        nagiosplugin.ScalarContext(args.name, args.warning, args.critical),
        PrometheusSummary())
    check.main(verbose=args.verbose)


if __name__ == '__main__':
    main()


