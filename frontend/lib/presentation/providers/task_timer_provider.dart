import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:async';

/// Timer state for a single task
class TaskTimerState {
  final String taskId;
  final int totalDurationMins;
  final int remainingSeconds;
  final bool isRunning;
  final bool isCompleted;

  TaskTimerState({
    required this.taskId,
    required this.totalDurationMins,
    required this.remainingSeconds,
    required this.isRunning,
    required this.isCompleted,
  });

  TaskTimerState copyWith({
    String? taskId,
    int? totalDurationMins,
    int? remainingSeconds,
    bool? isRunning,
    bool? isCompleted,
  }) {
    return TaskTimerState(
      taskId: taskId ?? this.taskId,
      totalDurationMins: totalDurationMins ?? this.totalDurationMins,
      remainingSeconds: remainingSeconds ?? this.remainingSeconds,
      isRunning: isRunning ?? this.isRunning,
      isCompleted: isCompleted ?? this.isCompleted,
    );
  }

  /// Get remaining time as mm:ss format
  String get formattedTime {
    final minutes = remainingSeconds ~/ 60;
    final seconds = remainingSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  /// Get progress percentage (0.0 to 1.0)
  double get progressPercent {
    final totalSeconds = totalDurationMins * 60;
    return (totalSeconds - remainingSeconds) / totalSeconds;
  }
}

/// Global timer manager - handles one active timer at a time
/// Using Riverpod 3.x Notifier pattern
class TaskTimerManager extends Notifier<Map<String, TaskTimerState>> {
  Timer? _activeTimer;
  String? _currentActiveTaskId;

  @override
  Map<String, TaskTimerState> build() {
    return {};
  }

  /// Start a timer for a task
  /// Returns true if started, false if another timer is active
  Future<bool> startTimer(String taskId, int durationMins) async {
    // If a different task is running, cancel it first
    if (_currentActiveTaskId != null && _currentActiveTaskId != taskId) {
      await pauseTimer();
    }

    // Initialize the task state if not already present
    if (!state.containsKey(taskId)) {
      state = {
        ...state,
        taskId: TaskTimerState(
          taskId: taskId,
          totalDurationMins: durationMins,
          remainingSeconds: durationMins * 60,
          isRunning: false,
          isCompleted: false,
        ),
      };
    }

    // Cancel any existing timer
    _activeTimer?.cancel();
    _currentActiveTaskId = taskId;

    // Start the countdown
    _activeTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      final currentState = state[taskId];
      if (currentState == null) {
        timer.cancel();
        return;
      }

      final newRemaining = currentState.remainingSeconds - 1;

      if (newRemaining <= 0) {
        // Timer finished
        timer.cancel();
        state = {
          ...state,
          taskId: currentState.copyWith(
            remainingSeconds: 0,
            isRunning: false,
            isCompleted: true,
          ),
        };
        _currentActiveTaskId = null;
      } else {
        // Update remaining time
        state = {
          ...state,
          taskId: currentState.copyWith(remainingSeconds: newRemaining),
        };
      }
    });

    // Update state to running
    final taskState = state[taskId]!;
    state = {
      ...state,
      taskId: taskState.copyWith(isRunning: true),
    };

    return true;
  }

  /// Pause the current active timer
  Future<void> pauseTimer() async {
    _activeTimer?.cancel();
    _activeTimer = null;

    if (_currentActiveTaskId != null) {
      final taskState = state[_currentActiveTaskId];
      if (taskState != null) {
        state = {
          ...state,
          _currentActiveTaskId!: taskState.copyWith(isRunning: false),
        };
      }
    }
  }

  /// Resume the current paused timer
  Future<bool> resumeTimer() async {
    if (_currentActiveTaskId == null) return false;

    final taskState = state[_currentActiveTaskId];
    if (taskState == null || taskState.isCompleted) return false;

    // Start the timer again
    _activeTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      final current = state[_currentActiveTaskId];
      if (current == null) {
        timer.cancel();
        return;
      }

      final newRemaining = current.remainingSeconds - 1;

      if (newRemaining <= 0) {
        timer.cancel();
        state = {
          ...state,
          _currentActiveTaskId!: current.copyWith(
            remainingSeconds: 0,
            isRunning: false,
            isCompleted: true,
          ),
        };
        _currentActiveTaskId = null;
      } else {
        state = {
          ...state,
          _currentActiveTaskId!: current.copyWith(remainingSeconds: newRemaining),
        };
      }
    });

    state = {
      ...state,
      _currentActiveTaskId!: taskState.copyWith(isRunning: true),
    };

    return true;
  }

  /// Stop and reset a timer for a task
  void resetTimer(String taskId) {
    if (_currentActiveTaskId == taskId) {
      _activeTimer?.cancel();
      _activeTimer = null;
      _currentActiveTaskId = null;
    }

    // Remove from state or reset to initial state
    state = Map.from(state)..remove(taskId);
  }

  /// Mark a task as completed (without finishing timer)
  void markTaskCompleted(String taskId) {
    final taskState = state[taskId];
    if (taskState != null) {
      if (_currentActiveTaskId == taskId) {
        _activeTimer?.cancel();
        _currentActiveTaskId = null;
      }

      state = {
        ...state,
        taskId: taskState.copyWith(isRunning: false, isCompleted: true),
      };
    }
  }

  /// Get the current active task ID (if any timer is running)
  String? getActiveTaskId() => _currentActiveTaskId;

  /// Get state for a specific task
  TaskTimerState? getTaskState(String taskId) => state[taskId];
}


/// Provider for task timer management
final taskTimerProvider = NotifierProvider<TaskTimerManager, Map<String, TaskTimerState>>(
  TaskTimerManager.new,
);

/// Provider to watch a specific task's timer state
final taskTimerStateProvider = Provider.family<TaskTimerState?, String>(
  (ref, taskId) {
    final timerMap = ref.watch(taskTimerProvider);
    return timerMap[taskId];
  },
);

/// Provider for the currently active task ID
final activeTaskTimerProvider = Provider<String?>((ref) {
  ref.watch(taskTimerProvider); // watch for changes
  // We need to access the notifier directly to get the active task
  final notifier = ref.read(taskTimerProvider.notifier);
  return notifier.getActiveTaskId();
});
