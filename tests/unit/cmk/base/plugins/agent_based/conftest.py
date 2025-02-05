#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import pytest

# This fixture is autoused, because adding it to all existing plugin tests would be too tedious.
# Please do not extend its scope, but use it explicitly if needed.


@pytest.fixture(autouse=True, scope="function")
def _autouse_initialised_item_state(initialised_item_state):
    pass
