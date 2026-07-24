import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:go_router/go_router.dart';
import '../../providers/study_planner_provider.dart';
import '../../../core/api/api_models.dart';

// ============= Utility Classes =============

/// Represents completion status indicators for a day
class DayCompletionStatus {
  final int totalBlocks;
  final int completedBlocks;
  
  DayCompletionStatus({
    required this.totalBlocks,
    required this.completedBlocks,
  });

  /// Get indicator: ● (fully completed), ◔ (partial), ○ (no tasks)
  String get indicator {
    if (totalBlocks == 0) return '○';
    if (completedBlocks == totalBlocks) return '●';
    if (completedBlocks > 0) return '◔';
    return '○';
  }

  /// Get completion percentage (0-100)
  int get completionPercentage {
    if (totalBlocks == 0) return 0;
    return ((completedBlocks / totalBlocks) * 100).toInt();
  }
}

/// Color scheme for task types
class TaskTypeColors {
  static Color getColorForTaskType(String taskType) {
    switch (taskType.toLowerCase()) {
      case 'learn':
        return Colors.blue;
      case 'revise':
        return Colors.orange;
      case 'practice':
        return Colors.green;
      case 'test':
        return Colors.red;
      default:
        return Colors.indigo;
    }
  }

  static Color getLightColorForTaskType(String taskType) {
    return getColorForTaskType(taskType).withOpacity(0.15);
  }

  static IconData getIconForTaskType(String taskType) {
    switch (taskType.toLowerCase()) {
      case 'learn':
        return Icons.school;
      case 'revise':
        return Icons.refresh;
      case 'practice':
        return Icons.assignment;
      case 'test':
        return Icons.assessment;
      default:
        return Icons.task_alt;
    }
  }
}

/// Represents a deadline item
class DeadlineItem {
  final String title; // "subject / topic"
  final DateTime dueDate;
  final int daysLeft;
  final String type; // 'plan_end' or 'task_deadline'
  final String? planId;

  DeadlineItem({
    required this.title,
    required this.dueDate,
    required this.daysLeft,
    required this.type,
    this.planId,
  });

  bool get isOverdue => daysLeft < 0;
  bool get isDueToday => daysLeft == 0;
  bool get isDueSoon => daysLeft > 0 && daysLeft <= 3;
}

// ============= Main Widget =============

class WeeklyScheduleScreen extends ConsumerStatefulWidget {
  final DateTime? initialDate;

  const WeeklyScheduleScreen({
    super.key,
    this.initialDate,
  });

  @override
  ConsumerState<WeeklyScheduleScreen> createState() =>
      _WeeklyScheduleScreenState();
}

class _WeeklyScheduleScreenState extends ConsumerState<WeeklyScheduleScreen> {
  late DateTime _weekStartDate;
  late ScrollController _dayScrollController;
  late ScrollController _timetableScrollController;
  
  static const int _startHour = 6; // Work hours start at 6 AM
  static const int _endHour = 22; // Work hours end at 10 PM
  static const int _hourHeight = 60;
  static const double _dayTileWidth = 75.0;

  @override
  void initState() {
    super.initState();
    // Calculate week start (Monday)
    final date = widget.initialDate ?? DateTime.now();
    final dayOfWeek = date.weekday; // 1 = Monday, 7 = Sunday
    _weekStartDate = date.subtract(Duration(days: dayOfWeek - 1));
    
    _dayScrollController = ScrollController();
    _timetableScrollController = ScrollController();
  }

  @override
  void dispose() {
    _dayScrollController.dispose();
    _timetableScrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Weekly Schedule'),
        elevation: 0,
        centerTitle: true,
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Center(
              child: Text(
                '${DateFormat('MMM d').format(_weekStartDate)} - ${DateFormat('MMM d').format(_weekStartDate.add(const Duration(days: 6)))}',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Compact day selector with completion indicators
          _buildCompactDaySelector(),

          const Divider(height: 1),

          // Timetable with synchronized scrolling
          Expanded(
            child: _buildTimetableSection(),
          ),

          // Upcoming deadlines section
          _buildUpcomingDeadlinesSection(),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCreateDeadlineDialog(context),
        tooltip: 'Add Deadline',
        child: const Icon(Icons.add),
      ),
    );
  }

  /// Build compact day selector with completion indicators
  Widget _buildCompactDaySelector() {
    return Container(
      height: 80,
      color: Colors.grey[50],
      child: SingleChildScrollView(
        controller: _dayScrollController,
        scrollDirection: Axis.horizontal,
        child: Row(
          children: List.generate(7, (dayIndex) {
            final date = _weekStartDate.add(Duration(days: dayIndex));
            final isToday = DateFormat('yyyy-MM-dd').format(date) ==
                DateFormat('yyyy-MM-dd').format(DateTime.now());
            final sessionDate = DateFormat('yyyy-MM-dd').format(date);
            final sessionAsync =
                ref.watch(aggregatedSessionByDateProvider(sessionDate));

            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
              child: GestureDetector(
                onTap: () {
                  context.push('/daily-schedule', extra: date);
                },
                child: sessionAsync.when(
                  data: (session) {
                    final status = DayCompletionStatus(
                      totalBlocks: session?.timeBlocks.length ?? 0,
                      completedBlocks:
                          session?.timeBlocks.where((b) => b.completed).length ?? 0,
                    );

                    return Container(
                      width: _dayTileWidth,
                      decoration: BoxDecoration(
                        color: isToday ? Colors.blue[50] : Colors.white,
                        border: Border.all(
                          color: isToday ? Colors.blue : Colors.grey[300]!,
                          width: isToday ? 2 : 1,
                        ),
                        borderRadius: BorderRadius.circular(8),
                        boxShadow: isToday
                            ? [
                                BoxShadow(
                                  color: Colors.blue.withOpacity(0.2),
                                  blurRadius: 4,
                                )
                              ]
                            : null,
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          // Day name
                          Text(
                            DateFormat('EEE').format(date),
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 9,
                              color: isToday ? Colors.blue : Colors.grey[600],
                            ),
                          ),
                          // Day number
                          Text(
                            '${date.day}',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                              color: isToday ? Colors.blue : Colors.black,
                            ),
                          ),
                          // Completion indicator + text (side-by-side)
                          if (status.totalBlocks == 0)
                            Text(
                              status.indicator,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey[400],
                              ),
                            )
                          else
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  status.indicator,
                                  style: TextStyle(
                                    fontSize: 14,
                                    color: status.completedBlocks > 0
                                        ? Colors.green
                                        : Colors.grey[400],
                                  ),
                                ),
                                const SizedBox(width: 2),
                                Text(
                                  '${status.completedBlocks}/${status.totalBlocks}',
                                  style: TextStyle(
                                    fontSize: 7,
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ],
                            ),
                        ],
                      ),
                    );
                  },
                  loading: () => Container(
                    width: _dayTileWidth,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: Border.all(color: Colors.grey[300]!),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Center(
                      child: SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 1.5),
                      ),
                    ),
                  ),
                  error: (_, _) => Container(
                    width: _dayTileWidth,
                    decoration: BoxDecoration(
                      color: Colors.red[50],
                      border: Border.all(color: Colors.red[300]!),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Center(
                      child: Icon(Icons.error_outline,
                          size: 16, color: Colors.red[400]),
                    ),
                  ),
                ),
              ),
            );
          }),
        ),
      ),
    );
  }

  /// Build timetable section.
  ///
  /// Layout: vertical scroll (outer) → horizontal scroll (inner) → fixed-width
  /// Column with day-headers + hour rows.  This keeps the SizedBox well within
  /// the Expanded constraint and avoids RenderFlex overflow while still allowing
  /// the user to scroll both axes.
  Widget _buildTimetableSection() {
    final totalWidth = 50.0 + (7 * 100.0); // time col + 7 day cols

    return ListView(
      // Vertical scroll handled by ListView
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        SingleChildScrollView(
          // Horizontal scroll only
          scrollDirection: Axis.horizontal,
          controller: _timetableScrollController,
          child: SizedBox(
            width: totalWidth,
            child: Column(
              children: [
                _buildDayHeaders(),
                ..._buildHourRows(),
              ],
            ),
          ),
        ),
      ],
    );
  }

  /// Build day header row (Monday, Tuesday, etc.) - compact version
  Widget _buildDayHeaders() {
    return Row(
        children: [
          // Time column header
          Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              color: Colors.grey[200],
              border: Border.all(color: Colors.grey[300]!),
            ),
            child: const Center(
              child: Text(
                'Time',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 10),
              ),
            ),
          ),
        // Day columns
        ...List.generate(7, (dayIndex) {
          final date = _weekStartDate.add(Duration(days: dayIndex));
          final isToday = DateFormat('yyyy-MM-dd').format(date) ==
              DateFormat('yyyy-MM-dd').format(DateTime.now());

          return Container(
            width: 100,
            height: 50,
            decoration: BoxDecoration(
              color: isToday ? Colors.blue[100] : Colors.grey[50],
              border: Border.all(
                color: isToday ? Colors.blue : Colors.grey[300]!,
                width: isToday ? 2 : 1,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  DateFormat('EEE').format(date),
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: isToday ? Colors.blue : Colors.black,
                    fontSize: 10,
                  ),
                ),
                Text(
                  '${date.day}',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: isToday ? Colors.blue : Colors.grey,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }

  /// Build hour rows with time blocks and color-coded cells
  List<Widget> _buildHourRows() {
    final rows = List.generate(_endHour - _startHour, (hourIndex) {
      final hour = _startHour + hourIndex;
      final nextHour = hour + 1;

      return Row(
        children: [
          // Time label - fixed on left
          Container(
            width: 50,
            height: _hourHeight.toDouble(),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              border: Border.all(color: Colors.grey[300]!),
            ),
            child: Center(
              child: Text(
                '${hour.toString().padLeft(2, '0')}:00',
                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w500),
              ),
            ),
          ),
          // Day cells with time blocks - horizontally scrollable
          ...List.generate(7, (dayIndex) {
            final date = _weekStartDate.add(Duration(days: dayIndex));
            final sessionDate = DateFormat('yyyy-MM-dd').format(date);
            final sessionAsync =
                ref.watch(aggregatedSessionByDateProvider(sessionDate));

            return sessionAsync.when(
              data: (session) {
                print('🔍 Checking $sessionDate: blocks = ${session?.timeBlocks.length ?? 0}');
                if (session != null && session.timeBlocks.isNotEmpty) {
                  print('   First block: ${session.timeBlocks.first.startTime} - ${session.timeBlocks.first.endTime}');
                }

                final blocksInHour = session?.timeBlocks
                    .where((block) {
                      final startTime = _parseTime(block.startTime);
                      final endTime = _parseTime(block.endTime);
                      final startMinutes = startTime.hour * 60 + startTime.minute;
                      final endMinutes = endTime.hour * 60 + endTime.minute;
                      final slotStart = hour * 60;
                      final slotEnd = (hour + 1) * 60;
                      final overlaps = startMinutes < slotEnd && endMinutes > slotStart;
                      if (overlaps) {
                        print('   ✅ Block ${block.topic} belongs to hour $hour');
                      }
                      return overlaps;
                    })
                    .toList() ??
                    [];

                print('   Hour $hour: ${blocksInHour.length} blocks');

                return GestureDetector(
                  onTap: () {
                    // Navigate to daily schedule for this date
                    context.push('/daily-schedule', extra: date);
                  },
                  child: Container(
                    width: 100,
                    height: _hourHeight.toDouble(),
                    decoration: BoxDecoration(
                      color: blocksInHour.isEmpty
                          ? Colors.white
                          : Colors.grey[50],
                      border: Border.all(color: Colors.grey[300]!),
                    ),
                    child: blocksInHour.isEmpty
                        ? const SizedBox.shrink()
                        : Padding(
                            padding: const EdgeInsets.all(3),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: blocksInHour
                                  .take(2) // Show max 2 blocks to avoid overflow
                                  .map((block) {
                                final isCompleted = block.completed;
                                final bgColor = TaskTypeColors.getLightColorForTaskType(
                                    block.taskType);
                                final borderColor =
                                    TaskTypeColors.getColorForTaskType(block.taskType);
                                final icon = TaskTypeColors.getIconForTaskType(
                                    block.taskType);

                                return Flexible(
                                  child: Container(
                                    padding: const EdgeInsets.all(2),
                                    margin: const EdgeInsets.only(bottom: 2),
                                    decoration: BoxDecoration(
                                      color: isCompleted
                                          ? Colors.green.withOpacity(0.2)
                                          : bgColor,
                                      borderRadius: BorderRadius.circular(2),
                                      border: Border.all(
                                        color: isCompleted ? Colors.green : borderColor,
                                        width: 0.5,
                                      ),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(icon,
                                            size: 10,
                                            color: isCompleted
                                                ? Colors.green
                                                : borderColor),
                                        const SizedBox(width: 2),
                                        Expanded(
                                          child: Text(
                                            block.topic,
                                            style: TextStyle(
                                              fontSize: 8,
                                              fontWeight: FontWeight.bold,
                                              color: isCompleted
                                                  ? Colors.green[700]
                                                  : Colors.grey[800],
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                            maxLines: 1,
                                          ),
                                        ),
                                        if (isCompleted)
                                          const Icon(Icons.check,
                                              size: 8, color: Colors.green),
                                      ],
                                    ),
                                  ),
                                );
                              }).toList(),
                            ),
                          ),
                  ),
                );
              },
              loading: () => Container(
                width: 100,
                height: _hourHeight.toDouble(),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: const Center(
                  child: SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 1.5),
                  ),
                ),
              ),
              error: (error, stack) => Container(
                width: 100,
                height: _hourHeight.toDouble(),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey[300]!),
                  color: Colors.red[50],
                ),
                child: const Icon(Icons.error_outline, size: 14, color: Colors.red),
              ),
            );
          }),
        ],
      );
    });
    print('DEBUG: Built ${rows.length} hour rows');
    return rows;
  }

  /// Build upcoming deadlines section
  Widget _buildUpcomingDeadlinesSection() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.grey[50],
        border: Border(top: BorderSide(color: Colors.grey[300]!)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Icon(Icons.calendar_today, size: 16, color: Colors.grey[600]),
                const SizedBox(width: 8),
                Text(
                  'Upcoming Deadlines (Next 30 days)',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey[700],
                  ),
                ),
              ],
            ),
          ),
          SizedBox(
            height: 70,
            child: _buildDeadlinesList(),
          ),
        ],
      ),
    );
  }

  /// Build horizontally scrollable deadlines list using Riverpod provider
  Widget _buildDeadlinesList() {
    return Consumer(
      builder: (context, ref, child) {
        final deadlinesAsync = ref.watch(upcomingDeadlinesDefaultProvider);
        
        return deadlinesAsync.when(
          data: (deadlines) {
            if (deadlines.isEmpty) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    'No upcoming deadlines',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
              );
            }
            
            return SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  const SizedBox(width: 12),
                  ...deadlines.map((deadline) {
                    return _buildDeadlineCard(deadline, ref);
                  }),
                  const SizedBox(width: 12),
                ],
              ),
            );
          },
          loading: () => SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                const SizedBox(width: 12),
                ...List.generate(3, (_) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: Container(
                      width: 140,
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(6),
                      ),
                    ),
                  );
                }),
                const SizedBox(width: 12),
              ],
            ),
          ),
          error: (err, stack) => SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Text(
                'Error loading deadlines',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.red[400],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  /// Build a single deadline card with action buttons
  Widget _buildDeadlineCard(UserDeadline deadline, WidgetRef ref) {
    final color = _getDeadlineColor(deadline);
    
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: GestureDetector(
        onLongPress: () {
          // Show delete confirmation
          showDialog(
            context: context,
            builder: (dialogContext) => AlertDialog(
              title: const Text('Delete Deadline?'),
              content: Text('Delete "${deadline.title}"?'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(dialogContext),
                  child: const Text('Cancel'),
                ),
                TextButton(
                  onPressed: () {
                    Navigator.pop(dialogContext);
                    _deleteDeadline(deadline.id, ref);
                  },
                  child: const Text('Delete', style: TextStyle(color: Colors.red)),
                ),
              ],
            ),
          );
        },
        child: Container(
          width: 140,
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(color: Colors.grey[300]!),
            borderRadius: BorderRadius.circular(6),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 2,
              )
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Status tag
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(3),
                  ),
                  child: Text(
                    deadline.statusLabel,
                    style: TextStyle(
                      fontSize: 8,
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                ),
                const SizedBox(height: 4),
                // Title with type icon
                Expanded(
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _getDeadlineTypeIcon(deadline.deadlineType),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          deadline.title,
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            overflow: TextOverflow.ellipsis,
                          ),
                          maxLines: 2,
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                // Days left + Complete button
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      deadline.isDueToday
                          ? 'Today'
                          : '${deadline.daysLeft} day${deadline.daysLeft.abs() == 1 ? '' : 's'} ${deadline.isOverdue ? 'ago' : 'left'}',
                      style: TextStyle(
                        fontSize: 9,
                        color: Colors.grey[600],
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (!deadline.completed)
                      GestureDetector(
                        onTap: () => _markDeadlineCompleted(deadline.id, ref),
                        child: Icon(
                          Icons.check_circle_outline,
                          size: 14,
                          color: Colors.green[600],
                        ),
                      )
                    else
                      Icon(
                        Icons.check_circle,
                        size: 14,
                        color: Colors.green[600],
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// Get color for deadline status
  Color _getDeadlineColor(UserDeadline deadline) {
    if (deadline.completed) return Colors.green;
    if (deadline.isOverdue) return Colors.red;
    if (deadline.isDueToday) return Colors.orange;
    if (deadline.isDueSoon) return Colors.amber;
    return Colors.blue;
  }

  /// Get icon for deadline type
  Widget _getDeadlineTypeIcon(String type) {
    IconData iconData;
    switch (type.toLowerCase()) {
      case 'assignment':
        iconData = Icons.assignment;
        break;
      case 'quiz':
        iconData = Icons.quiz;
        break;
      case 'exam':
        iconData = Icons.school;
        break;
      default:
        iconData = Icons.task_alt;
    }
    return Icon(iconData, size: 12, color: Colors.grey[600]);
  }

  /// Mark deadline as completed
  void _markDeadlineCompleted(String deadlineId, WidgetRef ref) async {
    final service = ref.read(studyPlannerServiceProvider);
    try {
      await service.markDeadlineCompleted(deadlineId);
      ref.invalidate(upcomingDeadlinesDefaultProvider);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  /// Delete a deadline
  void _deleteDeadline(String deadlineId, WidgetRef ref) async {
    final service = ref.read(studyPlannerServiceProvider);
    try {
      await service.deleteDeadline(deadlineId);
      ref.invalidate(upcomingDeadlinesDefaultProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Deadline deleted')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  /// Show dialog to create a new deadline
  void _showCreateDeadlineDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (dialogContext) => _CreateDeadlineDialog(
        onCreateDeadline: (title, dueDate, type, description) {
          _createDeadlineAndRefresh(title, dueDate, type, description);
          Navigator.pop(dialogContext);
        },
      ),
    );
  }

  /// Create a deadline and refresh the provider
  void _createDeadlineAndRefresh(
    String title,
    DateTime dueDate,
    String type,
    String? description,
  ) async {
    final service = ref.read(studyPlannerServiceProvider);
    try {
      await service.createDeadline(
        title: title,
        dueDate: dueDate,
        deadlineType: type,
        description: description,
      );
      ref.invalidate(upcomingDeadlinesDefaultProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Deadline created successfully')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error creating deadline: $e')),
        );
      }
    }
  }

  /// Parse time string (HH:MM) to DateTime for comparison (used by timetable)
  DateTime _parseTime(String timeStr) {
    try {
      final parts = timeStr.split(':');
      final hour = int.parse(parts[0]);
      final minute = int.parse(parts[1]);
      return DateTime(2024, 1, 1, hour, minute);
    } catch (e) {
      return DateTime(2024, 1, 1, 0, 0);
    }
  }
}

// ============= Create Deadline Dialog Widget =============

class _CreateDeadlineDialog extends StatefulWidget {
  final Function(String title, DateTime dueDate, String type, String? description)
      onCreateDeadline;

  const _CreateDeadlineDialog({
    required this.onCreateDeadline,
  });

  @override
  State<_CreateDeadlineDialog> createState() => _CreateDeadlineDialogState();
}

class _CreateDeadlineDialogState extends State<_CreateDeadlineDialog> {
  late TextEditingController _titleController;
  late TextEditingController _descriptionController;
  DateTime _selectedDate = DateTime.now().add(const Duration(days: 1));
  String _selectedType = 'assignment';

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController();
    _descriptionController = TextEditingController();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add New Deadline'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title field
            TextField(
              controller: _titleController,
              decoration: InputDecoration(
                hintText: 'e.g., Math Assignment 3',
                labelText: 'Title *',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              maxLength: 255,
            ),
            const SizedBox(height: 16),
            
            // Date picker
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Due Date *',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
                const SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey[400]!),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: ListTile(
                    title: Text(DateFormat('MMM dd, yyyy').format(_selectedDate)),
                    trailing: const Icon(Icons.calendar_today),
                    onTap: () async {
                      final pickedDate = await showDatePicker(
                        context: context,
                        initialDate: _selectedDate,
                        firstDate: DateTime.now(),
                        lastDate: DateTime.now().add(const Duration(days: 365)),
                      );
                      if (pickedDate != null) {
                        setState(() {
                          _selectedDate = pickedDate;
                        });
                      }
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Type dropdown
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Type *',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  initialValue: _selectedType,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  items: const [
                    DropdownMenuItem(value: 'assignment', child: Text('Assignment')),
                    DropdownMenuItem(value: 'quiz', child: Text('Quiz')),
                    DropdownMenuItem(value: 'exam', child: Text('Exam')),
                    DropdownMenuItem(value: 'other', child: Text('Other')),
                  ],
                  onChanged: (value) {
                    if (value != null) {
                      setState(() {
                        _selectedType = value;
                      });
                    }
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Description field
            TextField(
              controller: _descriptionController,
              decoration: InputDecoration(
                hintText: 'Optional notes (e.g., topics to cover)',
                labelText: 'Description (optional)',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              maxLines: 3,
              maxLength: 1000,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _submitDeadline,
          child: const Text('Create'),
        ),
      ],
    );
  }

  void _submitDeadline() {
    if (_titleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a title')),
      );
      return;
    }

    widget.onCreateDeadline(
      _titleController.text.trim(),
      _selectedDate,
      _selectedType,
      _descriptionController.text.trim().isEmpty
          ? null
          : _descriptionController.text.trim(),
    );
  }
}
