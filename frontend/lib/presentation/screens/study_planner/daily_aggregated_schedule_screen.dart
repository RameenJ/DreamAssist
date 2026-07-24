import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:dio/dio.dart';
import '../../../core/api/api_models.dart';
import '../../providers/study_planner_provider.dart';
import '../../providers/task_timer_provider.dart';
import '../../widgets/schedule_info_card.dart';

class DailyAggregatedScheduleScreen extends ConsumerStatefulWidget {
  final DateTime? initialDate;

  const DailyAggregatedScheduleScreen({
    super.key,
    this.initialDate,
  });

  @override
  ConsumerState<DailyAggregatedScheduleScreen> createState() =>
      _DailyAggregatedScheduleScreenState();
}

class _DailyAggregatedScheduleScreenState
    extends ConsumerState<DailyAggregatedScheduleScreen> {
  late DateTime _selectedDay;

  @override
  void initState() {
    super.initState();
    _selectedDay = widget.initialDate ?? DateTime.now();
  }

  @override
  Widget build(BuildContext context) {
    final sessionDate = DateFormat('yyyy-MM-dd').format(_selectedDay);
    final sessionAsync = ref.watch(aggregatedSessionByDateProvider(sessionDate));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Daily Study Plan'),
        elevation: 0,
        centerTitle: true,
        actions: [
          if (DateFormat('yyyy-MM-dd').format(DateTime.now()) == sessionDate)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.green[100],
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    'Today',
                    style: TextStyle(
                      color: Colors.green[700],
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
      body: sessionAsync.when(
        data: (session) => _buildSessionView(session),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => _buildErrorView(error),
      ),
    );
  }

  // ===================== UI Builders =====================

  Widget _buildErrorView(Object error) {
    // Treat 404 as empty schedule, not an error
    final is404 = error is DioException && error.response?.statusCode == 404;
    if (is404) {
      return _buildEmptyScheduleView();
    }

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.red),
          const SizedBox(height: 16),
          const Text('Error loading schedule'),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              error.toString(),
              style: const TextStyle(fontSize: 12, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              // Invalidate the provider to retry
              final date = DateFormat('yyyy-MM-dd').format(_selectedDay);
              ref.invalidate(aggregatedSessionByDateProvider(date));
            },
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyScheduleView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.calendar_today, size: 64, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            'No study sessions scheduled',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Colors.grey[600],
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Create a study plan to get started',
            style: TextStyle(color: Colors.grey[400], fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildSessionView(StudySession? session) {
    // If session is null or has no time blocks, show empty view
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
                Row(
                  children: [
                    ElevatedButton.icon(
                      onPressed: _goToPreviousDay,
                      icon: const Icon(Icons.arrow_back, size: 18),
                      label: const Text('Previous'),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton.icon(
                      onPressed: _goToToday,
                      icon: const Icon(Icons.today, size: 18),
                      label: const Text('Today'),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton.icon(
                      onPressed: _goToNextDay,
                      icon: const Icon(Icons.arrow_forward, size: 18),
                      label: const Text('Next'),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const Divider(),

          // Session summary section
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'All Active Plans',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    if (session.isAggregated && session.aggregatedPlanIds != null)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.blue[100],
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '${session.aggregatedPlanIds!.length} plans',
                          style: TextStyle(
                            color: Colors.blue[700],
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  'Total tasks: ${session.timeBlocks.length}',
                  style: TextStyle(color: Colors.grey[600], fontSize: 14),
                ),
                const SizedBox(height: 4),
                Text(
                  'Completed: ${session.completedBlocks} / ${session.timeBlocks.length}',
                  style: TextStyle(color: Colors.grey[600], fontSize: 14),
                ),
              ],
            ),
          ),

          // ✅ FEATURE 1.1: Schedule Info Card - Shows mood adjustments and makeup tasks
          ScheduleInfoCard(
            session: session,
            sessionDate: _selectedDay,
            dismissible: true,
            onDismiss: () {
              debugPrint('User dismissed schedule info for $sessionDate');
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

  Widget _buildAggregatedTimeBlockCard(TimeBlock block, String sessionId) {
    final difficulty = block.difficulty;
    final difficultyColor = difficulty > 0.7
        ? Colors.red[300]
        : difficulty > 0.4
            ? Colors.amber[300]
            : Colors.green[300];

    final typeIcon = block.taskType == 'learn'
        ? Icons.school
        : block.taskType == 'revise'
            ? Icons.replay
            : Icons.done_all;

    final typeLabel =
        block.taskType[0].toUpperCase() + block.taskType.substring(1);

    final planColor = _getPlanColor(block.planId);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Opacity(
        opacity: block.completed ? 0.6 : 1.0,
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            border: Border(
              left: BorderSide(
                color: block.completed ? Colors.grey[400]! : planColor,
                width: 4,
              ),
            ),
            color: block.completed ? Colors.grey[300] : null,
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: difficultyColor,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(typeIcon, color: Colors.white, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          block.subject,
                                          style: TextStyle(
                                            fontWeight: FontWeight.bold,
                                            fontSize: 14,
                                            color: block.completed
                                                ? Colors.grey[500]
                                                : Colors.black,
                                            decoration: block.completed
                                                ? TextDecoration.lineThrough
                                                : null,
                                          ),
                                        ),
                                      ),
                                      if (block.completed)
                                        Padding(
                                          padding:
                                              const EdgeInsets.only(left: 8.0),
                                          child: Icon(
                                            Icons.check_circle,
                                            size: 18,
                                            color: Colors.green[600],
                                          ),
                                        ),
                                    ],
                                  ),
                                  Text(
                                    block.topic,
                                    style: TextStyle(
                                      color: block.completed
                                          ? Colors.grey[400]
                                          : Colors.grey[600],
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                if (block.planId != null)
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 4,
                                    ),
                                    decoration: BoxDecoration(
                                      color: planColor.withAlpha(25),
                                      borderRadius: BorderRadius.circular(4),
                                      border:
                                          Border.all(color: planColor, width: 1),
                                    ),
                                    child: Text(
                                      'Plan',
                                      style: TextStyle(
                                        color: planColor,
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                const SizedBox(height: 4),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 4,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Colors.blue[50],
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text(
                                    typeLabel,
                                    style: TextStyle(
                                      color: Colors.blue[700],
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            Icon(Icons.schedule, size: 16,
                                color: block.completed
                                    ? Colors.grey[400]
                                    : Colors.grey[600]),
                            const SizedBox(width: 4),
                            Text(
                              '${block.startTime} - ${block.endTime} (${block.durationMins} min)',
                              style: TextStyle(
                                color: block.completed
                                    ? Colors.grey[400]
                                    : Colors.grey[600],
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Icon(Icons.trending_up, size: 16,
                                color: block.completed
                                    ? Colors.grey[400]
                                    : difficultyColor),
                            const SizedBox(width: 4),
                            Text(
                              'Difficulty: ${(block.difficulty * 100).toStringAsFixed(0)}%',
                              style: TextStyle(
                                color: block.completed
                                    ? Colors.grey[400]
                                    : Colors.grey[600],
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (!block.completed)
                _buildTaskTimerSection(block, sessionId)
              else
                Column(
                  children: [
                    Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 12,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.grey[200],
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.grey[400]!, width: 2),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.check_circle,
                              size: 20,
                              color: Colors.grey[600],
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Completed',
                              style: TextStyle(
                                color: Colors.grey[700],
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'This task is finished and cannot be marked again',
                      style: TextStyle(
                        color: Colors.grey[500],
                        fontSize: 11,
                        fontStyle: FontStyle.italic,
                      ),
                      textAlign: TextAlign.center,
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

  Widget _buildTaskTimerSection(TimeBlock block, String sessionId) {
    return Consumer(
      builder: (context, ref, child) {
        final timerState = ref.watch(taskTimerStateProvider(block.taskId));
        
        // If timer is active, show timer controls
        if (timerState != null) {
          return _buildTimerDisplay(context, ref, block, sessionId, timerState);
        }

        // Otherwise show start button
        return SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: () => _handleStartTask(context, ref, block, sessionId),
            icon: const Icon(Icons.play_arrow),
            label: const Text('Start'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue,
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        );
      },
    );
  }

  Widget _buildTimerDisplay(
    BuildContext context,
    WidgetRef ref,
    TimeBlock block,
    String sessionId,
    TaskTimerState timerState,
  ) {
    return Column(
      children: [
        // Timer display
        Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: timerState.isRunning ? Colors.blue[50] : Colors.amber[50],
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: timerState.isRunning ? Colors.blue : Colors.amber,
              width: 2,
            ),
          ),
          child: Column(
            children: [
              Text(
                timerState.isRunning ? 'In Progress' : 'Paused',
                style: TextStyle(
                  fontSize: 12,
                  color: timerState.isRunning
                      ? Colors.blue[700]
                      : Colors.amber[700],
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                timerState.formattedTime,
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'monospace',
                  color: timerState.isRunning
                      ? Colors.blue
                      : Colors.amber[700],
                ),
              ),
              const SizedBox(height: 8),
              // Progress bar
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: timerState.progressPercent,
                    minHeight: 6,
                    backgroundColor: timerState.isRunning
                        ? Colors.blue[100]
                        : Colors.amber[100],
                    valueColor: AlwaysStoppedAnimation<Color>(
                      timerState.isRunning
                          ? Colors.blue[600]!
                          : Colors.amber[600]!,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                '${(timerState.progressPercent * 100).toStringAsFixed(0)}% complete',
                style: TextStyle(
                  fontSize: 11,
                  color: timerState.isRunning
                      ? Colors.blue[700]
                      : Colors.amber[700],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        // Control buttons
        Row(
          children: [
            if (timerState.isRunning)
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () async {
                    await ref
                        .read(taskTimerProvider.notifier)
                        .pauseTimer();
                  },
                  icon: const Icon(Icons.pause),
                  label: const Text('Pause'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.orange,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              )
            else
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () async {
                    await ref
                        .read(taskTimerProvider.notifier)
                        .resumeTimer();
                  },
                  icon: const Icon(Icons.play_arrow),
                  label: const Text('Resume'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
            const SizedBox(width: 8),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () async {
                  ref.read(taskTimerProvider.notifier).resetTimer(block.taskId);
                },
                icon: const Icon(Icons.close),
                label: const Text('Stop'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () =>
                    _handleMarkTaskCompleted(context, ref, block, sessionId),
                icon: const Icon(Icons.check_circle),
                label: const Text('Mark Done'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Future<void> _handleStartTask(
    BuildContext context,
    WidgetRef ref,
    TimeBlock block,
    String sessionId,
  ) async {
    final manager = ref.read(taskTimerProvider.notifier);

    // Check if another timer is active
    final activeTaskId = manager.getActiveTaskId();
    if (activeTaskId != null && activeTaskId != block.taskId) {
      // Show confirmation dialog
      final shouldSwitch = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Timer Already Running'),
          content: const Text('Stop the current task and start this one?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Switch Task'),
            ),
          ],
        ),
      );

      if (shouldSwitch != true) return;
    }

    // Start the timer
    await manager.startTimer(block.taskId, block.durationMins);
  }

  Future<void> _handleMarkTaskCompleted(
    BuildContext context,
    WidgetRef ref,
    TimeBlock block,
    String sessionId,
  ) async {
    final timerState = ref.read(taskTimerStateProvider(block.taskId));

    // Check if timer is still running
    if (timerState != null && timerState.isRunning) {
      final confirm = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Timer Still Running'),
          content: const Text(
            'The timer is still active. Mark this task as done anyway?',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Mark as Done'),
            ),
          ],
        ),
      );

      if (confirm != true) return;
    }

    // Mark task as completed
    ref.read(taskTimerProvider.notifier).markTaskCompleted(block.taskId);

    try {
      final response = await ref.read(studyPlannerServiceProvider).completeSession(
        sessionId: sessionId,
        completedTaskIds: [block.taskId],
        userMoodEnd: 'neutral',
        interrupted: false,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${block.subject} - ${block.topic} completed!'),
            backgroundColor: Colors.green,
          ),
        );

        // === FIX #4: Handle suggested_actions from response ===
        // Check if response contains adaptive actions and display them
        if (response != null && response['suggested_actions'] is List) {
          final suggestedActions = List<String>.from(response['suggested_actions']);
          if (suggestedActions.isNotEmpty) {
            // Show first suggested action as a non-blocking notification
            if (mounted) {
              Future.delayed(const Duration(milliseconds: 500), () {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(suggestedActions.first),
                      backgroundColor: Colors.orange,
                      duration: const Duration(seconds: 4),
                      action: SnackBarAction(
                        label: 'Dismiss',
                        onPressed: () {},
                      ),
                    ),
                  );
                }
              });
            }
          }
        }

        // Refresh the session
        final sessionDate = DateFormat('yyyy-MM-dd').format(_selectedDay);
        ref.invalidate(aggregatedSessionByDateProvider(sessionDate));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error marking task complete: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  // ===================== Navigation Helpers =====================

  void _goToPreviousDay() {
    setState(() {
      _selectedDay = _selectedDay.subtract(const Duration(days: 1));
    });
    // Invalidate provider for new date
    final newDate = DateFormat('yyyy-MM-dd').format(_selectedDay);
    ref.invalidate(aggregatedSessionByDateProvider(newDate));
  }

  void _goToToday() {
    setState(() {
      _selectedDay = DateTime.now();
    });
    final newDate = DateFormat('yyyy-MM-dd').format(_selectedDay);
    ref.invalidate(aggregatedSessionByDateProvider(newDate));
  }

  void _goToNextDay() {
    setState(() {
      _selectedDay = _selectedDay.add(const Duration(days: 1));
    });
    final newDate = DateFormat('yyyy-MM-dd').format(_selectedDay);
    ref.invalidate(aggregatedSessionByDateProvider(newDate));
  }

  Color _getPlanColor(String? planId) {
    if (planId == null) return Colors.grey;
    final hash = planId.hashCode;
    final colors = [
      Colors.blue,
      Colors.green,
      Colors.purple,
      Colors.orange,
      Colors.pink,
      Colors.teal,
      Colors.indigo,
      Colors.red,
    ];
    return colors[hash.abs() % colors.length];
  }
}
