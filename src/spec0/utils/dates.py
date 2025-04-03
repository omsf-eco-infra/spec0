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
    # Months are weird because they aren't all the same length.
    total_month = date.month + n_months
    new_year = date.year + (total_month - 1) // 12
    new_month = (total_month - 1) % 12 + 1

    try:
        new_date = date.replace(year=new_year, month=new_month, day=date.day)
    except ValueError:
        # If the target month doesn't have the original day (e.g. February 31),
        # shift to the first day of the next month.
        if new_month == 12:
            new_year += 1
            new_month = 1
        else:
            new_month += 1
        new_date = date.replace(year=new_year, month=new_month, day=1)
    return new_date
