import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../data/models/ai_model.dart';
import '../../data/services/ai_api_service.dart';
import '../../core/providers/app_providers.dart';

part 'ai_study_tools_provider.g.dart';

/// Study tools state for summarization and flashcards
class StudyToolsState {
  final String? summary;
  final List<FlashcardModel> flashcards;
  final bool isLoadingSummary;
  final bool isLoadingFlashcards;
  final String? error;

  const StudyToolsState({
    this.summary,
    this.flashcards = const [],
    this.isLoadingSummary = false,
    this.isLoadingFlashcards = false,
    this.error,
  });

  StudyToolsState copyWith({
    String? summary,
    List<FlashcardModel>? flashcards,
    bool? isLoadingSummary,
    bool? isLoadingFlashcards,
    String? error,
  }) {
    return StudyToolsState(
      summary: summary ?? this.summary,
      flashcards: flashcards ?? this.flashcards,
      isLoadingSummary: isLoadingSummary ?? this.isLoadingSummary,
      isLoadingFlashcards: isLoadingFlashcards ?? this.isLoadingFlashcards,
      error: error,
    );
  }

  bool get isLoading =>
      isLoadingSummary || isLoadingFlashcards;
}

/// Study tools state notifier
@riverpod
class StudyTools extends _$StudyTools {
  @override
  StudyToolsState build() {
    return const StudyToolsState();
  }

  AiApiService get _aiService => ref.watch(aiApiServiceProvider);

  /// Summarize text
  Future<void> summarizeText(String text) async {
    state = state.copyWith(
      isLoadingSummary: true,
      error: null,
      summary: null,
    );

    final result = await _aiService.summarizeText(text);
    
    result.when(
      success: (response) {
        state = state.copyWith(
          summary: response.summary,
          isLoadingSummary: false,
        );
      },
      failure: (message) {
        state = state.copyWith(
          isLoadingSummary: false,
          error: message,
        );
      },
    );
  }

  /// Generate flashcards from text
  Future<void> generateFlashcards(String text) async {
    state = state.copyWith(
      isLoadingFlashcards: true,
      error: null,
      flashcards: [],
    );

    final result = await _aiService.generateFlashcards(text);
    
    result.when(
      success: (response) {
        state = state.copyWith(
          flashcards: response.flashcards,
          isLoadingFlashcards: false,
        );
      },
      failure: (message) {
        state = state.copyWith(
          isLoadingFlashcards: false,
          error: message,
        );
      },
    );
  }

  /// Clear summary
  void clearSummary() {
    state = state.copyWith(summary: null);
  }

  /// Clear flashcards
  void clearFlashcards() {
    state = state.copyWith(flashcards: []);
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(error: null);
  }

  /// Clear all data
  void clearAll() {
    state = const StudyToolsState();
  }
}
