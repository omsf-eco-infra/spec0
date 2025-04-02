import datetime


# utils/dates
def get_quarter(date):
    """Convert a date to a quarter as tuple (year, quarter).

    Quarters are 1-indexed.
    """
    return (date.year, ((date.month - 1) // 3) + 1)


def next_quarter(date):
    """Get the next quarter after the given date."""
    year, quarter = get_quarter(date)
    quarter += 1
    if quarter > 4:
        quarter = 1
        year += 1
    return (year, quarter)


def quarter_to_date(quarter):
    """
    Convert a quarter to the date associated with the start of that quarter.
    """
    year, quarter = quarter
    return datetime.datetime(
        year, (quarter - 1) * 3 + 1, 1, tzinfo=datetime.timezone.utc
    )


def shift_date_by_months(date, n_months):
    """Shift a date by a number of months."""
    # used to set the cutoff; if there's a better way to do this, go for it.
    # Months are weird because they aren't all the same length.
    dyears = n_months // 12
    dmonths = n_months % 12
    return date.replace(year=date.year + dyears, month=date.month + dmonths)
