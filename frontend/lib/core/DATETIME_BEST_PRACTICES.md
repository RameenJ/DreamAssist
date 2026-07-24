# MongoDB UTC DateTime Best Practices - Implementation Guide

## 📋 Quick Summary

**Backend (MongoDB Storage)**:
- ✅ Always store datetime in UTC using `datetime.utcnow()`
- ✅ Convert date objects to datetime: `datetime.combine(date_obj, time.min)`
- ✅ Store time objects as ISO strings: `time_obj.isoformat()`
- ✅ Reference: `backend/UTC_DATETIME_STANDARDS.md`

**Frontend (Display to Users)**:
- ✅ Parse UTC strings received from backend
- ✅ Convert to local timezone for display
- ✅ Use `DateTimeUtils` class for all conversions
- ✅ Reference: `core/datetime_utils.dart`

---

## 🎯 Integration Points in DREAMASSIST

### 1. **Schedule Info Card - DateTime Usage**

Location: `frontend/lib/presentation/widgets/schedule_info_card.dart`

The widget works with:
- `session.sessionDate` - Date string (e.g., "2026-04-30")
- `session.moodAtStart` - Mood at session start
- `timeBlocks` - Contains missed session dates

**Usage in ScheduleInfoCard**:
```dart
// Already handles datetime display internally
// The widget receives DateTime and displays appropriately
final formattedDate = DateFormat('MMMM d, yyyy').format(sessionDate);
```

---

### 2. **DailyAggregatedScheduleScreen - DateTime Handling**

Location: `frontend/lib/presentation/screens/study_planner/daily_aggregated_schedule_screen.dart`

**When fetching session data**:
```dart
// Convert date to string format for API query
final sessionDate = DateFormat('yyyy-MM-dd').format(_selectedDay);
final sessionAsync = ref.watch(aggregatedSessionByDateProvider(sessionDate));
```

**When displaying dates**:
```dart
// Format date for user display
final displayDate = DateFormat('EEEE, MMMM d, yyyy').format(_selectedDay);
```

---

### 3. **Using DateTimeUtils for Conversions**

#### For MongoDB UTC datetime strings (from backend):
```dart
import 'core/datetime_utils.dart';

// Parse and convert to local timezone
final mongoUTC = "2026-04-30T15:30:00Z";  // From backend
final localDateTime = DateTimeUtils.fromMongoUTC(mongoUTC);

// Format for display
final displayText = DateTimeUtils.formatForDisplay(mongoUTC);
// Output: "Apr 30, 2026 at 3:30 PM" (in user's timezone)

// Or use extension method:
final displayText2 = mongoUTC.toLocal();
```

#### For sending to backend:
```dart
// Convert local DateTime to UTC for backend
final localDateTime = DateTime.now();
final mongoUTC = DateTimeUtils.toMongoUTC(localDateTime);
// Result: "2026-04-30T19:30:00Z"
```

#### For time strings from backend:
```dart
// Backend sends: "09:00:00"
final displayTime = DateTimeUtils.formatTime("09:00:00");
// Output: "9:00 AM"
```

#### For date strings from backend:
```dart
// Backend sends: "2026-04-30"
final displayDate = DateTimeUtils.formatDate("2026-04-30");
// Output: "Apr 30, 2026"
```

---

## 🔄 Data Flow Examples

### Example 1: Displaying a Session Date

```dart
// 1. Backend returns UTC datetime
final response = {
  "session_date": "2026-04-30",
  "started_at": "2026-04-30T15:30:00Z",
  "completed_at": null
};

// 2. Parse into model
final session = StudySession.fromJson(response);

// 3. Display with timezone conversion
Text(DateTimeUtils.formatDate(session.sessionDate));
// Local display: "Apr 30, 2026" (already local since it's date-only)

Text(DateTimeUtils.formatForDisplay(session.startedAt));
// Local display: "Apr 30, 2026 at 3:30 PM" (converted to local tz)
```

### Example 2: Checking if Task is Overdue

```dart
// Backend returns UTC datetime
final taskDeadline = "2026-04-30T09:00:00Z";

// Check if past (automatically converts to local tz)
if (DateTimeUtils.isPast(taskDeadline)) {
  print("Task is overdue!");
}

// Or use extension:
if (taskDeadline.isPast()) {
  print("Task is overdue!");
}
```

### Example 3: Displaying Relative Times

```dart
// Backend returns UTC datetime
final completedAt = "2026-04-28T14:30:00Z";

// Display as relative time
Text(DateTimeUtils.formatRelative(completedAt));
// Output examples: "2 days ago", "Just now", "in 3 hours"

// Or use extension:
Text(completedAt.toRelative());
```

---

## 📱 Common UI Patterns

### Display Date for Today

```dart
// Check if date is today
if (DateTimeUtils.isToday(mongoDateTime)) {
  return Text("Today at ${DateTimeUtils.formatTime(mongoDateTime)}");
} else {
  return Text(DateTimeUtils.formatDateOnly(mongoDateTime));
}
```

### Display Smart Date Format

```dart
// Show "Today", "Tomorrow", "Yesterday", or actual date
String getSmartDateLabel(String? mongoDateTime) {
  if (mongoDateTime == null) return "No date";
  
  if (mongoDateTime.isToday()) return "Today";
  if (mongoDateTime.isTomorrow()) return "Tomorrow";
  if (DateTime.now().subtract(Duration(days: 1)).toString().startsWith(
        DateTimeUtils.formatDate(mongoDateTime).substring(0, 10))) {
    return "Yesterday";
  }
  
  return DateTimeUtils.formatDateOnly(mongoDateTime);
}
```

### Display Session Timeline

```dart
// Show when session started and completed
if (session.startedAt != null) {
  print("Started: ${DateTimeUtils.formatRelative(session.startedAt)}");
}
if (session.completedAt != null) {
  print("Completed: ${DateTimeUtils.formatRelative(session.completedAt)}");
}
```

---

## 🔐 Important Notes

### ❌ Don't Do This

```dart
// WRONG: Parsing without timezone conversion
final date = DateTime.parse(mongoUtcString);  // Stays in UTC!
print(date);  // Shows UTC, not local

// WRONG: Using local time for backend
final local = DateTime.now();
// Send directly to backend (WRONG - should be UTC)
```

### ✅ Do This Instead

```dart
// RIGHT: Convert to local for display
final localDate = DateTimeUtils.fromMongoUTC(mongoUtcString);
print(localDate);  // Shows in user's timezone

// RIGHT: Convert to UTC for backend
final utcString = DateTimeUtils.toMongoUTC(DateTime.now());
// Send utcString to backend
```

---

## 📊 Timezone Examples

**Scenario**: Backend returns UTC datetime: `"2026-04-30T15:30:00Z"`

| User Timezone | Converted Time | Display |
|---|---|---|
| EST (UTC-5) | 2026-04-30 10:30 AM | Apr 30, 2026 at 10:30 AM |
| PST (UTC-8) | 2026-04-30 07:30 AM | Apr 30, 2026 at 7:30 AM |
| IST (UTC+5:30) | 2026-04-30 8:00 PM | Apr 30, 2026 at 8:00 PM |
| GMT (UTC+0) | 2026-04-30 3:30 PM | Apr 30, 2026 at 3:30 PM |

---

## 🧪 Testing DateTime Handling

### Unit Test Example

```dart
void main() {
  test('Convert MongoDB UTC to local timezone', () {
    final mongoUTC = "2026-04-30T15:30:00Z";
    final local = DateTimeUtils.fromMongoUTC(mongoUTC);
    
    expect(local, isNotNull);
    expect(local!.year, 2026);
    expect(local.month, 4);
    expect(local.day, 30);
    // Time will be in local timezone
  });

  test('Convert local DateTime to MongoDB UTC', () {
    final local = DateTime(2026, 4, 30, 15, 30, 0);
    final mongoUTC = DateTimeUtils.toMongoUTC(local);
    
    expect(mongoUTC, contains('Z'));  // Has UTC suffix
    expect(mongoUTC, isNotEmpty);
  });

  test('Format for display', () {
    final mongoUTC = "2026-04-30T15:30:00Z";
    final display = DateTimeUtils.formatForDisplay(mongoUTC);
    
    expect(display, contains('Apr'));
    expect(display, contains('2026'));
  });
}
```

---

## 📚 File References

| File | Purpose | Status |
|------|---------|--------|
| `backend/UTC_DATETIME_STANDARDS.md` | Backend UTC standards | ✅ Verified |
| `backend/DATETIME_COMPLIANCE_STATUS.md` | Backend compliance | ✅ Compliant |
| `frontend/core/datetime_utils.dart` | Frontend conversion utilities | ✅ Implemented |
| `frontend/core/api/FUTURE_MODEL_UPDATES.dart` | Model enhancement guide | ✅ Reference |

---

## 🚀 Integration Checklist

- [x] Backend uses UTC for all datetime storage
- [x] Frontend imports `DateTimeUtils` in relevant screens
- [x] ScheduleInfoCard integrated in DailyAggregatedScheduleScreen
- [x] All datetime displays use `DateTimeUtils.format*()` methods
- [x] All datetime sends to backend use `DateTimeUtils.toMongoUTC()`
- [x] Timezone conversions handle all edge cases (null, invalid formats)
- [x] Extension methods available for convenience

---

## 📞 Quick Reference

### Most Common Operations

```dart
// Import
import 'package:dreamassist/core/datetime_utils.dart';

// Display UTC from backend
mongoDateTime.toLocal();                    // Simple display
DateTimeUtils.formatForDisplay(mongoUTC);   // With custom format
mongoDateTime.toRelative();                 // Relative time

// Check dates
mongoDateTime.isToday();
mongoDateTime.isPast();
mongoDateTime.isFuture();

// Send to backend
DateTimeUtils.toMongoUTC(DateTime.now());

// Format components
DateTimeUtils.formatDate("2026-04-30");     // "Apr 30, 2026"
DateTimeUtils.formatTime("09:00:00");       // "9:00 AM"
```

---

**Status**: ✅ Complete Integration Ready  
**Last Updated**: April 30, 2026  
**Backend Standard**: UTC (Verified Compliant)  
**Frontend Support**: DateTimeUtils (Fully Implemented)
