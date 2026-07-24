import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/task_timer_provider.dart';

/// Timer display and control widget for a task
class TaskTimerWidget extends ConsumerWidget {
  final String taskId;
  final int durationMins;
  final VoidCallback onTimerFinished;
  final VoidCallback? onCompleted;

  const TaskTimerWidget({
    super.key,
    required this.taskId,
    required this.durationMins,
    required this.onTimerFinished,
    this.onCompleted,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final timerState = ref.watch(taskTimerStateProvider(taskId));

    // Show button state based on timer
    if (timerState == null) {
      // Timer hasn't been started yet
      return _buildStartButton(context, ref);
    }

    if (timerState.isCompleted) {
      // Timer finished or task completed
      return _buildCompletedButton(context, ref);
    }

    if (timerState.isRunning) {
      // Timer is actively counting
      return _buildActiveTimerDisplay(context, ref, timerState);
    }

    // Timer is paused
    return _buildPausedTimerDisplay(context, ref, timerState);
  }

  Widget _buildStartButton(BuildContext context, WidgetRef ref) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: () async {
          final manager = ref.read(taskTimerProvider.notifier);
          
          // Check if another timer is active
          final activeTaskId = manager.getActiveTaskId();
          if (activeTaskId != null && activeTaskId != taskId) {
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
          await manager.startTimer(taskId, durationMins);
        },
        icon: const Icon(Icons.play_arrow),
        label: const Text('Start'),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.blue,
          padding: const EdgeInsets.symmetric(vertical: 12),
        ),
      ),
    );
  }

  Widget _buildActiveTimerDisplay(
    BuildContext context,
    WidgetRef ref,
    TaskTimerState timerState,
  ) {
    return Column(
      children: [
        // Timer display
        Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: Colors.blue[50],
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.blue, width: 2),
          ),
          child: Column(
            children: [
              Text(
                'In Progress',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.blue[700],
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                timerState.formattedTime,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'monospace',
                  color: Colors.blue,
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
                    backgroundColor: Colors.blue[100],
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.blue[600]!),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                '${(timerState.progressPercent * 100).toStringAsFixed(0)}% complete',
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.blue[700],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        // Control buttons
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () async {
                  await ref.read(taskTimerProvider.notifier).pauseTimer();
                },
                icon: const Icon(Icons.pause),
                label: const Text('Pause'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () async {
                  ref.read(taskTimerProvider.notifier).resetTimer(taskId);
                },
                icon: const Icon(Icons.close),
                label: const Text('Stop'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildPausedTimerDisplay(
    BuildContext context,
    WidgetRef ref,
    TaskTimerState timerState,
  ) {
    return Column(
      children: [
        // Paused timer display
        Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: Colors.amber[50],
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.amber, width: 2),
          ),
          child: Column(
            children: [
              Text(
                'Paused',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.amber[700],
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
                  color: Colors.amber[700],
                ),
              ),
              const SizedBox(height: 8),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: timerState.progressPercent,
                    minHeight: 6,
                    backgroundColor: Colors.amber[100],
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.amber[600]!),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        // Resume/Stop buttons
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () async {
                  await ref.read(taskTimerProvider.notifier).resumeTimer();
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
                  ref.read(taskTimerProvider.notifier).resetTimer(taskId);
                },
                icon: const Icon(Icons.close),
                label: const Text('Stop'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildCompletedButton(BuildContext context, WidgetRef ref) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: null, // Disabled
        icon: const Icon(Icons.check_circle),
        label: const Text('Completed'),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.green,
          disabledBackgroundColor: Colors.green[300],
          padding: const EdgeInsets.symmetric(vertical: 12),
        ),
      ),
    );
  }
}

/// Compact timer display for showing in task card header
class CompactTimerDisplay extends ConsumerWidget {
  final String taskId;

  const CompactTimerDisplay({
    super.key,
    required this.taskId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final timerState = ref.watch(taskTimerStateProvider(taskId));

    if (timerState == null || !timerState.isRunning) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.blue[100],
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: Colors.blue, width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.schedule, size: 12, color: Colors.blue),
          const SizedBox(width: 4),
          Text(
            '${timerState.formattedTime} left',
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: Colors.blue,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }
}
