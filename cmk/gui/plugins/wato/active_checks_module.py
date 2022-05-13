#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from typing import Mapping

from cmk.gui.i18n import _
from cmk.gui.plugins.wato.active_checks.common import (
    ip_address_family_element,
    RulespecGroupActiveChecks,
    RulespecGroupIntegrateOtherServices,
)
from cmk.gui.plugins.wato.utils import (
    HostRulespec,
    IndividualOrStoredPassword,
    PasswordFromStore,
    PluginCommandLine,
    rulespec_registry,
)
from cmk.gui.valuespec import (
    Age,
    Alternative,
    CascadingDropdown,
    Checkbox,
    Dictionary,
    DropdownChoice,
    FixedValue,
    Integer,
    ListOf,
    ListOfStrings,
    RegExp,
    TextInput,
    Transform,
    Tuple,
)


def _transform_add_address_family(v):
    v.setdefault("address_family", None)
    return v


def _valuespec_custom_checks():
    return Dictionary(
        title=_("Integrate Nagios plugins"),
        help=_(
            'With this ruleset you can configure "classical Monitoring checks" '
            "to be executed directly on your monitoring server. These checks "
            "will not use Check_MK. It is also possible to configure passive "
            "checks that are fed with data from external sources via the "
            "command pipe of the monitoring core."
        )
        + _('This option can only be used with the permission "Can add or modify executables".'),
        elements=[
            (
                "service_description",
                TextInput(
                    title=_("Service description"),
                    help=_(
                        "Please make sure that this is unique per host "
                        "and does not collide with other services."
                    ),
                    allow_empty=False,
                    default_value=_("Customcheck"),
                ),
            ),
            (
                "command_line",
                PluginCommandLine(),
            ),
            (
                "command_name",
                TextInput(
                    title=_("Internal command name"),
                    help=_(
                        "If you want, you can specify a name that will be used "
                        "in the <tt>define command</tt> section for these checks. This "
                        "allows you to a assign a custom PNP template for the performance "
                        "data of the checks. If you omit this, then <tt>check-mk-custom</tt> "
                        "will be used."
                    ),
                    size=32,
                ),
            ),
            (
                "has_perfdata",
                FixedValue(
                    value=True,
                    title=_("Performance data"),
                    totext=_("process performance data"),
                ),
            ),
            (
                "freshness",
                Dictionary(
                    title=_("Check freshness"),
                    help=_(
                        "Freshness checking is only useful for passive checks when the staleness feature "
                        "is not enough for you. It changes the state of a check to a configurable other state "
                        "when the check results are not arriving in time. Staleness will still grey out the "
                        "test after the corrsponding interval. If you don't want that, you might want to adjust "
                        "the staleness interval as well. The staleness interval is calculated from the normal "
                        "check interval multiplied by the staleness value in the <tt>Global Settings</tt>. "
                        "The normal check interval can be configured in a separate rule for your check."
                    ),
                    optional_keys=False,
                    elements=[
                        (
                            "interval",
                            Integer(
                                title=_("Expected update interval"),
                                label=_("Updates are expected at least every"),
                                unit=_("minutes"),
                                minvalue=1,
                                default_value=10,
                            ),
                        ),
                        (
                            "state",
                            DropdownChoice(
                                title=_("State in case of absent updates"),
                                choices=[
                                    (0, _("OK")),
                                    (1, _("WARN")),
                                    (2, _("CRIT")),
                                    (3, _("UNKNOWN")),
                                ],
                                default_value=3,
                            ),
                        ),
                        (
                            "output",
                            TextInput(
                                title=_("Plugin output in case of absent updates"),
                                size=40,
                                allow_empty=False,
                                default_value=_("Check result did not arrive in time"),
                            ),
                        ),
                    ],
                ),
            ),
        ],
        required_keys=["service_description"],
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupIntegrateOtherServices,
        match_type="all",
        name="custom_checks",
        valuespec=_valuespec_custom_checks,
    )
)


def _active_checks_bi_aggr_transform_from_disk(value):
    if isinstance(value, dict):
        return value
    new_value = {}
    new_value["base_url"] = value[0]
    new_value["aggregation_name"] = value[1]
    new_value["optional"] = value[4]
    new_value["credentials"] = ("configured", (value[2], value[3]))
    return new_value


def _valuespec_active_checks_bi_aggr():
    return Transform(
        valuespec=Dictionary(
            title=_("Check State of BI Aggregation"),
            help=_(
                "Connect to the local or a remote monitoring host, which uses Check_MK BI to aggregate "
                "several states to a single BI aggregation, which you want to show up as a single "
                "service."
            ),
            elements=[
                (
                    "base_url",
                    TextInput(
                        title=_("Base URL (OMD Site)"),
                        help=_(
                            "The base URL to the monitoring instance. For example <tt>http://mycheckmk01/mysite</tt>. "
                            "You can use macros like <tt>$HOSTADDRESS$</tt> and <tt>$HOSTNAME$</tt> within this URL to "
                            "make them be replaced by the hosts values."
                        ),
                        size=60,
                        allow_empty=False,
                    ),
                ),
                (
                    "aggregation_name",
                    TextInput(
                        title=_("Aggregation Name"),
                        help=_(
                            "The name of the aggregation to fetch. It will be added to the service description. You can "
                            "use macros like <tt>$HOSTADDRESS$</tt> and <tt>$HOSTNAME$</tt> within this parameter to "
                            "make them be replaced by the hosts values. The aggregation name is the title in the "
                            "top-level-rule of your BI pack."
                        ),
                        allow_empty=False,
                    ),
                ),
                (
                    "credentials",
                    CascadingDropdown(
                        choices=[
                            ("automation", _("Use the credentials of the 'automation' user")),
                            (
                                "configured",
                                _("Use the following credentials"),
                                Tuple(
                                    elements=[
                                        TextInput(
                                            title=_("Automation Username"),
                                            allow_empty=True,
                                            help=_(
                                                "The name of the automation account to use for fetching the BI aggregation via HTTP. Note: You may "
                                                "also set credentials of a standard user account, though it is disadvised. "
                                                "Using the credentials of a standard user also requires a valid authentication method set in the "
                                                "optional parameters."
                                            ),
                                        ),
                                        IndividualOrStoredPassword(
                                            title=_("Automation Secret"),
                                            help=_(
                                                "Valid automation secret for the automation user"
                                            ),
                                            allow_empty=False,
                                        ),
                                    ]
                                ),
                            ),
                        ],
                        help=_(
                            "Here you can configured the credentials to be used. Keep in mind that the <tt>automation</tt> user need "
                            "to exist if you choose this option"
                        ),
                        title=_("Login credentials"),
                        default_value="automation",
                    ),
                ),
                (
                    "optional",
                    Dictionary(
                        title=_("Optional parameters"),
                        elements=[
                            (
                                "auth_mode",
                                DropdownChoice(
                                    title=_("Authentication Mode"),
                                    default_value="cookie",
                                    choices=[
                                        ("cookie", _("Form (Cookie) based")),
                                        ("basic", _("HTTP Basic")),
                                        ("digest", _("HTTP Digest")),
                                        ("kerberos", _("Kerberos")),
                                    ],
                                ),
                            ),
                            (
                                "timeout",
                                Integer(
                                    title=_("Seconds before connection times out"),
                                    unit=_("sec"),
                                    default_value=60,
                                ),
                            ),
                            (
                                "in_downtime",
                                DropdownChoice(
                                    title=_("State, if BI aggregate is in scheduled downtime"),
                                    choices=[
                                        (None, _("Use normal state, ignore downtime")),
                                        ("ok", _("Force to be OK")),
                                        ("warn", _("Force to be WARN, if aggregate is not OK")),
                                    ],
                                ),
                            ),
                            (
                                "acknowledged",
                                DropdownChoice(
                                    title=_("State, if BI aggregate is acknowledged"),
                                    choices=[
                                        (None, _("Use normal state, ignore acknowledgement")),
                                        ("ok", _("Force to be OK")),
                                        ("warn", _("Force to be WARN, if aggregate is not OK")),
                                    ],
                                ),
                            ),
                            (
                                "track_downtimes",
                                Checkbox(
                                    title=_("Track downtimes"),
                                    label=_("Automatically track downtimes of aggregation"),
                                    help=_(
                                        "If this is active, the check will automatically go into downtime "
                                        "whenever the aggregation does. This downtime is also cleaned up "
                                        "automatically when the aggregation leaves downtime. "
                                        "Downtimes you set manually for this check are unaffected."
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
            optional_keys=False,
        ),
        forth=_active_checks_bi_aggr_transform_from_disk,
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupIntegrateOtherServices,
        match_type="all",
        name="active_checks:bi_aggr",
        valuespec=_valuespec_active_checks_bi_aggr,
    )
)


def _valuespec_active_checks_form_submit():
    return Transform(
        Tuple(
            title=_("Check HTML Form Submit"),
            help=_(
                "Check submission of HTML forms via HTTP/HTTPS using the plugin <tt>check_form_submit</tt> "
                "provided with Check_MK. This plugin provides more functionality than <tt>check_http</tt>, "
                "as it automatically follows HTTP redirect, accepts and uses cookies, parses forms "
                "from the requested pages, changes vars and submits them to check the response "
                "afterwards."
            ),
            elements=[
                TextInput(
                    title=_("Name"),
                    help=_("The name will be used in the service description"),
                    allow_empty=False,
                ),
                Dictionary(
                    title=_("Check the URL"),
                    elements=[
                        (
                            "hosts",
                            ListOfStrings(
                                title=_("Check specific host(s)"),
                                help=_(
                                    "By default, if you do not specify any host addresses here, "
                                    "the host address of the host this service is assigned to will "
                                    "be used. But by specifying one or several host addresses here, "
                                    "it is possible to let the check monitor one or multiple hosts."
                                ),
                            ),
                        ),
                        (
                            "uri",
                            TextInput(
                                title=_("URI to fetch (default is <tt>/</tt>)"),
                                allow_empty=False,
                                default_value="/",
                                regex="^/.*",
                            ),
                        ),
                        (
                            "port",
                            Integer(
                                title=_("TCP Port"),
                                minvalue=1,
                                maxvalue=65535,
                                default_value=80,
                            ),
                        ),
                        (
                            "tls_configuration",
                            DropdownChoice(
                                title=_("TLS/HTTPS configuration"),
                                help=_(
                                    "Activate or deactivate TLS for the connection. No certificate validation means that "
                                    "the server certificate will not be validated by the locally available certificate authorities."
                                ),
                                choices=[
                                    (
                                        "no_tls",
                                        _("No TLS"),
                                    ),
                                    (
                                        "tls_standard",
                                        _("TLS"),
                                    ),
                                    (
                                        "tls_no_cert_valid",
                                        _("TLS without certificate validation"),
                                    ),
                                ],
                            ),
                        ),
                        (
                            "timeout",
                            Integer(
                                title=_("Seconds before connection times out"),
                                unit=_("sec"),
                                default_value=10,
                            ),
                        ),
                        (
                            "expect_regex",
                            RegExp(
                                title=_("Regular expression to expect in content"),
                                mode=RegExp.infix,
                            ),
                        ),
                        (
                            "form_name",
                            TextInput(
                                title=_("Name of the form to populate and submit"),
                                help=_(
                                    "If there is only one form element on the requested page, you "
                                    "do not need to provide the name of that form here. But if you "
                                    "have several forms on that page, you need to provide the name "
                                    "of the form here, to enable the check to identify the correct "
                                    "form element."
                                ),
                                allow_empty=True,
                            ),
                        ),
                        (
                            "query",
                            TextInput(
                                title=_("Send HTTP POST data"),
                                help=_(
                                    "Data to send via HTTP POST method. Please make sure, that the data "
                                    'is URL-encoded (for example "key1=val1&key2=val2").'
                                ),
                                size=40,
                            ),
                        ),
                        (
                            "num_succeeded",
                            Tuple(
                                title=_("Multiple Hosts: Number of successful results"),
                                elements=[
                                    Integer(title=_("Warning if equal or below")),
                                    Integer(title=_("Critical if equal or below")),
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        ),
        forth=_transform_form_submit,
    )


def _transform_form_submit(p: tuple[str, Mapping[str, object]]) -> tuple[str, Mapping[str, object]]:
    service_name, params = p
    if "tls_configuration" in params:
        return p
    if "ssl" not in params:
        return p
    return service_name, {
        **{k: v for k, v in params.items() if k != "ssl"},
        "tls_configuration": "tls_standard",
    }


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupActiveChecks,
        match_type="all",
        name="active_checks:form_submit",
        valuespec=_valuespec_active_checks_form_submit,
    )
)


def _valuespec_active_checks_notify_count():
    return Tuple(
        title=_("Check notification number per contact"),
        help=_(
            "Check the number of sent notifications per contact using the plugin <tt>check_notify_count</tt> "
            "provided with Check_MK. This plugin counts the total number of notifications sent by the local "
            "monitoring core and creates graphs for each individual contact. You can configure thresholds "
            "on the number of notifications per contact in a defined time interval. "
            "This plugin queries livestatus to extract the notification related log entries from the "
            "log file of your monitoring core."
        ),
        elements=[
            TextInput(
                title=_("Service Description"),
                help=_("The name that will be used in the service description"),
                allow_empty=False,
            ),
            Integer(
                title=_("Interval to monitor"),
                label=_("notifications within last"),
                unit=_("minutes"),
                minvalue=1,
                default_value=60,
            ),
            Dictionary(
                title=_("Optional parameters"),
                elements=[
                    (
                        "num_per_contact",
                        Tuple(
                            title=_("Thresholds for Notifications per Contact"),
                            elements=[
                                Integer(title=_("Warning if above"), default_value=20),
                                Integer(title=_("Critical if above"), default_value=50),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupIntegrateOtherServices,
        match_type="all",
        name="active_checks:notify_count",
        valuespec=_valuespec_active_checks_notify_count,
    )
)


def _valuespec_active_checks_traceroute():
    return Transform(
        valuespec=Dictionary(
            title=_("Check current routing"),
            help=_(
                "This active check uses <tt>traceroute</tt> in order to determine the current "
                "routing from the monitoring host to the target host. You can specify any number "
                "of missing or expected routes in order to detect e.g. an (unintended) failover "
                "to a secondary route."
            ),
            elements=[
                (
                    "dns",
                    Checkbox(
                        title=_("Name resolution"),
                        label=_("Use DNS to convert IP addresses into hostnames"),
                        help=_(
                            "If you use this option, then <tt>traceroute</tt> is <b>not</b> being "
                            "called with the option <tt>-n</tt>. That means that all IP addresses "
                            "are tried to be converted into names. This usually adds additional "
                            "execution time. Also DNS resolution might fail for some addresses."
                        ),
                    ),
                ),
                ip_address_family_element(),
                (
                    "routers",
                    ListOf(
                        valuespec=Tuple(
                            elements=[
                                TextInput(
                                    title=_("Router (FQDN, IP-Address)"),
                                    allow_empty=False,
                                ),
                                DropdownChoice(
                                    title=_("How"),
                                    choices=[
                                        ("W", _("WARN - if this router is not being used")),
                                        ("C", _("CRIT - if this router is not being used")),
                                        ("w", _("WARN - if this router is being used")),
                                        ("c", _("CRIT - if this router is being used")),
                                    ],
                                ),
                            ]
                        ),
                        title=_("Router that must or must not be used"),
                        add_label=_("Add Condition"),
                    ),
                ),
                (
                    "method",
                    DropdownChoice(
                        title=_("Method of probing"),
                        choices=[
                            (None, _("UDP (default behaviour of traceroute)")),
                            ("icmp", _("ICMP Echo Request")),
                            ("tcp", _("TCP SYN")),
                        ],
                    ),
                ),
            ],
            optional_keys=False,
        ),
        forth=_transform_add_address_family,
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupActiveChecks,
        match_type="all",
        name="active_checks:traceroute",
        valuespec=_valuespec_active_checks_traceroute,
    )
)


def _valuespec_active_checks_by_ssh():
    return Tuple(
        title=_("Check via SSH service"),
        help=_("Checks via SSH. "),
        elements=[
            TextInput(
                title=_("Command"),
                help=_("Command to execute on remote host."),
                allow_empty=False,
                size=50,
            ),
            Dictionary(
                title=_("Optional parameters"),
                elements=[
                    (
                        "description",
                        TextInput(
                            title=_("Service Description"),
                            help=_(
                                "Must be unique for every host. Defaults to command that is executed."
                            ),
                            size=50,
                        ),
                    ),
                    (
                        "hostname",
                        TextInput(
                            title=_("DNS Hostname or IP address"),
                            default_value="$HOSTADDRESS$",
                            allow_empty=False,
                            help=_(
                                "You can specify a hostname or IP address different from IP address "
                                "of the host as configured in your host properties."
                            ),
                        ),
                    ),
                    (
                        "port",
                        Integer(
                            title=_("SSH Port"),
                            help=_("Default is 22."),
                            minvalue=1,
                            maxvalue=65535,
                            default_value=22,
                        ),
                    ),
                    (
                        "ip_version",
                        Alternative(
                            title=_("IP-Version"),
                            elements=[
                                FixedValue(value="ipv4", totext="", title=_("IPv4")),
                                FixedValue(value="ipv6", totext="", title=_("IPv6")),
                            ],
                        ),
                    ),
                    (
                        "timeout",
                        Integer(
                            title=_("Seconds before connection times out"),
                            unit=_("sec"),
                            default_value=10,
                        ),
                    ),
                    (
                        "logname",
                        TextInput(
                            title=_("Username"), help=_("SSH user name on remote host"), size=30
                        ),
                    ),
                    (
                        "identity",
                        TextInput(
                            title=_("Keyfile"), help=_("Identity of an authorized key"), size=50
                        ),
                    ),
                    (
                        "accept_new_host_keys",
                        FixedValue(
                            value=True,
                            title=_("Enable automatic host key acceptance"),
                            help=_(
                                "This will automatically accept hitherto-unseen keys"
                                "but will refuse connections for changed or invalid hostkeys"
                            ),
                            totext=_(
                                "Automatically stores the host key with no manual input requirement"
                            ),
                        ),
                    ),
                ],
            ),
        ],
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupIntegrateOtherServices,
        match_type="all",
        name="active_checks:by_ssh",
        valuespec=_valuespec_active_checks_by_ssh,
    )
)


def _valuespec_active_checks_elasticsearch_query():
    return Dictionary(
        required_keys=["svc_item", "pattern", "timerange"],
        title=_("Query elasticsearch logs"),
        help=_("You can search indices for defined patterns in defined fieldnames."),
        elements=[
            (
                "svc_item",
                TextInput(
                    title=_("Item suffix"),
                    help=_(
                        "Here you can define what service description (item) is "
                        "used for the created service. The resulting item "
                        "is always prefixed with 'Elasticsearch Query'."
                    ),
                    allow_empty=False,
                    size=16,
                ),
            ),
            (
                "hostname",
                TextInput(
                    title=_("DNS hostname or IP address"),
                    help=_(
                        "You can specify a hostname or IP address different from the IP address "
                        "of the host this check will be assigned to."
                    ),
                    allow_empty=False,
                ),
            ),
            ("user", TextInput(title=_("Username"), size=32, allow_empty=True)),
            (
                "password",
                PasswordFromStore(
                    title=_("Password of the user"),
                    allow_empty=False,
                ),
            ),
            (
                "protocol",
                DropdownChoice(
                    title=_("Protocol"),
                    help=_("Here you can define which protocol to use, default is https."),
                    choices=[
                        ("http", "HTTP"),
                        ("https", "HTTPS"),
                    ],
                    default_value="https",
                ),
            ),
            (
                "port",
                Integer(
                    title=_("Port"),
                    help=_(
                        "Use this option to query a port which is different from standard port 9200."
                    ),
                    default_value=9200,
                ),
            ),
            (
                "pattern",
                TextInput(
                    title=_("Search pattern"),
                    help=_(
                        "Here you can define what search pattern should be used. "
                        "You can use Kibana query language as described "
                        '<a href="https://www.elastic.co/guide/en/kibana/current/kuery-query.html"'
                        'target="_blank">here</a>. To optimize search speed, use defined indices and fields '
                        "otherwise all indices and fields will be searched."
                    ),
                    allow_empty=False,
                    size=32,
                ),
            ),
            (
                "index",
                ListOfStrings(
                    title=_("Indices to query"),
                    help=_(
                        "Here you can define what index should be queried "
                        "for the defined search. You can query one or "
                        "multiple indices. Without this option all indices "
                        "are queried. If you want to speed up your search, "
                        "use definded indices."
                    ),
                    orientation="horizontal",
                    allow_empty=False,
                    size=48,
                ),
            ),
            (
                "fieldname",
                ListOfStrings(
                    title=_("Fieldnames to query"),
                    help=_(
                        "Here you can define fieldnames that should be used "
                        "in the search. Regexp query is allowed as described "
                        '<a href="https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-regexp-query.html"'
                        'target="_blank">here</a>. If you want to speed up your search, '
                        "use defined indices."
                    ),
                    allow_empty=False,
                    orientation="horizontal",
                    size=32,
                ),
            ),
            (
                "timerange",
                Age(
                    title=_("Timerange"),
                    help=_(
                        "Here you can define the timerange to query, eg. the last x minutes from now. "
                        "The query will then check for the count of log messages in the defined range. "
                        "Default is 1 minute."
                    ),
                    display=["days", "hours", "minutes"],
                    default_value=60,
                ),
            ),
            (
                "count",
                Tuple(
                    title=_("Thresholds on message count"),
                    elements=[
                        Integer(
                            title=_("Warning at or above"),
                            unit=_("log messages"),
                        ),
                        Integer(
                            title=_("Critical at or above"),
                            unit=_("log messages"),
                        ),
                    ],
                ),
            ),
        ],
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupIntegrateOtherServices,
        match_type="all",
        name="active_checks:elasticsearch_query",
        valuespec=_valuespec_active_checks_elasticsearch_query,
    )
)
