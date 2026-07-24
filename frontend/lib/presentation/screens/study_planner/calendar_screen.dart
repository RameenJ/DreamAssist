import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:table_calendar/table_calendar.dart';
import '../../../core/api/api_models.dart';
import '../../providers/study_planner_provider.dart';

class StudyPlannerCalendarScreen extends ConsumerStatefulWidget {
  // Kept for compatibility, but IGNORED - we always use the first active plan.
  final String planId;

  const StudyPlannerCalendarScreen({
    super.key,
    required this.planId,
  });

  @override
  ConsumerState<StudyPlannerCalendarScreen> createState() =>
      _StudyPlannerCalendarScreenState();
}

class _StudyPlannerCalendarScreenState
    extends ConsumerState<StudyPlannerCalendarScreen> {
  late DateTime _focusedDay;
  late DateTime _selectedDay;
  late DateTime _firstDay;
  late DateTime _lastDay;

  @override
  void initState() {
    super.initState();
    _selectedDay = DateTime.now();
    _focusedDay = DateTime.now();
    _firstDay = DateTime.now().subtract(const Duration(days: 30));
    _lastDay = DateTime.now().add(const Duration(days: 60));
  }

  @override
  Widget build(BuildContext context) {
    // 1. First, get the ID of the active plan (first one returned by backend)
    final activePlanIdAsync = ref.watch(activePlanIdProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Study Plan Calendar'),
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          tooltip: 'Back',
          onPressed: () {
            if (context.canPop()) {
              context.pop();
            } else {
              context.go('/home');
            }
          },
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.home),
            tooltip: 'Home',
            onPressed: () => context.go('/home'),
          ),
        ],
      ),
      body: activePlanIdAsync.when(
        data: (activePlanId) {
          // No active plan exists – show appropriate UI
          if (activePlanId == null) {
            return _buildNoActivePlanUI();
          }

          // 2. Now fetch the full plan details using the valid activePlanId
          final planAsync = ref.watch(planDetailsProvider(activePlanId));
          return planAsync.when(
            data: (plan) {
              if (plan == null) {
                return _buildPlanNotFoundUI();
              }

              // Update calendar range based on plan dates
              final planStartDate = DateTime.parse(plan.startDate);
              final planEndDate = DateTime.parse(plan.endDate);
              _firstDay = planStartDate;
              _lastDay = planEndDate;

              return SingleChildScrollView(
                child: Column(
                  children: [
                    _buildCalendarWidget(),
                    const Divider(),
                    // Pass the valid plan ID to the session details widget
                    _buildSelectedDayDetails(activePlanId),
                    const SizedBox(height: 24),
                  ],
                ),
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, stack) => _buildErrorUI(error),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => _buildErrorUI(error),
      ),
    );
  }

  // ===================== UI Components =====================

  Widget _buildNoActivePlanUI() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.calendar_today, size: 48, color: Colors.grey),
          const SizedBox(height: 16),
          const Text('No active study plan found'),
          const SizedBox(height: 8),
          const Text(
            'Please create a study plan first to see your calendar.',
            style: TextStyle(fontSize: 12, color: Colors.grey),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () {
              // Navigate to plan creation screen using GoRouter
              context.push('/study-planner/create');
            },
            icon: const Icon(Icons.add),
            label: const Text('Create Study Plan'),
          ),
        ],
      ),
    );
  }

  Widget _buildPlanNotFoundUI() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.orange),
          const SizedBox(height: 16),
          const Text('Plan not found'),
          const SizedBox(height: 8),
          const Text(
            'The active plan might have been deleted. Please create a new one.',
            style: TextStyle(fontSize: 12, color: Colors.grey),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () {
              context.push('/study-planner/create');
            },
            icon: const Icon(Icons.add),
            label: const Text('Create New Plan'),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorUI(Object error) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.red),
          const SizedBox(height: 16),
          const Text('Error loading plan'),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              error.toString().contains('404') || error.toString().contains('not found')
                  ? 'Plan not found. It may have been deleted.'
                  : 'Failed to load plan details. Please check your connection.',
              style: const TextStyle(fontSize: 12, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              ref.invalidate(activePlanIdProvider);
            },
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildCalendarWidget() {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: TableCalendar(
        firstDay: _firstDay,
        lastDay: _lastDay,
        focusedDay: _focusedDay,
        selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
        onDaySelected: (selectedDay, focusedDay) {
          setState(() {
            _selectedDay = selectedDay;
            _focusedDay = focusedDay;
          });
        },
        onPageChanged: (focusedDay) {
          setState(() {
            _focusedDay = focusedDay;
          });
        },
        calendarStyle: CalendarStyle(
          defaultTextStyle: TextStyle(color: Colors.grey[700]),
          weekendTextStyle: TextStyle(color: Colors.red[400]),
          selectedDecoration: BoxDecoration(
            color: Theme.of(context).primaryColor,
            shape: BoxShape.circle,
          ),
          todayDecoration: const BoxDecoration(
            color: Colors.amber,
            shape: BoxShape.circle,
          ),
          markerDecoration: const BoxDecoration(
            color: Colors.green,
            shape: BoxShape.circle,
          ),
        ),
        headerStyle: HeaderStyle(
          formatButtonDecoration: BoxDecoration(
            color: Theme.of(context).primaryColor,
            borderRadius: BorderRadius.circular(4),
          ),
          formatButtonTextStyle: const TextStyle(color: Colors.white),
        ),
      ),
    );
  }

  // ===================== Session Details =====================

  Widget _buildSelectedDayDetails(String activePlanId) {
    final sessionDate = DateFormat('yyyy-MM-dd').format(_selectedDay);
    // Use the valid activePlanId instead of widget.planId
    final sessionAsync = ref.watch(
      sessionByDateProvider((planId: activePlanId, date: sessionDate)),
    );

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.calendar_today, color: Colors.blueAccent),
              const SizedBox(width: 8),
              Text(
                DateFormat('EEEE, MMMM d, yyyy').format(_selectedDay),
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Text(
            'Study Plan for Selected Day',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 12),
          sessionAsync.when(
            data: (session) {
              if (session == null || session.planId == null || session.timeBlocks.isEmpty) {
                return const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Text('No study sessions scheduled for this day'),
                  ),
                );
              }
              return ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: session.timeBlocks.length,
                itemBuilder: (context, index) {
                  final block = session.timeBlocks[index];
                  return _buildTimeBlockCard(block, session.id);
                },
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, stack) => Text('Error: $error'),
          ),
        ],
      ),
    );
  }

  Widget _buildTimeBlockCard(TimeBlock block, String sessionId) {
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

    final typeLabel = block.taskType[0].toUpperCase() + block.taskType.substring(1);
    final planColor = _getPlanColor(block.planId);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(4),
          border: Border(
            left: BorderSide(color: planColor, width: 4),
          ),
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
                                  Text(
                                    block.subject,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 14,
                                    ),
                                  ),
                                  Text(
                                    block.topic,
                                    style: TextStyle(
                                      color: Colors.grey[600],
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
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
                            Icon(Icons.schedule, size: 16, color: Colors.grey[600]),
                            const SizedBox(width: 4),
                            Text(
                              '${block.startTime} - ${block.endTime} (${block.durationMins} min)',
                              style: TextStyle(color: Colors.grey[600], fontSize: 12),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Icon(Icons.trending_up, size: 16, color: difficultyColor),
                            const SizedBox(width: 4),
                            Text(
                              'Difficulty: ${(block.difficulty * 100).toStringAsFixed(0)}%',
                              style: TextStyle(color: Colors.grey[600], fontSize: 12),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => _markBlockComplete(block, sessionId),
                  icon: block.completed
                      ? const Icon(Icons.check)
                      : const Icon(Icons.play_arrow),
                  label: block.completed ? const Text('Completed') : const Text('Start'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: block.completed ? Colors.green : Colors.blue,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
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

  Future<void> _markBlockComplete(TimeBlock block, String sessionId) async {
    if (block.completed) return;

    if (sessionId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Cannot complete: session ID missing.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    try {
      await ref.read(studyPlannerServiceProvider).completeSession(
        sessionId: sessionId,
        completedTaskIds: [block.taskId],
        userMoodEnd: 'neutral',
        interrupted: false,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${block.subject.isNotEmpty ? block.subject : block.topic} — ${block.topic} completed!'),
            backgroundColor: Colors.green,
          ),
        );

        // Refresh the session for the selected day
        final sessionDate = DateFormat('yyyy-MM-dd').format(_selectedDay);
        final activePlanId = ref.read(activePlanIdProvider).value;
        if (activePlanId != null) {
          ref.invalidate(sessionByDateProvider((planId: activePlanId, date: sessionDate)));
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error marking complete: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
}