// Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
// This file is part of Checkmk (https://checkmk.com). It is subject to the
// terms and conditions defined in the file COPYING, which is part of this
// source code package.

#ifndef global_counters_h
#define global_counters_h

#include "config.h"  // IWYU pragma: keep

#include <cstdlib>

// Remember to update num_counters when you change the enum below. C++ really
// lacks a feature to iterate over enums easily...
enum class Counter {
    neb_callbacks,
    requests,
    connections,
    service_checks,
    host_checks,
    metrics,
    perf_data,
    forks,
    log_messages,
    commands,
    livechecks,

    carbon_overflows,
    influxdb_overflows,
    livestatus_overflows,
    rrdcached_overflows
};

// TODO(sp): We really need an OO version of this. :-P
void counterReset(Counter which);
void counterIncrement(Counter which);
void counterIncrementBy(Counter which, std::size_t value);
double counterValue(Counter which);
double counterRate(Counter which);
void do_statistics();

#endif  // global_counters_h
