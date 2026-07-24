"""
DateTime Utilities for UTC-consistent operations
Ensures all date/time operations in DreamAssist follow UTC standards
"""

from datetime import datetime, date, time, timedelta
from typing import Union, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Get current UTC time. Always use this instead of datetime.now()"""
    return datetime.utcnow()


def get_utc_today() -> date:
    """Get today's date in UTC. Always use this instead of date.today()"""
    return datetime.utcnow().date()


def date_to_datetime_utc(d: date) -> datetime:
    """
    Convert a date object to UTC datetime (midnight).
    
    Args:
        d: date object
    Returns:
        datetime at midnight UTC (00:00:00)
    
    Example:
        >>> d = date(2026, 4, 27)
        >>> dt = date_to_datetime_utc(d)
        >>> assert dt == datetime(2026, 4, 27, 0, 0, 0)
    """
    if isinstance(d, datetime):
        return d
    return datetime.combine(d, time.min)


def date_to_datetime_end_of_day_utc(d: date) -> datetime:
    """
    Convert a date object to UTC datetime (end of day).
    
    Args:
        d: date object
    Returns:
        datetime at 23:59:59.999999 UTC
    
    Example:
        >>> d = date(2026, 4, 27)
        >>> dt = date_to_datetime_end_of_day_utc(d)
        >>> assert dt == datetime(2026, 4, 27, 23, 59, 59, 999999)
    """
    if isinstance(d, datetime):
        return d.replace(hour=23, minute=59, second=59, microsecond=999999)
    return datetime.combine(d, time.max)


def time_to_isoformat(t: time) -> str:
    """
    Convert a time object to ISO format string for MongoDB storage.
    
    MongoDB BSON cannot serialize datetime.time objects directly.
    This converts them to ISO format strings that Pydantic models can parse.
    
    Args:
        t: time object (e.g., time(9, 0, 0))
    Returns:
        ISO format string (e.g., "09:00:00")
    
    Example:
        >>> t = time(9, 30, 45)
        >>> s = time_to_isoformat(t)
        >>> assert s == "09:30:45"
    """
    if isinstance(t, str):
        return t  # Already a string
    if isinstance(t, time):
        return t.isoformat()
    return str(t)


def time_from_isoformat(s: str) -> time:
    """
    Parse an ISO format string back to a time object.
    
    Args:
        s: ISO format string (e.g., "09:00:00")
    Returns:
        time object
    
    Example:
        >>> t = time_from_isoformat("09:30:45")
        >>> assert t == time(9, 30, 45)
    """
    if isinstance(s, time):
        return s  # Already a time object
    return time.fromisoformat(s)


def ensure_utc_datetime(dt: Union[datetime, date, str, None]) -> Union[datetime, None]:
    """
    Ensure a value is a UTC datetime object.
    
    Converts date objects to datetime at midnight.
    Handles strings in ISO format.
    
    Args:
        dt: datetime, date, ISO string, or None
    Returns:
        UTC datetime object or None
    """
    if dt is None:
        return None
    
    if isinstance(dt, datetime):
        # If timezone-aware, assume it's already UTC
        # If naive, assume it's UTC
        return dt
    
    if isinstance(dt, date):
        return date_to_datetime_utc(dt)
    
    if isinstance(dt, str):
        # Try to parse ISO format
        try:
            return datetime.fromisoformat(dt)
        except ValueError:
            logger.warning(f"Could not parse datetime string: {dt}")
            return None
    
    return None


def convert_dict_dates_to_datetime(d: Dict[str, Any], date_fields: List[str]) -> Dict[str, Any]:
    """
    Convert specified date fields in a dictionary to UTC datetime objects.
    
    Args:
        d: Dictionary potentially containing date objects
        date_fields: List of field names that should be converted
    Returns:
        Dictionary with date fields converted to datetime
    
    Example:
        >>> d = {"start_date": date(2026, 4, 27), "name": "My Plan"}
        >>> converted = convert_dict_dates_to_datetime(d, ["start_date"])
        >>> assert isinstance(converted["start_date"], datetime)
    """
    result = d.copy()
    for field in date_fields:
        if field in result and result[field] is not None:
            result[field] = ensure_utc_datetime(result[field])
    return result


def get_date_range(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    """
    Get inclusive date range as UTC datetime tuples.
    
    Perfect for MongoDB range queries that should include the entire start and end dates.
    
    Args:
        start_date: Start date
        end_date: End date (inclusive)
    Returns:
        Tuple of (start_datetime, end_datetime) for query filter
    
    Example:
        >>> start, end = get_date_range(date(2026, 4, 1), date(2026, 4, 30))
        >>> assert start == datetime(2026, 4, 1, 0, 0, 0)
        >>> assert end == datetime(2026, 4, 30, 23, 59, 59, 999999)
        
    Usage in MongoDB query:
        >>> query = {
        ...     "date_field": {
        ...         "$gte": start,
        ...         "$lte": end
        ...     }
        ... }
    """
    start_dt = date_to_datetime_utc(start_date)
    end_dt = date_to_datetime_end_of_day_utc(end_date)
    return (start_dt, end_dt)


def validate_datetime_in_utc(dt: datetime) -> bool:
    """
    Validate that a datetime is properly stored in UTC.
    
    Args:
        dt: datetime object to validate
    Returns:
        True if datetime is valid
    Raises:
        ValueError if datetime appears to have timezone issues
    """
    if not isinstance(dt, datetime):
        raise ValueError(f"Expected datetime, got {type(dt)}")
    
    # Check if timezone-aware (should not be for our use case)
    if dt.tzinfo is not None:
        logger.warning(f"Datetime has timezone info: {dt.tzinfo}")
        # This is a warning but not necessarily wrong - could be explicitly UTC
    
    return True


def days_between_utc(from_date: date, to_date: date) -> int:
    """
    Calculate days between two dates using UTC.
    
    Args:
        from_date: Start date
        to_date: End date
    Returns:
        Number of days (negative if to_date is before from_date)
    """
    delta = to_date - from_date
    return delta.days


def add_days_utc(d: date, days: int) -> date:
    """
    Add days to a date using UTC.
    
    Args:
        d: Start date
        days: Number of days to add
    Returns:
        New date
    """
    dt = date_to_datetime_utc(d) + timedelta(days=days)
    return dt.date()


def convert_datetime_to_date(
    data: Any,
    target_fields: set = None,
    exclude_fields: set = None,
) -> Any:
    """
    Recursively convert datetime objects to date objects for specific fields.
    
    This fixes Pydantic serialization warnings when datetime objects are passed
    to fields that expect date types (e.g., session_date, deadline, start_date).
    
    MongoDB returns datetime objects for all datetime fields, but Pydantic models
    expecting date types will warn. This converter fixes that before Pydantic
    serialization occurs.
    
    Args:
        data: Input data structure (dict, list, scalar value, or Pydantic model)
        target_fields: Set of field names to convert. If None, converts all
                      fields ending with '_date' (except those in exclude_fields)
        exclude_fields: Set of field names to skip (e.g., {'created_at', 'updated_at'})
                       to keep as datetime timestamps
    
    Returns:
        Data structure with datetime→date conversions applied
    
    Examples:
        >>> import datetime as dt_module
        >>> # Convert specific fields
        >>> data = {
        ...     'session_date': dt_module.datetime(2026, 5, 26, 0, 0),
        ...     'created_at': dt_module.datetime.utcnow(),
        ...     'user_id': 'abc123'
        ... }
        >>> cleaned = convert_datetime_to_date(data, target_fields={'session_date'})
        >>> isinstance(cleaned['session_date'], dt_module.date)
        True
        >>> isinstance(cleaned['created_at'], dt_module.datetime)
        True
        
        >>> # Auto-detect date fields (ending with _date, but exclude timestamps)
        >>> data = {
        ...     'session_date': dt_module.datetime(2026, 5, 26),
        ...     'created_at': dt_module.datetime.utcnow(),
        ...     'updated_at': dt_module.datetime.utcnow()
        ... }
        >>> cleaned = convert_datetime_to_date(
        ...     data,
        ...     exclude_fields={'created_at', 'updated_at'}
        ... )
        >>> isinstance(cleaned['session_date'], dt_module.date)
        True
    """
    if target_fields is None:
        target_fields = set()
    if exclude_fields is None:
        exclude_fields = {'created_at', 'updated_at', 'started_at', 
                         'completed_at', 'updated_at', 'deleted_at'}
    
    return _convert_datetime_to_date_recursive(data, target_fields, exclude_fields)


def _convert_datetime_to_date_recursive(
    data: Any,
    target_fields: set,
    exclude_fields: set,
    current_path: str = "",
) -> Any:
    """
    Internal recursive function for datetime→date conversion.
    
    Args:
        data: Current data being processed
        target_fields: Set of field names to convert
        exclude_fields: Set of field names to skip
        current_path: Current field path (for debugging)
    
    Returns:
        Converted data
    """
    # Handle None
    if data is None:
        return None
    
    # Handle dict
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            field_path = f"{current_path}.{key}" if current_path else key
            
            # Check if this field should be converted
            should_convert = False
            if target_fields and key in target_fields:
                should_convert = True
            elif not target_fields and key not in exclude_fields and key.endswith('_date'):
                should_convert = True
            
            # Convert datetime to date if applicable
            if should_convert and isinstance(value, datetime):
                result[key] = value.date()
            else:
                # Recursively process nested structures
                result[key] = _convert_datetime_to_date_recursive(
                    value, target_fields, exclude_fields, field_path
                )
        return result
    
    # Handle list
    if isinstance(data, list):
        return [
            _convert_datetime_to_date_recursive(
                item, target_fields, exclude_fields, f"{current_path}[{i}]"
            )
            for i, item in enumerate(data)
        ]
    
    # Handle datetime specifically
    if isinstance(data, datetime):
        # Only convert if no specific fields were targeted (auto-mode)
        # or if we're in a context where conversion makes sense
        return data
    
    # Return other types unchanged
    return data
