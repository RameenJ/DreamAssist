import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/mood_log_model.dart';
import '../../data/services/mood_api_service.dart';
import '../../core/providers/app_providers.dart';
import 'study_planner_provider.dart';

part 'mood_provider.g.dart';

/// Mood logging state
class MoodState {
  final bool isLoading;
  final String? error;
  final TodayMoodResponse? todayMood;
  final bool showModal;

  const MoodState({
    this.isLoading = false,
    this.error,
    this.todayMood,
    this.showModal = false,
  });

  MoodState copyWith({
    bool? isLoading,
    String? error,
    TodayMoodResponse? todayMood,
    bool? showModal,
  }) {
    return MoodState(
      isLoading: isLoading ?? this.isLoading,
      error: error,
      todayMood: todayMood ?? this.todayMood,
      showModal: showModal ?? this.showModal,
    );
  }
}

/// Mood logging state notifier
@riverpod
class Mood extends _$Mood {
  @override
  MoodState build() {
    // Keep provider alive to prevent disposal during navigation
    ref.keepAlive();
    return const MoodState();
  }

  MoodApiService get _moodService => ref.watch(moodApiServiceProvider);

  /// Check if user has logged mood today
  /// Now that multiple logs per day are allowed, this always returns showModal: true
  /// Users can update their mood anytime during the day
  Future<void> checkTodayMood() async {
    print('🎭 [MoodProvider] Checking today mood...');
    if (!ref.mounted) return;
    state = state.copyWith(isLoading: true, error: null);
    
    final result = await _moodService.checkTodayMood();
    
    if (!ref.mounted) {
      print('🎭 [MoodProvider] Provider disposed after API call');
      return;
    }
    
    result.when(
      success: (response) {
        print('🎭 [MoodProvider] Mood check response: logged=${response.logged}, mood=${response.mood}');
        // Always show modal to allow users to log or update their mood anytime
        // since multiple logs per day are now supported
        state = state.copyWith(
          todayMood: response,
          isLoading: false,
          showModal: true, // Always show to allow re-logging
        );
        print('🎭 [MoodProvider] showModal = true (allowing unlimited daily logs)');
      },
      failure: (message) {
        print('🎭 [MoodProvider] Mood check failed: $message');
        state = state.copyWith(
          isLoading: false,
          error: message,
          showModal: true, // Still show modal even on error to allow retry
        );
      },
    );
  }

  /// Log user's mood
  Future<bool> logMood(String mood) async {
    if (!ref.mounted) return false;
    state = state.copyWith(isLoading: true, error: null);
    
    final result = await _moodService.logMood(mood);
    
    if (!ref.mounted) return false;
    
    return result.when(
      success: (response) {
        if (response.success) {
          state = state.copyWith(
            isLoading: false,
            todayMood: TodayMoodResponse(
              logged: true,
              mood: response.mood,
              date: response.date,
            ),
            showModal: false,
          );
          
          // 🎯 NEW: Refresh aggregated session for today after mood adjustment
          try {
            // Invalidate the aggregated session provider to force refresh
            final todayDate = DateTime.now();
            final formattedDate = '${todayDate.year}-${todayDate.month.toString().padLeft(2, '0')}-${todayDate.day.toString().padLeft(2, '0')}';
            ref.invalidate(aggregatedSessionByDateProvider(formattedDate));
            print('✅ [MoodProvider] Invalidated session for date: $formattedDate');
          } catch (e) {
            print('⚠️ [MoodProvider] Error refreshing session after mood log: $e');
            // Don't fail the mood logging if session refresh fails
          }
          
          return true;
        } else {
          state = state.copyWith(
            isLoading: false,
            error: response.message,
          );
          return false;
        }
      },
      failure: (message) {
        state = state.copyWith(
          isLoading: false,
          error: message,
        );
        return false;
      },
    );
  }

  /// Hide modal (when user skips)
  void hideModal() {
    state = state.copyWith(showModal: false);
  }

  /// Show modal manually
  void showModal() {
    state = state.copyWith(showModal: true);
  }
}

/// Provider for tracking dismissed mood adjustment banners per date
/// Simple in-memory tracking that persists during the session
final moodAdjustmentBannerDismissedProvider = Provider<Set<String>>((ref) {
  return {};
});

/// Mood history state
class MoodHistoryState {
  final bool isLoading;
  final String? error;
  final MoodHistoryResponse? history;
  final int selectedDays;

  const MoodHistoryState({
    this.isLoading = false,
    this.error,
    this.history,
    this.selectedDays = 7,
  });

  MoodHistoryState copyWith({
    bool? isLoading,
    String? error,
    MoodHistoryResponse? history,
    int? selectedDays,
  }) {
    return MoodHistoryState(
      isLoading: isLoading ?? this.isLoading,
      error: error,
      history: history ?? this.history,
      selectedDays: selectedDays ?? this.selectedDays,
    );
  }
}

/// Notifier for managing mood history
@riverpod
class MoodHistory extends _$MoodHistory {
  @override
  MoodHistoryState build() {
    return const MoodHistoryState();
  }

  MoodApiService get _moodService => ref.watch(moodApiServiceProvider);

  /// Fetch mood history for specified number of days
  Future<void> fetchMoodHistory({int days = 7}) async {
    state = state.copyWith(isLoading: true, error: null, selectedDays: days);

    final result = await _moodService.getMoodHistory(days: days);

    result.when(
      success: (response) {
        state = state.copyWith(
          history: response,
          isLoading: false,
        );
      },
      failure: (message) {
        state = state.copyWith(
          isLoading: false,
          error: message,
        );
      },
    );
  }

  /// Switch between 7 and 14 day view
  Future<void> switchDayRange(int days) async {
    await fetchMoodHistory(days: days);
  }
}
