import 'package:flutter/material.dart';
import '../../core/api/api_models.dart';

/// A widget that displays contextual information about the daily schedule
/// based on mood adjustments.
///
/// Shows user-friendly messages like:
/// - "☁️ Your schedule today has been lightened because you weren't feeling your best."
/// - "⚡ Great mood! We added a bit more to today's plan."
/// - "📅 Here's your plan for today."
class ScheduleInfoCard extends StatefulWidget {
  /// The study session containing schedule data
  final StudySession? session;

  /// The date of the session for context
  final DateTime sessionDate;

  /// Optional callback when the card is dismissed
  final VoidCallback? onDismiss;

  /// Whether the card can be dismissed (defaults to true)
  final bool dismissible;

  const ScheduleInfoCard({
    super.key,
    required this.session,
    required this.sessionDate,
    this.onDismiss,
    this.dismissible = true,
  });

  @override
  State<ScheduleInfoCard> createState() => _ScheduleInfoCardState();
}

class _ScheduleInfoCardState extends State<ScheduleInfoCard> {
  late bool _isDismissed;

  @override
  void initState() {
    super.initState();
    _isDismissed = false;
  }

  /// Generates the schedule information message based on session data
  ScheduleInfoMessage _generateMessage() {
    if (widget.session == null || widget.session!.timeBlocks.isEmpty) {
      return ScheduleInfoMessage(
        title: 'Plan for Today',
        message: '📅 Here\'s your plan for today.',
        icon: Icons.calendar_today,
        color: Colors.blue,
      );
    }

    final session = widget.session!;
    final messages = <String>[];
    String? title;
    Color messageColor = Colors.blue;
    IconData messageIcon = Icons.calendar_today;

    // Check for mood adjustments
    if (session.moodAdjustmentsApplied != null &&
        session.moodAdjustmentsApplied!.isNotEmpty) {
      final moodInfo = _parseMoodAdjustments(
        session.moodAtStart,
        session.moodAdjustmentsApplied ?? [],
      );
      
      messages.add(moodInfo.message);
      messageColor = moodInfo.color;
      messageIcon = moodInfo.icon;
      title = moodInfo.title;
    }

    // If no adjustments, show neutral message
    if (messages.isEmpty) {
      return ScheduleInfoMessage(
        title: 'Your Plan',
        message: '📅 Here\'s your plan for today.',
        icon: Icons.calendar_today,
        color: Colors.blue,
      );
    }

    // Combine all messages
    final combinedMessage = messages.join('\n');

    return ScheduleInfoMessage(
      title: title ?? 'Study Plan',
      message: combinedMessage,
      icon: messageIcon,
      color: messageColor,
    );
  }

  /// Parses mood adjustments and returns appropriate message, icon, and color
  MoodInfo _parseMoodAdjustments(
    String mood,
    List<String> adjustments,
  ) {
    // Check for "lightened" adjustments (down mood)
    if (adjustments.any((a) => a.toLowerCase().contains('lighten'))) {
      return MoodInfo(
        title: 'Adjusted Schedule',
        message: '☁️ Your schedule today has been lightened because you weren\'t feeling your best.',
        icon: Icons.cloud,
        color: Colors.orange,
      );
    }

    // Check for "increased" adjustments (good/motivated mood)
    if (adjustments.any((a) => a.toLowerCase().contains('increas'))) {
      return MoodInfo(
        title: 'Bonus Challenge',
        message: '⚡ Great mood! We added a bit more to today\'s plan.',
        icon: Icons.flash_on,
        color: Colors.amber,
      );
    }

    // Generic mood-based messages
    final lowerMood = mood.toLowerCase();
    
    if (lowerMood.contains('down') || lowerMood.contains('bad') || lowerMood.contains('sad')) {
      return MoodInfo(
        title: 'Supportive Adjustment',
        message: '☁️ Your schedule has been adjusted to match your mood.',
        icon: Icons.cloud,
        color: Colors.orange,
      );
    }

    if (lowerMood.contains('good') || lowerMood.contains('motivated') || lowerMood.contains('confident')) {
      return MoodInfo(
        title: 'Boosted Schedule',
        message: '⚡ Your great mood means we\'ve added some extra challenges!',
        icon: Icons.flash_on,
        color: Colors.amber,
      );
    }

    // Default mood message
    return MoodInfo(
      title: 'Mood Adjustment',
      message: '🎯 Your schedule has been adjusted based on your mood.',
      icon: Icons.sentiment_satisfied,
      color: Colors.blue,
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isDismissed) {
      return const SizedBox.shrink();
    }

    final message = _generateMessage();

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: message.color.withAlpha(25),
        border: Border.all(color: message.color.withAlpha(100)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                message.icon,
                color: message.color,
                size: 20,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      message.title,
                      style: TextStyle(
                        color: message.color,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      message.message,
                      style: TextStyle(
                        color: message.color,
                        fontSize: 12,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
              if (widget.dismissible)
                SizedBox(
                  width: 32,
                  height: 32,
                  child: IconButton(
                    icon: Icon(
                      Icons.close,
                      size: 18,
                      color: message.color,
                    ),
                    onPressed: () {
                      setState(() {
                        _isDismissed = true;
                      });
                      widget.onDismiss?.call();
                    },
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Data class holding schedule information message details
class ScheduleInfoMessage {
  final String title;
  final String message;
  final IconData icon;
  final Color color;

  ScheduleInfoMessage({
    required this.title,
    required this.message,
    required this.icon,
    required this.color,
  });
}

/// Data class holding mood-specific information
class MoodInfo {
  final String title;
  final String message;
  final IconData icon;
  final Color color;

  MoodInfo({
    required this.title,
    required this.message,
    required this.icon,
    required this.color,
  });
}
