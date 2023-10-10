#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only

def current_date() -> str:
    from datetime import date
    return date.today().isoformat()
