import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/utils/result.dart';
import '../../data/models/ai_model.dart';
import '../../core/providers/app_providers.dart';
import '../../data/services/ai_api_service.dart';
import 'package:logger/logger.dart';

// State class for history
class HistoryState {
  final bool isLoading;
  final String? error;
  final List<QuizHistoryItem> quizHistory;
  final List<FlashcardSetPublic> flashcardSets;

  const HistoryState({
    this.isLoading = false,
    this.error,
    this.quizHistory = const [],
    this.flashcardSets = const [],
  });

  HistoryState copyWith({
    bool? isLoading,
    String? error,
    List<QuizHistoryItem>? quizHistory,
    List<FlashcardSetPublic>? flashcardSets,
  }) {
    return HistoryState(
      isLoading: isLoading ?? this.isLoading,
      error: error,
      quizHistory: quizHistory ?? this.quizHistory,
      flashcardSets: flashcardSets ?? this.flashcardSets,
    );
  }
}

// Quiz History Notifier
class QuizHistoryNotifier extends Notifier<HistoryState> {
  late AiApiService aiApiService;
  late Logger logger;

  @override
  HistoryState build() {
    aiApiService = ref.watch(aiApiServiceProvider);
    logger = ref.watch(loggerProvider);
    return const HistoryState();
  }

  Future<void> loadQuizHistory() async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await aiApiService.getQuizHistory();

    if (result is Success<List<QuizHistoryItem>>) {
      state = state.copyWith(
        quizHistory: result.data,
        isLoading: false,
      );
      logger.i('Quiz history loaded: ${result.data.length} items');
    } else if (result is Failure) {
      final failure = result as Failure;
      state = state.copyWith(
        isLoading: false,
        error: failure.message,
      );
      logger.e('Failed to load quiz history: ${failure.message}');
    }
  }

  Future<void> loadQuizHistoryByBook(String bookId) async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await aiApiService.getQuizHistoryByBook(bookId);

    if (result is Success<List<QuizHistoryItem>>) {
      state = state.copyWith(
        quizHistory: result.data,
        isLoading: false,
      );
      logger.i('Book quiz history loaded: ${result.data.length} items');
    } else if (result is Failure) {
      final failure = result as Failure;
      state = state.copyWith(
        isLoading: false,
        error: failure.message,
      );
      logger.e('Failed to load book quiz history: ${failure.message}');
    }
  }
}

// Flashcard History Notifier
class FlashcardHistoryNotifier extends Notifier<HistoryState> {
  late AiApiService aiApiService;
  late Logger logger;

  @override
  HistoryState build() {
    aiApiService = ref.watch(aiApiServiceProvider);
    logger = ref.watch(loggerProvider);
    return const HistoryState();
  }

  Future<void> loadFlashcardSets(String bookId) async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await aiApiService.getFlashcardSets(bookId);

    if (result is Success<List<FlashcardSetPublic>>) {
      state = state.copyWith(
        flashcardSets: result.data,
        isLoading: false,
      );
      logger.i('Flashcard sets loaded: ${result.data.length} items');
    } else if (result is Failure) {
      final failure = result as Failure;
      state = state.copyWith(
        isLoading: false,
        error: failure.message,
      );
      logger.e('Failed to load flashcard sets: ${failure.message}');
    }
  }
}

// Providers
final quizHistoryProvider = NotifierProvider<QuizHistoryNotifier, HistoryState>(
  QuizHistoryNotifier.new,
);

final flashcardHistoryProvider = NotifierProvider<FlashcardHistoryNotifier, HistoryState>(
  FlashcardHistoryNotifier.new,
);

// Single flashcard set provider
final selectedFlashcardSetProvider =
    FutureProvider.family<FlashcardSetPublic?, String>((ref, setId) async {
  final aiApiService = ref.watch(aiApiServiceProvider);
  final result = await aiApiService.getFlashcards(setId);

  if (result is Success<FlashcardSetPublic>) {
    return result.data;
  } else {
    return null;
  }
});
