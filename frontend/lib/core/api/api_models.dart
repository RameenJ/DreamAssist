/// API Models for Study Planner
/// These models represent the data structures used in API requests/responses
library;

import 'package:intl/intl.dart';

// Helper function to safely convert values to int
int _toInt(dynamic value, int defaultValue) {
  if (value == null) return defaultValue;
  if (value is int) return value;
  if (value is double) return value.toInt();
  if (value is String) return int.tryParse(value) ?? defaultValue;
  return defaultValue;
}

// Helper function to safely convert values to double
// Handles string values like "easy", "medium", "hard", "low", "moderate", "high"
double _toDouble(dynamic value, double defaultValue) {
  if (value == null) return defaultValue;
  if (value is double) return value;
  if (value is int) return value.toDouble();
  if (value is String) {
    // Try to parse as number first
    final parsed = double.tryParse(value);
    if (parsed != null) return parsed;
    
    // Handle difficulty/pace string values
    switch (value.toLowerCase().trim()) {
      case 'easy': return 1.0;
      case 'medium': return 2.0;
      case 'hard': return 3.0;
      case 'low': return 1.0;
      case 'moderate': return 2.0;
      case 'high': return 3.0;
      default: return defaultValue;
    }
  }
  return defaultValue;
}

// Study Plan Models
class StudyTask {
  final String id;
  final String subject;
  final String topic;
  final String taskType; // learn, revise, practice
  final double difficulty;
  final int estimatedTimeMins;
  final double priorityScore;
  final String deadline;
  final String status; // pending, scheduled, completed, missed, skipped

  StudyTask({
    required this.id,
    required this.subject,
    required this.topic,
    required this.taskType,
    required this.difficulty,
    required this.estimatedTimeMins,
    required this.priorityScore,
    required this.deadline,
    required this.status,
  });

  factory StudyTask.fromJson(Map<String, dynamic> json) {
    return StudyTask(
      id: json['_id'] ?? '',
      subject: json['subject'] ?? '',
      topic: json['topic'] ?? '',
      taskType: json['task_type'] ?? 'learn',
      difficulty: _toDouble(json['difficulty'], 0.5),
      estimatedTimeMins: _toInt(json['estimated_time_mins'], 45),
      priorityScore: _toDouble(json['priority_score'], 0.5),
      deadline: json['deadline'] ?? '',
      status: json['status'] ?? 'pending',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      '_id': id,
      'subject': subject,
      'topic': topic,
      'task_type': taskType,
      'difficulty': difficulty,
      'estimated_time_mins': estimatedTimeMins,
      'priority_score': priorityScore,
      'deadline': deadline,
      'status': status,
    };
  }
}

class TimeBlock {
  final String blockId;
  final String taskId;
  final String? planId; // Plan that this task belongs to (null for non-aggregated sessions)
  final String subject;
  final String topic;
  final String startTime;
  final String endTime;
  final int durationMins;
  final String taskType;
  final double difficulty;
  final bool completed;
  
  // Makeup task support
  final bool isMakeup;
  final String? originalScheduledDate;
  final String? missedSessionDate;

  TimeBlock({
    required this.blockId,
    required this.taskId,
    this.planId,
    required this.subject,
    required this.topic,
    required this.startTime,
    required this.endTime,
    required this.durationMins,
    required this.taskType,
    required this.difficulty,
    required this.completed,
    this.isMakeup = false,
    this.originalScheduledDate,
    this.missedSessionDate,
  });

  factory TimeBlock.fromJson(Map<String, dynamic> json) {
    return TimeBlock(
      blockId: json['block_id'] ?? '',
      taskId: json['task_id'] ?? '',
      planId: json['plan_id'],
      subject: json['subject'] ?? '',
      topic: json['topic'] ?? '',
      startTime: json['start_time'] ?? '06:00',
      endTime: json['end_time'] ?? '07:00',
      durationMins: _toInt(json['duration_mins'], 60),
      taskType: json['task_type'] ?? 'learn',
      difficulty: _toDouble(json['difficulty'], 0.5),
      completed: json['completed'] ?? false,
      isMakeup: json['is_makeup'] ?? false,
      originalScheduledDate: json['original_scheduled_date'],
      missedSessionDate: json['missed_session_date'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'block_id': blockId,
      'task_id': taskId,
      'plan_id': planId,
      'subject': subject,
      'topic': topic,
      'start_time': startTime,
      'end_time': endTime,
      'duration_mins': durationMins,
      'task_type': taskType,
      'difficulty': difficulty,
      'completed': completed,
      'is_makeup': isMakeup,
      'original_scheduled_date': originalScheduledDate,
      'missed_session_date': missedSessionDate,
    };
  }

  /// Get human-readable format of missed session date
  /// Example: "2025-03-15" → "March 15, 2025"
  String? get formattedMissedDate {
    if (missedSessionDate == null) return null;
    try {
      final date = DateTime.parse(missedSessionDate!);
      return DateFormat('MMMM d, yyyy').format(date);
    } catch (e) {
      return missedSessionDate; // Fallback to original format
    }
  }

  /// Check if this is a makeup task from a date in the past
  bool get isMakeupFromPastDate {
    if (!isMakeup || missedSessionDate == null) return false;
    try {
      final missedDate = DateTime.parse(missedSessionDate!);
      return missedDate.isBefore(DateTime.now());
    } catch (e) {
      return false;
    }
  }
}

class StudySession {
  final String id;
  final String? planId; // null for aggregated sessions across multiple plans
  final List<String>? aggregatedPlanIds; // plan IDs that contributed tasks to this session
  final String sessionDate;
  final List<TimeBlock> timeBlocks;
  final String moodAtStart;
  final String? moodAtEnd;
  final int completedBlocks;
  final String status; 
  final List<String>? moodAdjustmentsApplied;// pending, in_progress, completed, missed, skipped

  
  StudySession({
    required this.id,
    this.planId,
    this.aggregatedPlanIds,
    required this.sessionDate,
    required this.timeBlocks,
    required this.moodAtStart,
    this.moodAtEnd,
    required this.completedBlocks,
    required this.status,
    this.moodAdjustmentsApplied,   // add this line
  });

  /// Check if this is an aggregated session across multiple plans
  bool get isAggregated => planId == null && aggregatedPlanIds != null && aggregatedPlanIds!.isNotEmpty;

  factory StudySession.fromJson(Map<String, dynamic> json) {
    return StudySession(
      id: json['session_id'] ?? json['_id'] ?? '',
      planId: json['plan_id'],
      aggregatedPlanIds: json['aggregated_plan_ids'] != null
          ? List<String>.from(json['aggregated_plan_ids'] as List)
          : null,
      sessionDate: json['session_date'] ?? '',
      timeBlocks: (json['time_blocks'] as List?)
          ?.map((block) => TimeBlock.fromJson(block))
          .toList() ??
          [],
      moodAtStart: json['mood_at_start'] ?? 'neutral',
      moodAtEnd: json['mood_at_end'],
      completedBlocks: _toInt(json['completed_blocks'], 0),
      status: json['status'] ?? 'pending',
      moodAdjustmentsApplied: json['mood_adjustments_applied'] != null
          ? List<String>.from(json['mood_adjustments_applied'] as List)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      '_id': id,
      'plan_id': planId,
      'aggregated_plan_ids': aggregatedPlanIds,
      'session_date': sessionDate,
      'time_blocks': timeBlocks.map((block) => block.toJson()).toList(),
      'mood_at_start': moodAtStart,
      'mood_at_end': moodAtEnd,
      'completed_blocks': completedBlocks,
      'status': status,
    };
  }
}

class StudyPlan {
  final String id;
  final String planName;
  final List<String> subjects;
  final String startDate;
  final String endDate;
  final String mode; // unified, per_subject
  final String status; // active, paused, completed
  final double totalAvailableHours;
  final String studyPace; // slow, moderate, fast
  final int scheduledSessions;
  final int completedSessions;
  final int missedSessions;
  final double completionRate;
  final double productivityScore;
  final bool autoRescheduleEnabled;

  StudyPlan({
    required this.id,
    required this.planName,
    required this.subjects,
    required this.startDate,
    required this.endDate,
    required this.mode,
    required this.status,
    required this.totalAvailableHours,
    required this.studyPace,
    required this.scheduledSessions,
    required this.completedSessions,
    required this.missedSessions,
    required this.completionRate,
    required this.productivityScore,
    required this.autoRescheduleEnabled,
  });

  factory StudyPlan.fromJson(Map<String, dynamic> json) {
    // 🔧 Parse plan ID - backend now returns '_id' from MongoDB
    // Try in order of preference: _id (MongoDB standard), then id, then plan_id (legacy)
    final planId = json['_id'] ?? json['id'] ?? json['plan_id'] ?? '';
    
    if (planId.isEmpty) {
      throw Exception('StudyPlan.fromJson: No valid ID found. JSON: $json');
    }
    
    return StudyPlan(
      id: planId,
      planName: json['plan_name'] ?? '',
      subjects: List<String>.from(json['subjects'] ?? []),
      startDate: json['start_date'] ?? '',
      endDate: json['end_date'] ?? '',
      mode: json['mode'] ?? 'unified',
      status: json['status'] ?? 'active',
      totalAvailableHours: (json['total_available_hours'] ?? 20).toDouble(),
      studyPace: json['study_pace'] ?? 'moderate',
      scheduledSessions: _toInt(json['scheduled_sessions'], 0),
      completedSessions: _toInt(json['completed_sessions'], 0),
      missedSessions: _toInt(json['missed_sessions'], 0),
      completionRate: (json['completion_rate'] ?? 0.0).toDouble(),
      productivityScore: (json['productivity_score'] ?? 0.0).toDouble(),
      autoRescheduleEnabled: json['auto_reschedule_enabled'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'plan_name': planName,
      'subjects': subjects,
      'start_date': startDate,
      'end_date': endDate,
      'mode': mode,
      'status': status,
      'total_available_hours': totalAvailableHours,
      'study_pace': studyPace,
      'scheduled_sessions': scheduledSessions,
      'completed_sessions': completedSessions,
      'missed_sessions': missedSessions,
      'completion_rate': completionRate,
      'productivity_score': productivityScore,
      'auto_reschedule_enabled': autoRescheduleEnabled,
    };
  }
}

class PlanAnalytics {
  final String planId;
  final double overallCompletionRate;
  final double productivityScore;
  final Map<String, double> subjectCompletion;
  final Map<String, int> moodDistribution;
  final List<WeeklySummary> weeklySummaries;

  PlanAnalytics({
    required this.planId,
    required this.overallCompletionRate,
    required this.productivityScore,
    required this.subjectCompletion,
    required this.moodDistribution,
    required this.weeklySummaries,
  });

  factory PlanAnalytics.fromJson(Map<String, dynamic> json) {
    return PlanAnalytics(
      planId: json['plan_id'] ?? '',
      overallCompletionRate: (json['overall_completion_rate'] ?? 0.0).toDouble(),
      productivityScore: (json['productivity_score'] ?? 0.0).toDouble(),
      subjectCompletion: Map<String, double>.from(
        (json['subject_completion'] as Map?)?.map(
              (k, v) => MapEntry(k as String, (v as num).toDouble()),
            ) ??
            {},
      ),
      moodDistribution: Map<String, int>.from(
        (json['mood_distribution'] as Map?)?.map(
              (k, v) => MapEntry(k as String, v as int),
            ) ??
            {},
      ),
      weeklySummaries: (json['weekly_summaries'] as List?)
          ?.map((week) => WeeklySummary.fromJson(week))
          .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'plan_id': planId,
      'overall_completion_rate': overallCompletionRate,
      'productivity_score': productivityScore,
      'subject_completion': subjectCompletion,
      'mood_distribution': moodDistribution,
      'weekly_summaries': weeklySummaries.map((w) => w.toJson()).toList(),
    };
  }
}

class WeeklySummary {
  final int week;
  final double completionRate;
  final double averageMood;
  final int totalSessionsPlanned;
  final int totalSessionsCompleted;

  WeeklySummary({
    required this.week,
    required this.completionRate,
    required this.averageMood,
    required this.totalSessionsPlanned,
    required this.totalSessionsCompleted,
  });

  factory WeeklySummary.fromJson(Map<String, dynamic> json) {
    return WeeklySummary(
      week: _toInt(json['week'], 0),
      completionRate: (json['completion_rate'] ?? 0.0).toDouble(),
      averageMood: (json['avg_mood'] ?? 0.5).toDouble(),
      totalSessionsPlanned: _toInt(json['total_sessions_planned'], 0),
      totalSessionsCompleted: _toInt(json['total_sessions_completed'], 0),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'week': week,
      'completion_rate': completionRate,
      'avg_mood': averageMood,
      'total_sessions_planned': totalSessionsPlanned,
      'total_sessions_completed': totalSessionsCompleted,
    };
  }
}

// User Deadlines Models
class UserDeadline {
  final String id;
  final String title;
  final DateTime dueDate;
  final String deadlineType; // assignment, quiz, exam, other
  final String? description;
  final bool completed;
  final DateTime createdAt;
  final int daysLeft; // Computed field
  
  UserDeadline({
    required this.id,
    required this.title,
    required this.dueDate,
    required this.deadlineType,
    this.description,
    required this.completed,
    required this.createdAt,
    required this.daysLeft,
  });

  factory UserDeadline.fromJson(Map<String, dynamic> json) {
    final dueDateStr = json['due_date'] as String?;
    final dueDate = dueDateStr != null ? DateTime.parse(dueDateStr) : DateTime.now();
    final createdAtStr = json['created_at'] as String?;
    final createdAt = createdAtStr != null ? DateTime.parse(createdAtStr) : DateTime.now();
    
    return UserDeadline(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      dueDate: dueDate,
      deadlineType: json['deadline_type'] ?? 'other',
      description: json['description'],
      completed: json['completed'] ?? false,
      createdAt: createdAt,
      daysLeft: _toInt(json['days_left'], 0),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'due_date': dueDate.toIso8601String().split('T')[0],
      'deadline_type': deadlineType,
      'description': description,
      'completed': completed,
      'created_at': createdAt.toIso8601String(),
      'days_left': daysLeft,
    };
  }

  // Helper getters for status
  bool get isOverdue => daysLeft < 0;
  bool get isDueToday => daysLeft == 0;
  bool get isDueSoon => daysLeft > 0 && daysLeft <= 3;
  String get statusLabel {
    if (isOverdue) return 'OVERDUE';
    if (isDueToday) return 'TODAY';
    if (isDueSoon) return 'DUE SOON';
    return 'UPCOMING';
  }
}
