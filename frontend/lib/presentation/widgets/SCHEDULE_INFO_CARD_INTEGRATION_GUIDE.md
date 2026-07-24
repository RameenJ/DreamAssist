/// Integration Guide for ScheduleInfoCard
/// 
/// This guide shows how to integrate the ScheduleInfoCard widget into your
/// DailyAggregatedScheduleScreen to display contextual schedule information.

//import 'package:flutter/material.dart';
//import 'package:intl/intl.dart';
//import '../../core/api/api_models.dart';
//import '../widgets/schedule_info_card.dart';

/// Example: How to integrate ScheduleInfoCard into DailyAggregatedScheduleScreen
/// 
/// In your _buildSessionView() method, add the ScheduleInfoCard right after
/// the date picker section and before the time blocks section:

// ============================================================================
// BEFORE (Current structure):
// ============================================================================
/*
  Widget _buildSessionView(StudySession? session) {
    if (session == null || session.timeBlocks.isEmpty) {
      return _buildEmptyScheduleView();
    }

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Date picker section
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.grey[50],
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ... date and navigation buttons
              ],
            ),
          ),
          const Divider(),

          // 🔴 INSERT SCHEDULE_INFO_CARD HERE 🔴
          
          // Time blocks section
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              // ... time blocks
            ),
          ),
        ],
      ),
    );
  }
*/

// ============================================================================
// AFTER (With ScheduleInfoCard):
// ============================================================================
/*
  Widget _buildSessionView(StudySession? session) {
    if (session == null || session.timeBlocks.isEmpty) {
      return _buildEmptyScheduleView();
    }

    final sessionDate = DateFormat('yyyy-MM-dd').format(_selectedDay);

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Date picker section
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.grey[50],
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  DateFormat('EEEE, MMMM d, yyyy').format(_selectedDay),
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 12),
                // Navigation buttons...
              ],
            ),
          ),
          const Divider(),

          // ✅ ADD THIS: Schedule Info Card
          ScheduleInfoCard(
            session: session,
            sessionDate: _selectedDay,
            dismissible: true,
            onDismiss: () {
              // Optional: Log or handle dismissal
              debugPrint('Schedule info card dismissed for $sessionDate');
            },
          ),

          // Time blocks section
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Tasks',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 12),
                ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: session.timeBlocks.length,
                  itemBuilder: (context, index) {
                    final block = session.timeBlocks[index];
                    return _buildAggregatedTimeBlockCard(block, session.id);
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
*/

// ============================================================================
// ENHANCED: Backend Model Support for Explicit Makeup Task Detection
// ============================================================================
/// 
/// If the backend adds explicit makeup task support, update TimeBlock to include:
///
/// class TimeBlock {
///   final String blockId;
///   final String taskId;
///   final String? planId;
///   final String subject;
///   final String topic;
///   final String startTime;
///   final String endTime;
///   final int durationMins;
///   final String taskType;
///   final double difficulty;
///   final bool completed;
///   
///   // ✅ NEW FIELDS FOR MAKEUP TASK DETECTION:
///   final bool isMakeup;  // Explicit flag from backend
///   final String? originalScheduledDate;  // Original date before rescheduling
///   final String? missedSessionDate;  // Date when task was originally missed
///   
///   TimeBlock({
///     required this.blockId,
///     required this.taskId,
///     this.planId,
///     required this.subject,
///     required this.topic,
///     required this.startTime,
///     required this.endTime,
///     required this.durationMins,
///     required this.taskType,
///     required this.difficulty,
///     required this.completed,
///     this.isMakeup = false,  // NEW
///     this.originalScheduledDate,  // NEW
///     this.missedSessionDate,  // NEW
///   });
///
///   factory TimeBlock.fromJson(Map<String, dynamic> json) {
///     return TimeBlock(
///       blockId: json['block_id'] ?? '',
///       taskId: json['task_id'] ?? '',
///       planId: json['plan_id'],
///       subject: json['subject'] ?? '',
///       topic: json['topic'] ?? '',
///       startTime: json['start_time'] ?? '06:00',
///       endTime: json['end_time'] ?? '07:00',
///       durationMins: _toInt(json['duration_mins'], 60),
///       taskType: json['task_type'] ?? 'learn',
///       difficulty: _toDouble(json['difficulty'], 0.5),
///       completed: json['completed'] ?? false,
///       // NEW: Parse explicit makeup fields
///       isMakeup: json['is_makeup'] ?? false,
///       originalScheduledDate: json['original_scheduled_date'],
///       missedSessionDate: json['missed_session_date'],
///     );
///   }
///
///   Map<String, dynamic> toJson() {
///     return {
///       'block_id': blockId,
///       'task_id': taskId,
///       'plan_id': planId,
///       'subject': subject,
///       'topic': topic,
///       'start_time': startTime,
///       'end_time': endTime,
///       'duration_mins': durationMins,
///       'task_type': taskType,
///       'difficulty': difficulty,
///       'completed': completed,
///       'is_makeup': isMakeup,  // NEW
///       'original_scheduled_date': originalScheduledDate,  // NEW
///       'missed_session_date': missedSessionDate,  // NEW
///     };
///   }
/// }

// ============================================================================
// THEN: Update ScheduleInfoCard to use explicit fields
// ============================================================================
///
/// Once the backend adds these fields, update the _isMakeupTask method:
///
/// bool _isMakeupTask(TimeBlock block) {
///   // First, check explicit flag (preferred)
///   if (block.isMakeup) {
///     return true;
///   }
///
///   // Fallback: check if original date is different from today
///   if (block.originalScheduledDate != null) {
///     try {
///       final originalDate = DateTime.parse(block.originalScheduledDate!);
///       if (originalDate.isBefore(widget.sessionDate)) {
///         return true;
///       }
///     } catch (e) {
///       // Invalid date format, ignore
///     }
///   }
///
///   // Fallback: check notes/metadata
///   if (block.notes != null && 
///       (block.notes!.toLowerCase().contains('makeup') ||
///        block.notes!.toLowerCase().contains('missed') ||
///        block.notes!.toLowerCase().contains('catch-up'))) {
///     return true;
///   }
///
///   return false;
/// }
///
/// And update _getMakeupBlocksByDate:
///
/// Map<String, List<TimeBlock>> _getMakeupBlocksByDate(StudySession session) {
///   final makeupBlocks = <String, List<TimeBlock>>{};
///   
///   for (final block in session.timeBlocks) {
///     if (_isMakeupTask(block)) {
///       // Use explicit date if available, otherwise extract from notes
///       final date = block.missedSessionDate ?? 
///                    _extractMissedDateFromNotes(block.notes ?? '') ??
///                    'previous date';
///       makeupBlocks.putIfAbsent(date, () => []).add(block);
///     }
///   }
///   
///   return makeupBlocks;
/// }

// ============================================================================
// EXAMPLE OUTPUT MESSAGES
// ============================================================================

/// Examples of messages the ScheduleInfoCard will display:

/*
Example 1: Mood adjustment (down mood, schedule lightened)
┌─────────────────────────────────────────────────┐
│ ☁️ ADJUSTED SCHEDULE                            │
│ Your schedule today has been lightened because  │
│ you weren't feeling your best.                  │ ✕
│                                                 │
└─────────────────────────────────────────────────┘

Example 2: Good mood, increased tasks
┌─────────────────────────────────────────────────┐
│ ⚡ BONUS CHALLENGE                              │
│ Great mood! We added a bit more to today's      │
│ plan.                                           │ ✕
│                                                 │
└─────────────────────────────────────────────────┘

Example 3: Makeup tasks only
┌─────────────────────────────────────────────────┐
│ 📚 CATCH-UP ITEMS                               │
│ Includes catch‑up of 2 tasks from a missed      │
│ session on 2025-03-15.                          │ ✕
│                                                 │
└─────────────────────────────────────────────────┘

Example 4: Multiple missed sessions
┌─────────────────────────────────────────────────┐
│ 📚 CATCH-UP ITEMS                               │
│ Includes catch‑up tasks from 2 missed sessions. │ ✕
│                                                 │
└─────────────────────────────────────────────────┘

Example 5: Combined mood + makeup
┌─────────────────────────────────────────────────┐
│ ☁️ ADJUSTED SCHEDULE                            │
│ Your schedule today has been lightened because  │
│ you weren't feeling your best.                  │
│                                                 │
│ 📚 Includes catch‑up from sessions you missed   │
│ on 2025-03-10.                                  │ ✕
│                                                 │
└─────────────────────────────────────────────────┘

Example 6: Neutral (no adjustments)
┌─────────────────────────────────────────────────┐
│ 📅 YOUR PLAN                                    │
│ Here's your plan for today.                     │ ✕
│                                                 │
└─────────────────────────────────────────────────┘
*/
