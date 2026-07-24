import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../data/models/ai_model.dart';
import '../../data/services/ai_api_service.dart';
import '../../core/providers/app_providers.dart';

part 'ai_quiz_provider.g.dart';

/// Quiz attempt data
class QuizAttempt {
  final String quizId;
  final String bookId;
  final String topicName; // Added to track topic for evaluation
  final List<QuizQuestionModel> questions;
  final List<String?> userAnswers; // Changed to String for free-text answers
  final int currentQuestionIndex;
  final bool isCompleted;
  final QuizEvaluationResponse? evaluation;

  const QuizAttempt({
    required this.quizId,
    required this.bookId,
    required this.topicName,
    required this.questions,
    this.userAnswers = const [],
    this.currentQuestionIndex = 0,
    this.isCompleted = false,
    this.evaluation,
  });

  QuizAttempt copyWith({
    String? quizId,
    String? bookId,
    String? topicName,
    List<QuizQuestionModel>? questions,
    List<String?>? userAnswers,  // Changed to String
    int? currentQuestionIndex,
    bool? isCompleted,
    QuizEvaluationResponse? evaluation,
  }) {
    return QuizAttempt(
      quizId: quizId ?? this.quizId,
      bookId: bookId ?? this.bookId,
      topicName: topicName ?? this.topicName,
      questions: questions ?? this.questions,
      userAnswers: userAnswers ?? this.userAnswers,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      isCompleted: isCompleted ?? this.isCompleted,
      evaluation: evaluation ?? this.evaluation,
    );
  }
}

/// AI Quiz state
class AiQuizState {
  final QuizAttempt? currentQuiz;
  final bool isLoading;
  final String? error;

  const AiQuizState({
    this.currentQuiz,
    this.isLoading = false,
    this.error,
  });

  AiQuizState copyWith({
    QuizAttempt? currentQuiz,
    bool? isLoading,
    String? error,
  }) {
    return AiQuizState(
      currentQuiz: currentQuiz ?? this.currentQuiz,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// AI Quiz state notifier
@riverpod
class AiQuiz extends _$AiQuiz {
  @override
  AiQuizState build() {
    return const AiQuizState();
  }

  AiApiService get _aiService => ref.watch(aiApiServiceProvider);

  /// Generate a new quiz for a book or specific topic
  Future<bool> generateQuiz({
    String? bookId,
    String? topicId,
    String? topicName, // Added to track topic for evaluation
    required int numQuestions,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _aiService.generateQuiz(
      bookId: bookId,
      topicId: topicId,
      numQuestions: numQuestions,
    );
    
    return result.when(
      success: (quiz) {
        // Initialize user answers list with null values for free-text input
        final userAnswers = List<String?>.filled(quiz.questions.length, null);
        
        final quizAttempt = QuizAttempt(
          quizId: quiz.quizId,
          bookId: quiz.bookId,
          topicName: topicName ?? 'Whole Book', // Default if not specified
          questions: quiz.questions,
          userAnswers: userAnswers,
        );

        state = state.copyWith(
          currentQuiz: quizAttempt,
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

  /// Answer a question with free-text input
  void answerQuestion(int questionIndex, String answer) {
    if (state.currentQuiz == null) return;

    final updatedAnswers = List<String?>.from(state.currentQuiz!.userAnswers);
    updatedAnswers[questionIndex] = answer.trim();

    final updatedQuiz = state.currentQuiz!.copyWith(
      userAnswers: updatedAnswers,
    );

    state = state.copyWith(currentQuiz: updatedQuiz);
  }

  /// Go to next question
  void nextQuestion() {
    if (state.currentQuiz == null) return;

    final currentIndex = state.currentQuiz!.currentQuestionIndex;
    final totalQuestions = state.currentQuiz!.questions.length;

    if (currentIndex < totalQuestions - 1) {
      final updatedQuiz = state.currentQuiz!.copyWith(
        currentQuestionIndex: currentIndex + 1,
      );
      state = state.copyWith(currentQuiz: updatedQuiz);
    }
  }

  /// Go to previous question
  void previousQuestion() {
    if (state.currentQuiz == null) return;

    final currentIndex = state.currentQuiz!.currentQuestionIndex;

    if (currentIndex > 0) {
      final updatedQuiz = state.currentQuiz!.copyWith(
        currentQuestionIndex: currentIndex - 1,
      );
      state = state.copyWith(currentQuiz: updatedQuiz);
    }
  }

  /// Jump to specific question
  void goToQuestion(int index) {
    if (state.currentQuiz == null) return;

    if (index >= 0 && index < state.currentQuiz!.questions.length) {
      final updatedQuiz = state.currentQuiz!.copyWith(
        currentQuestionIndex: index,
      );
      state = state.copyWith(currentQuiz: updatedQuiz);
    }
  }

  /// Submit quiz for evaluation
  Future<bool> submitQuiz() async {
    print('🎯 [QUIZ SUBMIT] Starting quiz submission...');
    if (state.currentQuiz == null) {
      print('❌ [QUIZ SUBMIT] No active quiz found');
      state = state.copyWith(error: 'No active quiz to submit');
      return false;
    }

    print('🎯 [QUIZ SUBMIT] Quiz ID: ${state.currentQuiz!.quizId}');
    print('🎯 [QUIZ SUBMIT] Book ID: ${state.currentQuiz!.bookId}');
    print('🎯 [QUIZ SUBMIT] Topic: ${state.currentQuiz!.topicName}');
    print('🎯 [QUIZ SUBMIT] User answers: ${state.currentQuiz!.userAnswers}');

    // Allow submission even with unanswered questions (will be marked as incorrect)
    final unansweredCount = state.currentQuiz!.userAnswers.where((a) => a == null || a.trim().isEmpty).length;
    print('⚠️ [QUIZ SUBMIT] Unanswered questions: $unansweredCount');

    print('✅ [QUIZ SUBMIT] Sending quiz to backend for evaluation...');
    state = state.copyWith(isLoading: true, error: null);

    // Convert user answers to UserAnswer objects (include all questions, even unanswered)
    final List<UserAnswer> attemptedAnswers = [];
    for (int i = 0; i < state.currentQuiz!.questions.length; i++) {
      final answer = state.currentQuiz!.userAnswers[i];
      attemptedAnswers.add(UserAnswer(
        questionText: state.currentQuiz!.questions[i].questionText,
        userAnswer: answer?.trim() ?? '', // Empty string for unanswered questions
      ));
    }

    print('🎯 [QUIZ SUBMIT] Created ${attemptedAnswers.length} answer objects (including unanswered)');
    
    final result = await _aiService.evaluateQuiz(
      quizId: state.currentQuiz!.quizId,
      attemptedAnswers: attemptedAnswers,
      bookId: state.currentQuiz!.bookId,
      topicName: state.currentQuiz!.topicName,
    );
    
    return result.when(
      success: (evaluation) {
        print('✅ [QUIZ SUBMIT] Evaluation successful!');
        print('🎯 [QUIZ SUBMIT] Total Score: ${evaluation.totalScore}');
        print('🎯 [QUIZ SUBMIT] Grade: ${evaluation.totalGrade}');
        print('🎯 [QUIZ SUBMIT] Results count: ${evaluation.results.length}');
        
        final updatedQuiz = state.currentQuiz!.copyWith(
          isCompleted: true,
          evaluation: evaluation,
        );

        state = state.copyWith(
          currentQuiz: updatedQuiz,
          isLoading: false,
        );
        print('✅ [QUIZ SUBMIT] Quiz state updated with evaluation');
        return true;
      },
      failure: (message) {
        print('❌ [QUIZ SUBMIT] Evaluation failed: $message');
        state = state.copyWith(
          isLoading: false,
          error: message,
        );
        return false;
      },
    );
  }

  /// Check if current question is answered
  bool isCurrentQuestionAnswered() {
    if (state.currentQuiz == null) return false;
    
    final currentIndex = state.currentQuiz!.currentQuestionIndex;
    return state.currentQuiz!.userAnswers[currentIndex] != null;
  }

  /// Get percentage of questions answered
  double getProgress() {
    if (state.currentQuiz == null) return 0.0;

    final answered = state.currentQuiz!.userAnswers
        .where((answer) => answer != null)
        .length;
    final total = state.currentQuiz!.questions.length;

    return answered / total;
  }

  /// Clear current quiz
  void clearQuiz() {
    state = state.copyWith(currentQuiz: null, error: null);
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(error: null);
  }

  /// Reset quiz (start over with same questions)
  void resetQuiz() {
    if (state.currentQuiz == null) return;

    final userAnswers = List<String?>.filled(
      state.currentQuiz!.questions.length,
      null,
    );

    final resetQuiz = state.currentQuiz!.copyWith(
      userAnswers: userAnswers,
      currentQuestionIndex: 0,
      isCompleted: false,
      evaluation: null,
    );

    state = state.copyWith(currentQuiz: resetQuiz);
  }
}
