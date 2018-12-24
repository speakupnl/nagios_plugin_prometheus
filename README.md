# nagios_plugin_prometheus
Nagios/Icinga plugin for alerting on Prometheus query results.


# Features
  * Autodetect vector and scalar result sets.
  * Handle multiple results and provide the metrics to Nagios / Icinga.
  * Easy debugging due to multiple levels of verbosity.
  * Compatble with python versions 2.7+ and 3+.
  * Less quoting nightmare than a plugin written in bash.


# Requirements
  * python-nagiosplugin
  * python-requests


# Usage
    usage: check_prometheus.py [-h] -u URL -q QUERY [-w RANGE] [-c RANGE]
                               [-U USERNAME] [-P PASSWORD] [-H HOSTNAME]
                               [-n SERVICENAME] [-I] [-v]
    
    Nagios/Icinga plugin to check values from Prometheus.
    
    optional arguments:
      -h, --help            show this help message and exit
      -u URL, --url URL     URL for the Prometheus API, i.e.:
                            https://prometheus/api/v1/query
      -q QUERY, --query QUERY
                            Prometheus query that returns one or more floats or
                            ints
      -w RANGE, --warning RANGE
                            Warning level range "[@][start:][end]". "start:" may
                            be omitted if start==0. "~:" means that start is
                            negative infinity. If end is omitted, infinity is
                            assumed. To invert the match condition, prefix the
                            range expression with "@".
      -c RANGE, --critical RANGE
                            Critical level range "[@][start:][end]". "start:" may
                            be omitted if start==0. "~:" means that start is
                            negative infinity. If end is omitted, infinity is
                            assumed. To invert the match condition, prefix the
                            range expression with "@".
      -U USERNAME, --username USERNAME
                            Username to authenticate to Prometheus
      -P PASSWORD, --password PASSWORD
                            Password to authenticate to Prometheus
      -H HOSTNAME, --host HOSTNAME
                            Hostname as known in Nagios/Icinga, default:
                            prometheus
      -n SERVICENAME, --name SERVICENAME
                            A name for the metric being checked, default:
                            prometheus
      -I, --ignorenan       Ignore NaN results
      -k, --insecure        Allow insecure connections
      -v, --verbose         Increase output verbosity (use up to 3 times)

