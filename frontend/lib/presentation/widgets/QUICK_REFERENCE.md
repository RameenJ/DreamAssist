# ScheduleInfoCard - Quick Reference

## 🚀 TL;DR - In 60 Seconds

### What Does It Do?
Displays user-friendly messages about why today's schedule looks a certain way.

### Import & Use
```dart
import '../widgets/schedule_info_card.dart';

// In your _buildSessionView():
ScheduleInfoCard(
  session: session,
  sessionDate: _selectedDay,
  dismissible: true,
)
```

### Messages It Shows
- **Down mood**: "☁️ Your schedule today has been lightened..."
- **Good mood**: "⚡ Great mood! We added a bit more..."
- **Makeup tasks**: "📚 Includes catch‑up from sessions you missed..."
- **Combined**: Both messages together
- **Neutral**: "📅 Here's your plan for today."

---

## 📋 Message Decision Tree

```
┌─ Session has mood_adjustments_applied?
│  ├─ YES → Check adjustment type
│  │  ├─ "lightened" → Show down mood message
│  │  └─ "increased" → Show good mood message
│  └─ NO → Continue to makeup check
│
├─ Session has makeup tasks?
│  ├─ YES (single date) → "Includes catch‑up of N tasks from [date]"
│  └─ YES (multiple) → "Includes catch‑up tasks from N sessions"
│
└─ Neither? → Show neutral message "📅 Here's your plan for today"
```

---

## 🎨 Quick Customization

### Change Message Text
Edit `_parseMoodAdjustments()` or `_generateMakeupMessage()`:
```dart
message: 'Your custom message here',
```

### Change Colors
```dart
color: Colors.red,  // Instead of orange
```

### Disable Dismissal
```dart
ScheduleInfoCard(
  // ...
  dismissible: false,
)
```

### Add Callback
```dart
ScheduleInfoCard(
  // ...
  onDismiss: () {
    print('User dismissed!');
  },
)
```

---

## 🔍 Data Requirements

| Field | Required | Source | Format |
|-------|----------|--------|--------|
| `session` | Yes | Provider | StudySession object |
| `sessionDate` | Yes | Screen state | DateTime |
| `mood_at_start` | No | session object | "down", "neutral", "good" |
| `mood_adjustments_applied` | No | session object | List of strings |
| `timeBlocks` | Yes | session object | List of TimeBlock |
| `TimeBlock.notes` | No | session object | String (for makeup detection) |

---

## ✅ Testing Checklist

- [ ] Widget appears on screen
- [ ] Shows correct message for session mood
- [ ] Detects makeup tasks (if notes contain keywords)
- [ ] Dismiss button works
- [ ] No console errors
- [ ] Colors look good
- [ ] Text is readable

---

## 🐛 Quick Fixes

### Widget Not Showing
→ Check if session.timeBlocks is empty

### Wrong Message
→ Check session.moodAdjustmentsApplied list contents

### Makeup Tasks Not Detected
→ Ensure TimeBlock.notes contains "makeup" or "missed" or "catch-up"

### Import Error
→ Verify path: `lib/presentation/widgets/schedule_info_card.dart`

---

## 📁 File Locations

```
frontend/lib/presentation/widgets/
├── schedule_info_card.dart          ← Main widget (production)
├── README_SCHEDULE_INFO_CARD.md     ← Full documentation
├── IMPLEMENTATION_SUMMARY.md        ← Roadmap & overview
├── CONCRETE_INTEGRATION_EXAMPLE.dart    ← Code example
├── SCHEDULE_INFO_CARD_INTEGRATION_GUIDE.dart  ← Integration steps
└── BACKEND_ENHANCEMENT_GUIDE.py     ← Future improvements
```

---

## 🔗 Quick Links

- **Full README**: `README_SCHEDULE_INFO_CARD.md`
- **Integration Steps**: `SCHEDULE_INFO_CARD_INTEGRATION_GUIDE.dart`
- **Code Example**: `CONCRETE_INTEGRATION_EXAMPLE.dart`
- **Roadmap**: `IMPLEMENTATION_SUMMARY.md`

---

## 📞 Key Methods

| Method | Purpose | Input | Output |
|--------|---------|-------|--------|
| `_generateMessage()` | Creates message object | session | ScheduleInfoMessage |
| `_isMakeupTask()` | Checks if block is makeup | TimeBlock | bool |
| `_parseMoodAdjustments()` | Parses mood info | mood, adjustments | MoodInfo |
| `_generateMakeupMessage()` | Creates makeup message | makeupMap | String |

---

## 🎯 Success Indicators

✅ Widget displays below date picker  
✅ Shows appropriate message for session  
✅ Can be dismissed  
✅ No errors in console  
✅ Looks good with app theme  

---

## 📊 Message Examples

```
┌─────────────────────────────┐
│ ☁️ ADJUSTED SCHEDULE        │
│ Your schedule has been      │ ✕
│ lightened...                │
└─────────────────────────────┘

┌─────────────────────────────┐
│ ⚡ BONUS CHALLENGE          │
│ Great mood! We added more...│ ✕
└─────────────────────────────┘

┌─────────────────────────────┐
│ 📚 CATCH-UP ITEMS           │
│ Includes catch‑up from 2    │ ✕
│ missed sessions.            │
└─────────────────────────────┘
```

---

## 💡 Pro Tips

1. **Test early**: Add widget before perfecting integration
2. **Save defaults**: Copy base colors before customizing
3. **Check logs**: Use debugPrint for mood/adjustment values
4. **Iterate**: Get feedback before major changes
5. **Plan backend**: Add explicit makeup fields soon

---

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| Widget won't show | Verify session.timeBlocks is not empty |
| Wrong message | Print session.moodAdjustmentsApplied to debug |
| Makeup not detected | Ensure notes contain "makeup"/"missed" |
| Build error | Run `flutter pub get` |
| Import fails | Check file path spelling |

---

**Status**: Production Ready ✅  
**Version**: 1.0  
**Time to Implement**: ~15 minutes  
**Difficulty**: Easy  

👉 **Ready?** Start with `CONCRETE_INTEGRATION_EXAMPLE.dart`
