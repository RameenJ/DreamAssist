import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../data/models/diagnostic_quiz_model.dart';
import '../../data/services/diagnostic_api_service.dart';
import '../../core/providers/app_providers.dart';

part 'diagnostic_provider.g.dart';

/// Diagnostic quiz state
class DiagnosticState {
  final DiagnosticQuizResponse? currentQuiz;
  final DiagnosticQuizResult? lastResult;
  final List<SubjectProfile> profiles;
  final bool isLoading;
  final String? error;

  const DiagnosticState({
    this.currentQuiz,
    this.lastResult,
    this.profiles = const [],
    this.isLoading = false,
    this.error,
  });

  DiagnosticState copyWith({
    DiagnosticQuizResponse? currentQuiz,
    DiagnosticQuizResult? lastResult,
    List<SubjectProfile>? profiles,
    bool? isLoading,
    String? error,
  }) {
    return DiagnosticState(
      currentQuiz: currentQuiz ?? this.currentQuiz,
      lastResult: lastResult ?? this.lastResult,
      profiles: profiles ?? this.profiles,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// Diagnostic quiz state notifier
@riverpod
class Diagnostic extends _$Diagnostic {
  @override
  DiagnosticState build() {
    return const DiagnosticState();
  }

  DiagnosticApiService get _diagnosticService =>
      ref.watch(diagnosticApiServiceProvider);

  /// Generate a diagnostic quiz for a subject
  Future<bool> generateQuiz(String subject) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _diagnosticService.generateQuiz(subject);
    return result.when(
      success: (quiz) {
        state = state.copyWith(
          currentQuiz: quiz,
          isLoading: false,
        );
        return true;
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

  /// Submit quiz answers and get evaluation
  Future<DiagnosticQuizResult?> submitQuiz(
    DiagnosticQuizSubmission submission,
  ) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _diagnosticService.submitQuiz(submission);
    return result.when(
      success: (quizResult) {
        state = state.copyWith(
          lastResult: quizResult,
          isLoading: false,
        );
        return quizResult;
      },
      failure: (message) {
        state = state.copyWith(
          isLoading: false,
          error: message,
        );
        return null;
      },
    );
  }

  /// Set manual level for a subject
  Future<bool> setManualLevel(ManualLevelSetting setting) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _diagnosticService.setManualLevel(setting);
    return result.when(
      success: (response) {
        state = state.copyWith(isLoading: false);
        return true;
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

  /// Load user's subject profiles
  Future<void> loadProfiles() async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _diagnosticService.getMyProfiles();
    result.when(
      success: (profiles) {
        state = state.copyWith(
          profiles: profiles,
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

  /// Clear current quiz
  void clearCurrentQuiz() {
    state = state.copyWith(
      currentQuiz: null,
      lastResult: null,
    );
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(error: null);
  }
}
