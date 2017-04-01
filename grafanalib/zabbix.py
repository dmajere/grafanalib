import re
import attr
from attr.validators import instance_of


ZABBIX_QMODE_METRICS = 0
ZABBIX_QMODE_SERVICES = 1
ZABBIX_QMODE_TEXT = 2

ZABBIX_SLA_PROP_STATUS = {
    "name": "Status",
    "property": "status"}

ZABBIX_SLA_PROP_SLA = {
    "name": "SLA",
    "property": "sla"}

ZABBIX_SLA_PROP_OKTIME = {
    "name": "OK time",
    "property": "okTime"}

ZABBIX_SLA_PROP_PROBTIME = {
    "name": "Problem time",
    "property": "problemTime"}

ZABBIX_SLA_PROP_DOWNTIME = {
    "name": "Down time",
    "property": "downtimeTime"}


@attr.attributes(repr=False, slots=True)
class _IsInValidator(object):
    choices = attr.attr()

    def __call__(self, inst, attr, value):
        if value not in self.choices:
            raise ValueError("{attr} should be one of {choice}".format(
                attr=attr, choice=self.choices))

    def __repr__(self):
        return (
            "<is value present in list of  {choice}>"
            .format(choice=self.choices)
        )


def is_in_validator(choices):
    """
    A validator that raises a :exc:`ValueError` if the attribute value is not
    in a provided list.

    :param choices: List of valid choices
    """
    return _IsInValidator(choices)


def is_valid_interval(instance, attribute, value):
    """
    A validator that raises a :exc:`ValueError` if the attribute value is not
    matching on regular expression.
    """
    if not re.match("^[+-]?\d*[smhdMY]$", value):
        raise ValueError(
            "valid interval should be a string "
            "matching an expressiong: ^[+-]?\d*[smhdMY]$. "
            "Exaxples: 24h 7d 1M +24h -24h")


def is_number(instance, attribute, value):
    """
    A validator that raises a :exc:`ValueError` if the attribute value is not
    a number (not int or float).
    """
    if isinstance(value, int) or isinstance(value, float):
        return
    raise ValueError("{attr} should be interger or float".format(
        attr=attribute))


@attr.s
class ZabbixTargetOptions(object):
    showDisabledItems = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        return {
            "showDisabledItems": self.showDisabledItems
        }


@attr.s
class ZabbixTargetField(object):
    filter = attr.ib(default="", validator=instance_of(str))

    def to_json_data(self):
        return {
            "filter": self.filter
        }


@attr.s
class ZabbixTarget(object):
    """Generates Zabbix datasource target JSON structure.

    Grafana-Zabbix is a plugin for Grafana allowing
    to visualize monitoring data from Zabbix and create
    dashboards for analyzing metrics and realtime monitoring.

    Grafana docs on using Zabbix pluging: http://docs.grafana-zabbix.org/

    :param application: zabbix application name
    :param expr: zabbix arbitary query
    :param functions: list of zabbix aggregation functions
    :param group: zabbix host group
    :param host: hostname
    :param intervalFactor: defines interval between metric queries
    :param item: regexp that defines which metric to query
    :param itService: zabbix it service name
    :param mode: query mode type
    :param options: additional query options
    :param refId: target reference id
    :param slaProperty: zabbix it service sla property.
        Zabbix returns the following availability information about IT service
        Status - current status of the IT service
        SLA - SLA for the given time interval
        OK time - time the service was in OK state, in seconds
        Problem time - time the service was in problem state, in seconds
        Down time - time the service was in scheduled downtime, in seconds
    :param textFilter: query text filter. Use regex to extract a part of
        the returned value.
    :param useCaptureGroups: defines if capture groups should be used during
        metric query
    """

    application = attr.ib(default="", validator=instance_of(str))
    expr = attr.ib(default="")
    functions = attr.ib(default=attr.Factory(list))
    group = attr.ib(default="", validator=instance_of(str))
    host = attr.ib(default="", validator=instance_of(str))
    intervalFactor = attr.ib(default=2, validator=instance_of(int))
    item = attr.ib(default="", validator=instance_of(str))
    itService = attr.ib(default="", validator=instance_of(str))
    mode = attr.ib(default=ZABBIX_QMODE_METRICS, validator=instance_of(int))
    options = attr.ib(default=attr.Factory(ZabbixTargetOptions),
                      validator=instance_of(ZabbixTargetOptions))
    refId = attr.ib(default="")
    slaProperty = attr.ib(default=attr.Factory(dict))
    textFilter = attr.ib(default="", validator=instance_of(str))
    useCaptureGroups = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        obj = {
            "application": ZabbixTargetField(self.application),
            "expr": self.expr,
            "functions": self.functions,
            "group": ZabbixTargetField(self.group),
            "host": ZabbixTargetField(self.host),
            "intervalFactor": self.intervalFactor,
            "item": ZabbixTargetField(self.item),
            "mode": self.mode,
            "options": self.options,
            "refId": self.refId,
        }
        if self.mode == ZABBIX_QMODE_SERVICES:
            obj["slaProperty"] = self.slaProperty,
            obj["itservice"] = {"name": self.itService}
        if self.mode == ZABBIX_QMODE_TEXT:
            obj["textFilter"] = self.textFilter
            obj["useCaptureGroups"] = self.useCaptureGroups
        return obj


@attr.s
class ZabbixDeltaFunction(object):
    """ZabbixDeltaFunction

    Convert absolute values to delta, for example, bits to bits/sec
    http://docs.grafana-zabbix.org/reference/functions/#delta
    """
    added = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        text = "delta()"
        definition = {
            "category": "Transform",
            "name": "delta",
            "defaultParams": [],
            "params": []}
        return {
            "added": self.added,
            "text": text,
            "def": definition,
            "params": [],
        }


@attr.s
class ZabbixGroupByFunction(object):
    """ZabbixGroupByFunction

    Takes each timeseries and consolidate its points falled in given interval
    into one point using function, which can be one of: avg, min, max, median.
    http://docs.grafana-zabbix.org/reference/functions/#groupBy
    """

    __options = ("avg", "min", "max", "median")
    __default_interval = "1m"
    __default_function = "avg"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=__default_interval, validator=is_valid_interval)
    function = attr.ib(default=__default_function,
                       validator=is_in_validator(__options))

    def to_json_data(self):
        text = "groupBy({interval}, {function})"
        definition = {
            "category": "Transform",
            "name": "groupBy",
            "defaultParams": [
                self.__default_interval,
                self.__default_function,
            ],
            "params": [
                {"name": "interval",
                 "type": "string"},
                {"name": "function",
                 "options": self.__options,
                 "type": "string"}]}
        return {
            "def": definition,
            "text": text.format(
                interval=self.interval, function=self.function),
            "params": [self.interval, self.function],
            "added": self.added,
        }


@attr.s
class ZabbixScaleFunction(object):
    """ZabbixScaleFunction

    Takes timeseries and multiplies each point by the given factor.
    http://docs.grafana-zabbix.org/reference/functions/#scale
    """

    __default_factor = 100

    added = attr.ib(default=False, validator=instance_of(bool))
    factor = attr.ib(default=__default_factor, validator=is_number)

    def to_json_data(self):
        text = "scale({factor})"
        definition = {
            "category": "Transform",
            "name": "scale",
            "defaultParams": [self.__default_factor],
            "params": [
                {"name": "factor",
                 "options": [100, 0.01, 10, -1],
                 "type": "float"}]
        }
        return {
            "def": definition,
            "text": text.format(factor=self.factor),
            "params": [self.factor],
            "added": self.added,
        }


@attr.s
class ZabbixAggregateByFunction(object):
    """ZabbixAggregateByFunction

    Takes all timeseries and consolidate all its points falled in given
    interval into one point using function, which can be one of:
        avg, min, max, median.
    http://docs.grafana-zabbix.org/reference/functions/#aggregateBy
    """

    __options = ("avg", "min", "max", "median")
    __default_interval = "1m"
    __default_function = "avg"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=__default_interval, validator=is_valid_interval)
    function = attr.ib(default=__default_function,
                       validator=is_in_validator(__options))

    def to_json_data(self):
        text = "aggregateBy({interval}, {function})"
        definition = {
            "category": "Aggregate",
            "name": "aggregateBy",
            "defaultParams": [
                self.__default_interval,
                self.__default_function,
            ],
            "params": [
                {"name": "interval",
                 "type": "string"},
                {"name": "function",
                 "options": self.__options,
                 "type": "string"}]}
        return {
            "def": definition,
            "text": text.format(
                interval=self.interval, function=self.function),
            "params": [self.interval, self.function],
            "added": self.added,
        }


@attr.s
class ZabbixAverageFunction(object):
    """ZabbixAverageFunction

    Deprecated, use aggregateBy(interval, avg) instead.
    http://docs.grafana-zabbix.org/reference/functions/#average
    """

    __default_interval = "1m"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=__default_interval, validator=is_valid_interval)

    def to_json_data(self):
        text = "average({interval})"
        definition = {
            "category": "Aggregate",
            "name": "average",
            "defaultParams": [
                self.__default_interval,
            ],
            "params": [
                {"name": "interval",
                 "type": "string"}]
        }
        return {
            "def": definition,
            "text": text.format(
                interval=self.interval),
            "params": [self.interval],
            "added": self.added,
        }


@attr.s
class ZabbixMaxFunction(object):
    """ZabbixMaxFunction

    Deprecated, use aggregateBy(interval, max) instead.
    http://docs.grafana-zabbix.org/reference/functions/#max
    """

    __default_interval = "1m"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=__default_interval, validator=is_valid_interval)

    def to_json_data(self):
        text = "max({interval})"
        definition = {
            "category": "Aggregate",
            "name": "max",
            "defaultParams": [
                self.__default_interval,
            ],
            "params": [
                {"name": "interval",
                 "type": "string"}]
        }
        return {
            "def": definition,
            "text": text.format(
                interval=self.interval),
            "params": [self.interval],
            "added": self.added,
        }


@attr.s
class ZabbixMedianFunction(object):
    """ZabbixMedianFunction

    Deprecated, use aggregateBy(interval, median) instead.
    http://docs.grafana-zabbix.org/reference/functions/#median
    """

    __default_interval = "1m"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default="1m", validator=is_valid_interval)

    def to_json_data(self):
        text = "median({interval})"
        definition = {
            "category": "Aggregate",
            "name": "median",
            "defaultParams": [
                self.__default_interval,
            ],
            "params": [
                {"name": "interval",
                 "type": "string"}]
        }
        return {
            "def": definition,
            "text": text.format(
                interval=self.interval),
            "params": [self.interval],
            "added": self.added,
        }


@attr.s
class ZabbixMinFunction(object):
    """ZabbixMinFunction

    Deprecated, use aggregateBy(interval, min) instead.
    http://docs.grafana-zabbix.org/reference/functions/#min
    """

    __default_interval = "1m"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=__default_interval, validator=is_valid_interval)

    def to_json_data(self):
        text = "min({interval})"
        definition = {
            "category": "Aggregate",
            "name": "min",
            "defaultParams": [
                self.__default_interval,
            ],
            "params": [
                {"name": "interval",
                 "type": "string"}]
        }
        return {
            "def": definition,
            "text": text.format(
                interval=self.interval),
            "params": [self.interval],
            "added": self.added,
        }


@attr.s
class ZabbixSumSeriesFunction(object):
    """ZabbixSumSeriesFunction

    This will add metrics together and return the sum at each datapoint.
    This method required interpolation of each timeseries so it may
    cause high CPU load.
    Try to combine it with groupBy() function to reduce load.
    http://docs.grafana-zabbix.org/reference/functions/#sumSeries
    """
    added = attr.ib(default=False)

    def to_json_data(self):
        text = "sumSeries()"
        definition = {
            "category": "Aggregate",
            "name": "sumSeries",
            "defaultParams": [],
            "params": []}
        return {
            "added": self.added,
            "text": text,
            "def": definition,
            "params": [],
        }


@attr.s
class ZabbixBottomFunction(object):

    __options = ("avg", "min", "max", "median")
    __default_number = 5
    __default_function = "avg"

    added = attr.ib(default=False, validator=instance_of(bool))
    number = attr.ib(default=__default_number, validator=instance_of(int))
    function = attr.ib(default=__default_function,
                       validator=is_in_validator(__options))

    def to_json_data(self):
        text = "bottom({number}, {function})"
        definition = {
            "category": "Filter",
            "name": "bottom",
            "defaultParams": [
                self.__default_number,
                self.__default_function,
            ],
            "params": [
                {"name": "number",
                 "type": "string"},
                {"name": "function",
                 "options": self.__options,
                 "type": "string"}]}
        return {
            "def": definition,
            "text": text.format(
                number=self.number, function=self.function),
            "params": [self.number, self.function],
            "added": self.added,
        }


@attr.s
class ZabbixTopFunction(object):

    __options = ("avg", "min", "max", "median")
    __default_number = 5
    __default_function = "avg"

    added = attr.ib(default=False, validator=instance_of(bool))
    number = attr.ib(default=__default_number, validator=instance_of(int))
    function = attr.ib(default=__default_function,
                       validator=is_in_validator(__options))

    def to_json_data(self):
        text = "top({number}, {function})"
        definition = {
            "category": "Filter",
            "name": "top",
            "defaultParams": [
                self.__default_number,
                self.__default_function,
            ],
            "params": [
                {"name": "number",
                 "type": "string"},
                {"name": "function",
                 "options": self.__options,
                 "type": "string"}]}
        return {
            "def": definition,
            "text": text.format(
                number=self.number, function=self.function),
            "params": [self.number, self.function],
            "added": self.added,
        }


@attr.s
class ZabbixTrendValueFunction(object):
    """ZabbixTrendValueFunction

    Specifying type of trend value returned by Zabbix when
    trends are used (avg, min or max).
    http://docs.grafana-zabbix.org/reference/functions/#trendValue
    """

    __options = ('avg', 'min', 'max')
    __default_type = "avg"
    added = attr.ib(default=False, validator=instance_of(bool))
    type = attr.ib(default=__default_type,
                   validator=is_in_validator(__options))

    def to_json_data(self):
        text = "trendValue({type})"
        definition = {
            "category": "Trends",
            "name": "trendValue",
            "defaultParams": [
                self.__default_type,
            ],
            "params": [
                {"name": "type",
                 "options": self.__options,
                 "type": "string"}]}
        return {
            "def": definition,
            "text": text.format(
                type=self.type),
            "params": [self.type],
            "added": self.added,
        }


@attr.s
class ZabbixTimeShiftFunction(object):
    """ZabbixTimeShiftFunction

    Draws the selected metrics shifted in time.
    If no sign is given, a minus sign ( - ) is implied which will
    shift the metric back in time.
    If a plus sign ( + ) is given, the metric will be shifted forward in time.
    http://docs.grafana-zabbix.org/reference/functions/#timeShift
    """

    __options = ("24h", "7d", "1M", "+24h", "-24h")
    __default_interval = "24h"

    added = attr.ib(default=False, validator=instance_of(bool))
    interval = attr.ib(default=__default_interval)

    def to_json_data(self):
        text = "timeShift({interval})"
        definition = {
            "category": "Time",
            "name": "timeShift",
            "defaultParams": [
                self.__default_interval,
            ],
            "params": [
                {"name": "interval",
                 "options": self.__options,
                 "type": "string"}]}
        return {
            "def": definition,
            "text": text.format(
                interval=self.interval),
            "params": [self.interval],
            "added": self.added,
        }


@attr.s
class ZabbixSetAliasFunction(object):
    """ZabbixSetAliasFunction

    Returns given alias instead of the metric name.
    http://docs.grafana-zabbix.org/reference/functions/#setAlias
    """
    alias = attr.ib(validator=instance_of(str))
    added = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        text = "setAlias({alias})"
        definition = {
            "category": "Alias",
            "name": "setAlias",
            "defaultParams": [],
            "params": [
                {"name": "alias",
                 "type": "string"}]}
        return {
            "def": definition,
            "text": text.format(alias=self.alias),
            "params": [self.alias],
            "added": self.added,
        }


@attr.s
class ZabbixSetAliasByRegexFunction(object):
    """ZabbixSetAliasByRegexFunction

    Returns part of the metric name matched by regex.
    http://docs.grafana-zabbix.org/reference/functions/#setAliasByRegex
    """

    regexp = attr.ib(validator=instance_of(str))
    added = attr.ib(default=False, validator=instance_of(bool))

    def to_json_data(self):
        text = "setAliasByRegex({regexp})"
        definition = {
            "category": "Alias",
            "name": "setAliasByRegex",
            "defaultParams": [],
            "params": [
                {"name": "aliasByRegex",
                 "type": "string"}]}
        return {
            "def": definition,
            "text": text.format(regexp=self.regexp),
            "params": [self.regexp],
            "added": self.added,
        }


def zabbixMetricTarget(application, group, host, item, functions=[]):
    return ZabbixTarget(
        mode=ZABBIX_QMODE_METRICS,
        application=application,
        group=group,
        host=host,
        item=item,
        functions=functions,
    )


def zabbixServiceTarget(service, sla=ZABBIX_SLA_PROP_STATUS):
    return ZabbixTarget(
        mode=ZABBIX_QMODE_SERVICES,
        itService=service,
        slaProperty=sla,
    )


def zabbixTextTarget(application, group, host, item, text,
                     useCaptureGroups=False):
    return ZabbixTarget(
        mode=ZABBIX_QMODE_TEXT,
        application=application,
        group=group,
        host=host,
        item=item,
        textFilter=text,
        useCaptureGroups=useCaptureGroups,
    )
