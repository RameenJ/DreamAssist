# Schedule Info Card Widget - Complete Guide

A comprehensive Flutter widget that displays contextual, user-friendly messages about daily study schedules based on mood adjustments and makeup tasks.

## 📋 Overview

The `ScheduleInfoCard` widget intelligently informs users about:
- **Mood adjustments**: Why their schedule looks a certain way based on their emotional state
- **Makeup tasks**: Catch-up work from missed sessions
- **Combined context**: When both factors apply to the current day

## 🎯 Features

### ✅ Mood Adjustment Messages
- **Down mood**: "☁️ Your schedule today has been lightened because you weren't feeling your best."
- **Good mood**: "⚡ Great mood! We added a bit more to today's plan."
- **Smart parsing**: Detects "lightened" and "increased" adjustment types
- **Graceful fallback**: Neutral messages when no specific adjustment applies

### ✅ Makeup Task Detection
- **Single missed session**: "📚 Includes catch‑up of 2 tasks from a missed session on 2025-03-15."
- **Multiple missed sessions**: "📚 Includes catch‑up tasks from 3 missed sessions."
- **Flexible inference**: Works with notes fields until backend adds explicit support

### ✅ Combined Messages
- Automatically combines mood adjustments and makeup messages when both apply
- Maintains clear hierarchy and readability
- Non-intrusive card-based design with dismiss option

### ✅ User Experience
- **Dismissible**: Users can close the card; state persists during session
- **Non-intrusive**: Subtle styling with contextual colors
- **Reusable**: Works seamlessly in any schedule view
- **Null-safe**: Gracefully handles missing data

## 📁 File Structure

```
frontend/lib/presentation/
├── widgets/
│   ├── schedule_info_card.dart              # Main widget (production)
│   ├── SCHEDULE_INFO_CARD_INTEGRATION_GUIDE.dart  # How to integrate
│   ├── BACKEND_ENHANCEMENT_GUIDE.py         # Backend recommendations
│   └── README_SCHEDULE_INFO_CARD.md         # This file
```

## 🚀 Quick Start Integration

### Step 1: Import the Widget
```dart
import '../widgets/schedule_info_card.dart';
import '../../core/api/api_models.dart';
```

### Step 2: Add to Your Screen
In your `_buildSessionView()` method, add the `ScheduleInfoCard` after the date/navigation section:

```dart
Widget _buildSessionView(StudySession? session) {
  if (session == null || session.timeBlocks.isEmpty) {
    return _buildEmptyScheduleView();
  }

  return SingleChildScrollView(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Date picker and navigation
        Container(
          padding: const EdgeInsets.all(16),
          // ... your existing date picker
        ),
        const Divider(),

        // 👇 ADD THE SCHEDULE INFO CARD HERE 👇
        ScheduleInfoCard(
          session: session,
          sessionDate: _selectedDay,
          dismissible: true,
          onDismiss: () {
            debugPrint('User dismissed schedule info');
          },
        ),

        // Time blocks section
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            // ... your existing time blocks
          ),
        ),
      ],
    ),
  );
}
```

### Step 3: Done! ✅
The widget automatically displays appropriate messages based on your session data.

## 📊 API Reference

### ScheduleInfoCard Constructor

```dart
ScheduleInfoCard({
  required StudySession? session,        // Session data with mood & time blocks
  required DateTime sessionDate,         // Date of the session
  VoidCallback? onDismiss,              // Optional callback when dismissed
  bool dismissible = true,              // Whether user can dismiss
})
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session` | `StudySession?` | Yes | Study session containing mood and time blocks |
| `sessionDate` | `DateTime` | Yes | The date being displayed |
| `onDismiss` | `VoidCallback?` | No | Called when user dismisses the card |
| `dismissible` | `bool` | No | Enable/disable dismiss button (default: true) |

## 🎨 Styling & Customization

### Color Scheme
The widget uses context-aware colors:
- **Mood adjustments** (down): Orange (`Colors.orange`)
- **Mood adjustments** (good): Amber (`Colors.amber`)
- **Makeup tasks**: Amber (`Colors.amber`)
- **Neutral**: Blue (`Colors.blue`)

### Adjusting Colors
In `schedule_info_card.dart`, modify the color assignments in `_parseMoodAdjustments()`:

```dart
// Example: Change down mood color to red
if (adjustments.any((a) => a.toLowerCase().contains('lighten'))) {
  return MoodInfo(
    title: 'Adjusted Schedule',
    message: '☁️ Your schedule today has been lightened...',
    icon: Icons.cloud,
    color: Colors.red,  // Changed from orange
  );
}
```

### Adjusting Messages
All user-facing messages are in the helper methods:
- `_parseMoodAdjustments()` - Mood-based messages
- `_generateMakeupMessage()` - Makeup task messages

Modify these methods to customize wording.

## 🔧 How It Works

### Mood Adjustment Detection

The widget checks `session.moodAdjustmentsApplied` list for patterns:

```dart
// Example session.moodAdjustmentsApplied content:
[
  "lightened_due_to_down_mood",
  "increased_sessions_due_to_good_mood"
]

// Widget detects "lightened" → shows down mood message
// Widget detects "increased" → shows good mood message
```

### Makeup Task Detection (Current)

Currently infers from `TimeBlock.notes` field:

```dart
bool _isMakeupTask(TimeBlock block) {
  if (block.notes != null && 
      (block.notes!.toLowerCase().contains('makeup') ||
       block.notes!.toLowerCase().contains('missed') ||
       block.notes!.toLowerCase().contains('catch-up'))) {
    return true;
  }
  return false;
}
```

**Note**: This is inference-based. For production, the backend should add explicit fields.

### Message Generation Logic

```
┌─ Check mood adjustments
│  ├─ "lightened" → Down mood message
│  ├─ "increased" → Good mood message
│  └─ Parse mood_at_start for fallback
│
├─ Check makeup tasks
│  ├─ Detect from notes/metadata
│  └─ Group by missed date
│
└─ Combine messages
   ├─ If mood only → Mood message
   ├─ If makeup only → Makeup message
   ├─ If both → Combined message
   └─ If neither → Neutral message
```

## 🔌 Backend Integration (Recommended)

For best results, the backend should provide explicit makeup task fields:

```python
class TimeBlock(BaseModel):
    # ... existing fields ...
    is_makeup: bool = False
    original_scheduled_date: Optional[date] = None
    missed_session_date: Optional[date] = None
```

See `BACKEND_ENHANCEMENT_GUIDE.py` for full implementation details.

### Update ScheduleInfoCard Once Backend Changes

When backend fields are available, simplify `_isMakeupTask()`:

```dart
bool _isMakeupTask(TimeBlock block) {
  return block.isMakeup;  // Simple, explicit check
}
```

## 📱 Display Examples

### Example 1: Down Mood with Lightened Schedule
```
╔════════════════════════════════════════════╗
║ ☁️ ADJUSTED SCHEDULE                       ║
║                                            ║ ✕
║ Your schedule today has been lightened     ║
║ because you weren't feeling your best.     ║
╚════════════════════════════════════════════╝
```

### Example 2: Good Mood with Extra Tasks
```
╔════════════════════════════════════════════╗
║ ⚡ BONUS CHALLENGE                         ║
║                                            ║ ✕
║ Great mood! We added a bit more to         ║
║ today's plan.                              ║
╚════════════════════════════════════════════╝
```

### Example 3: Makeup Tasks from Missed Session
```
╔════════════════════════════════════════════╗
║ 📚 CATCH-UP ITEMS                          ║
║                                            ║ ✕
║ Includes catch‑up of 2 tasks from a        ║
║ missed session on 2025-03-15.              ║
╚════════════════════════════════════════════╝
```

### Example 4: Multiple Missed Sessions
```
╔════════════════════════════════════════════╗
║ 📚 CATCH-UP ITEMS                          ║
║                                            ║ ✕
║ Includes catch‑up tasks from 3 missed      ║
║ sessions.                                  ║
╚════════════════════════════════════════════╝
```

### Example 5: Combined (Mood + Makeup)
```
╔════════════════════════════════════════════╗
║ ☁️ ADJUSTED SCHEDULE                       ║
║                                            ║ ✕
║ Your schedule today has been lightened     ║
║ because you weren't feeling your best.     ║
║                                            ║
║ 📚 Includes catch‑up from sessions you     ║
║ missed on 2025-03-10.                      ║
╚════════════════════════════════════════════╝
```

### Example 6: Neutral (No Info Needed)
```
╔════════════════════════════════════════════╗
║ 📅 YOUR PLAN                               ║
║                                            ║ ✕
║ Here's your plan for today.                ║
╚════════════════════════════════════════════╝
```

## 🧪 Testing

### Unit Test Example

```dart
testWidgets('Shows mood adjustment message', (WidgetTester tester) async {
  final session = StudySession(
    id: '123',
    sessionDate: '2025-03-20',
    timeBlocks: [
      TimeBlock(
        blockId: 'b1',
        taskId: 't1',
        subject: 'Math',
        topic: 'Algebra',
        startTime: '09:00',
        endTime: '10:00',
        durationMins: 60,
        taskType: 'learn',
        difficulty: 0.5,
        completed: false,
      ),
    ],
    moodAtStart: 'down',
    moodAdjustmentsApplied: ['lightened_due_to_down_mood'],
    completedBlocks: 0,
    status: 'scheduled',
  );

  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: ScheduleInfoCard(
          session: session,
          sessionDate: DateTime(2025, 3, 20),
        ),
      ),
    ),
  );

  expect(find.byIcon(Icons.cloud), findsOneWidget);
  expect(find.byType(ScheduleInfoCard), findsOneWidget);
});
```

## 🐛 Troubleshooting

### Card Not Showing
- Verify `session` is not null
- Check that `timeBlocks` is not empty
- Confirm mood or makeup data exists

### Wrong Message Displaying
- Check `mood_at_start` value matches your cases
- Verify `mood_adjustments_applied` list contains expected strings
- Review debug logs for adjustment pattern matching

### Makeup Tasks Not Detected
- Currently relies on keywords in `notes` field
- Ensure backend includes these keywords when marking makeup tasks
- Use explicit backend fields once they're added

### Styling Issues
- Colors are derived from Material theme
- Adjust colors in `_parseMoodAdjustments()` if needed
- Check container padding/margins for spacing

## 📈 Future Enhancements

### Phase 2: Backend Support
- [ ] Add explicit `is_makeup` flag to TimeBlock
- [ ] Add `missed_session_date` to TimeBlock
- [ ] Add `original_scheduled_date` to TimeBlock
- [ ] Remove inference logic once backend fields available

### Phase 3: Advanced Features
- [ ] Show specific topics that need catch-up
- [ ] Display time commitment for makeup tasks
- [ ] Suggest optimal time to tackle makeup work
- [ ] Analytics on completion rate of makeup tasks

### Phase 4: Personalization
- [ ] User preference for message verbosity
- [ ] Toggle mood-based messages on/off
- [ ] Custom message templates
- [ ] Dark mode color variations

## 📚 Related Files

- **Widget**: `schedule_info_card.dart`
- **Integration guide**: `SCHEDULE_INFO_CARD_INTEGRATION_GUIDE.dart`
- **Backend guide**: `BACKEND_ENHANCEMENT_GUIDE.py`
- **API models**: `core/api/api_models.dart`
- **Screen**: `presentation/screens/study_planner/daily_aggregated_schedule_screen.dart`

## 💡 Best Practices

1. **Always pass valid data**: Ensure `session` contains proper `mood_at_start` and `moodAdjustmentsApplied`
2. **Test with edge cases**: Empty sessions, null moods, multiple makeup tasks
3. **Monitor performance**: Card generation is lightweight, but test with many time blocks
4. **Collect user feedback**: Validate that users find messages helpful
5. **Plan backend upgrade**: Start collecting explicit makeup data now

## 📝 Version History

- **v1.0** (Current): Inference-based makeup detection with mood adjustments
- **v1.1** (Planned): Explicit backend fields support
- **v2.0** (Planned): Advanced makeup task analytics

---

**Last Updated**: March 2025  
**Maintained By**: DREAMASSIST Development Team  
**Status**: Production Ready
