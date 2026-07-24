/// Frontend Datetime Utilities for MongoDB UTC Integration
/// 
/// Implements best practices for handling UTC datetimes from MongoDB:
/// - Store in UTC in backend (verified in UTC_DATETIME_STANDARDS.md)
/// - Convert to local timezone on display (frontend responsibility)
/// - Ensure consistency across the app

import 'package:intl/intl.dart';

/// Datetime utilities for handling MongoDB UTC conversions
class DateTimeUtils {
  /// Parse UTC datetime string from MongoDB and convert to local timezone
  /// 
  /// MongoDB stores: "2026-04-30T15:30:00Z" (ISO 8601 UTC)
  /// Display: "2026-04-30 3:30 PM" (user's local timezone)
  /// 
  /// Example:
  /// ```dart
  /// final mongoUtcString = "2026-04-30T15:30:00Z";
  /// final localDateTime = DateTimeUtils.fromMongoUTC(mongoUtcString);
  /// ```
  static DateTime? fromMongoUTC(String? mongoUtcString) {
    if (mongoUtcString == null || mongoUtcString.isEmpty) {
      return null;
    }

    try {
      // Parse as UTC datetime (MongoDB format)
      final utcDateTime = DateTime.parse(mongoUtcString).toUtc();
      
      // Convert to local timezone
      return utcDateTime.toLocal();
    } catch (e) {
      print('Error parsing MongoDB datetime: $mongoUtcString - $e');
      return null;
    }
  }

  /// Convert local DateTime to UTC ISO format for sending to backend
  /// 
  /// Local: "2026-04-30 3:30 PM EST"
  /// Send to MongoDB: "2026-04-30T19:30:00Z" (UTC)
  /// 
  /// Example:
  /// ```dart
  /// final localDateTime = DateTime.now();
  /// final mongoUtcString = DateTimeUtils.toMongoUTC(localDateTime);
  /// // Send mongoUtcString to backend
  /// ```
  static String toMongoUTC(DateTime localDateTime) {
    // Convert to UTC
    final utcDateTime = localDateTime.toUtc();
    
    // Format as ISO 8601 with Z suffix
    return '${utcDateTime.toIso8601String()}Z';
  }

  /// Format MongoDB UTC datetime for display in user's timezone
  /// 
  /// Example:
  /// ```dart
  /// final mongoString = "2026-04-30T15:30:00Z";
  /// final displayText = DateTimeUtils.formatForDisplay(mongoString);
  /// // Output: "Apr 30, 2026 at 3:30 PM" (in user's local timezone)
  /// ```
  static String formatForDisplay(String? mongoUtcString, {String format = 'MMM dd, yyyy \'at\' h:mm a'}) {
    final localDateTime = fromMongoUTC(mongoUtcString);
    if (localDateTime == null) {
      return 'Invalid date';
    }

    return DateFormat(format).format(localDateTime);
  }

  /// Format date only (no time)
  /// 
  /// Example: "Apr 30, 2026"
  static String formatDateOnly(String? mongoUtcString) {
    return formatForDisplay(mongoUtcString, format: 'MMM dd, yyyy');
  }

  /// Format time only (no date)
  /// 
  /// Example: "3:30 PM"
  static String formatTimeOnly(String? mongoUtcString) {
    return formatForDisplay(mongoUtcString, format: 'h:mm a');
  }

  /// Format with full day name
  /// 
  /// Example: "Wednesday, April 30, 2026 at 3:30 PM"
  static String formatFull(String? mongoUtcString) {
    return formatForDisplay(mongoUtcString, format: 'EEEE, MMMM dd, yyyy \'at\' h:mm a');
  }

  /// Format relative to now (e.g., "2 hours ago", "in 3 days")
  /// 
  /// Example:
  /// ```dart
  /// final mongoString = "2026-04-30T15:30:00Z";
  /// final relativeText = DateTimeUtils.formatRelative(mongoString);
  /// // Output: "Just now", "2 hours ago", "in 3 days", etc.
  /// ```
  static String formatRelative(String? mongoUtcString) {
    final localDateTime = fromMongoUTC(mongoUtcString);
    if (localDateTime == null) {
      return 'Invalid date';
    }

    final now = DateTime.now();
    final difference = now.difference(localDateTime);

    // Future times
    if (difference.isNegative) {
      final absDiff = difference.abs();
      if (absDiff.inSeconds < 60) {
        return 'in ${absDiff.inSeconds} seconds';
      } else if (absDiff.inMinutes < 60) {
        return 'in ${absDiff.inMinutes} minutes';
      } else if (absDiff.inHours < 24) {
        return 'in ${absDiff.inHours} hours';
      } else if (absDiff.inDays < 7) {
        return 'in ${absDiff.inDays} days';
      } else {
        return formatDateOnly(mongoUtcString);
      }
    }

    // Past times
    if (difference.inSeconds < 60) {
      return 'Just now';
    } else if (difference.inMinutes < 60) {
      final mins = difference.inMinutes;
      return '$mins minute${mins > 1 ? 's' : ''} ago';
    } else if (difference.inHours < 24) {
      final hours = difference.inHours;
      return '$hours hour${hours > 1 ? 's' : ''} ago';
    } else if (difference.inDays < 7) {
      final days = difference.inDays;
      return '$days day${days > 1 ? 's' : ''} ago';
    } else {
      return formatDateOnly(mongoUtcString);
    }
  }

  /// Check if a MongoDB UTC datetime is today
  static bool isToday(String? mongoUtcString) {
    final localDateTime = fromMongoUTC(mongoUtcString);
    if (localDateTime == null) return false;

    final now = DateTime.now();
    return localDateTime.year == now.year &&
        localDateTime.month == now.month &&
        localDateTime.day == now.day;
  }

  /// Check if a MongoDB UTC datetime is tomorrow
  static bool isTomorrow(String? mongoUtcString) {
    final localDateTime = fromMongoUTC(mongoUtcString);
    if (localDateTime == null) return false;

    final tomorrow = DateTime.now().add(const Duration(days: 1));
    return localDateTime.year == tomorrow.year &&
        localDateTime.month == tomorrow.month &&
        localDateTime.day == tomorrow.day;
  }

  /// Check if a MongoDB UTC datetime is in the past
  static bool isPast(String? mongoUtcString) {
    final localDateTime = fromMongoUTC(mongoUtcString);
    if (localDateTime == null) return false;

    return localDateTime.isBefore(DateTime.now());
  }

  /// Check if a MongoDB UTC datetime is in the future
  static bool isFuture(String? mongoUtcString) {
    final localDateTime = fromMongoUTC(mongoUtcString);
    if (localDateTime == null) return false;

    return localDateTime.isAfter(DateTime.now());
  }

  /// Get time difference between two MongoDB UTC datetimes
  /// 
  /// Returns: Duration between the two dates
  static Duration? getDifference(String? mongoUTC1, String? mongoUTC2) {
    final dt1 = fromMongoUTC(mongoUTC1);
    final dt2 = fromMongoUTC(mongoUTC2);

    if (dt1 == null || dt2 == null) return null;

    return dt1.difference(dt2);
  }

  /// Parse MongoDB time string (e.g., "09:00:00") to display format
  /// 
  /// Example:
  /// ```dart
  /// final mongoTimeString = "09:00:00";
  /// final displayTime = DateTimeUtils.formatTime(mongoTimeString);
  /// // Output: "9:00 AM"
  /// ```
  static String formatTime(String? mongoTimeString) {
    if (mongoTimeString == null || mongoTimeString.isEmpty) {
      return 'Invalid time';
    }

    try {
      // Parse as time string
      final parts = mongoTimeString.split(':');
      if (parts.length < 2) return 'Invalid time';

      final hour = int.parse(parts[0]);
      final minute = int.parse(parts[1]);

      // Create a dummy date with the time
      final dummy = DateTime(2026, 1, 1, hour, minute);
      
      return DateFormat('h:mm a').format(dummy);
    } catch (e) {
      print('Error parsing time string: $mongoTimeString - $e');
      return 'Invalid time';
    }
  }

  /// Parse MongoDB date string (e.g., "2026-04-30") to display format
  /// 
  /// Example:
  /// ```dart
  /// final mongoDateString = "2026-04-30";
  /// final displayDate = DateTimeUtils.formatDate(mongoDateString);
  /// // Output: "Apr 30, 2026"
  /// ```
  static String formatDate(String? mongoDateString) {
    if (mongoDateString == null || mongoDateString.isEmpty) {
      return 'Invalid date';
    }

    try {
      final dateOnly = DateTime.parse(mongoDateString);
      return DateFormat('MMM dd, yyyy').format(dateOnly);
    } catch (e) {
      print('Error parsing date string: $mongoDateString - $e');
      return 'Invalid date';
    }
  }

  /// Convert local DateTime to date-only string (YYYY-MM-DD format for API)
  /// 
  /// Example:
  /// ```dart
  /// final now = DateTime.now();
  /// final dateStr = DateTimeUtils.toDateString(now);
  /// // Output: "2026-04-30"
  /// ```
  static String toDateString(DateTime dateTime) {
    return DateFormat('yyyy-MM-dd').format(dateTime);
  }

  /// Convert local DateTime to time-only string (HH:MM:SS format for API)
  /// 
  /// Example:
  /// ```dart
  /// final now = DateTime.now();
  /// final timeStr = DateTimeUtils.toTimeString(now);
  /// // Output: "15:30:45"
  /// ```
  static String toTimeString(DateTime dateTime) {
    return DateFormat('HH:mm:ss').format(dateTime);
  }
}

/// Extension methods for convenient datetime operations
extension MongoDateTimeExtension on String? {
  /// Convert MongoDB UTC datetime to local and format for display
  /// 
  /// Example:
  /// ```dart
  /// String mongoDateTime = "2026-04-30T15:30:00Z";
  /// print(mongoDateTime.toLocal()); // "Apr 30, 2026 at 3:30 PM"
  /// ```
  String toLocal({String format = 'MMM dd, yyyy \'at\' h:mm a'}) {
    return DateTimeUtils.formatForDisplay(this, format: format);
  }

  /// Check if this MongoDB datetime is today
  /// 
  /// Example:
  /// ```dart
  /// if (mongoDateTime.isToday()) { ... }
  /// ```
  bool isToday() => DateTimeUtils.isToday(this);

  /// Check if this MongoDB datetime is in the past
  /// 
  /// Example:
  /// ```dart
  /// if (mongoDateTime.isPast()) { ... }
  /// ```
  bool isPast() => DateTimeUtils.isPast(this);

  /// Check if this MongoDB datetime is in the future
  /// 
  /// Example:
  /// ```dart
  /// if (mongoDateTime.isFuture()) { ... }
  /// ```
  bool isFuture() => DateTimeUtils.isFuture(this);

  /// Format as relative time (e.g., "2 hours ago")
  /// 
  /// Example:
  /// ```dart
  /// print(mongoDateTime.toRelative()); // "2 hours ago"
  /// ```
  String toRelative() => DateTimeUtils.formatRelative(this);
}
