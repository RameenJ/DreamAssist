import 'package:dio/dio.dart';
import '../../core/network/dio_client.dart';
import '../../core/config/app_config.dart';
import '../../core/utils/result.dart';
import '../models/ai_model.dart';

/// API service for AI-powered features
class AiApiService {
  final DioClient _dioClient;

  AiApiService(this._dioClient);

  /// Chat with AI mentor about a book using RAG
  Future<Result<ChatResponse>> chatWithBook(String bookId, String query) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.aiEndpoint}/chat/$bookId',
        data: ChatRequest(query: query).toJson(),
      );
      return Success(ChatResponse.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to get AI response');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Summarize text
  Future<Result<SummarizationResponse>> summarizeText(String text) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.aiEndpoint}/summarize-text',
        data: SummarizeRequest(textToSummarize: text).toJson(),
      );
      return Success(SummarizationResponse.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to summarize text');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Generate flashcards from text
  Future<Result<FlashcardsResponse>> generateFlashcards(String text) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.aiEndpoint}/generate-flashcards',
        data: FlashcardRequest(textForFlashcards: text).toJson(),
      );
      return Success(FlashcardsResponse.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to generate flashcards');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Generate a quiz for a book or specific topic
  Future<Result<GeneratedQuiz>> generateQuiz({
    String? bookId,
    String? topicId,
    required int numQuestions,
  }) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.aiEndpoint}/quiz/generate',
        data: QuizGenerationRequest(
          bookId: bookId,
          topicId: topicId,
          numQuestions: numQuestions,
        ).toJson(),
      );
      
      // Log the response for debugging
      print('Quiz generation response: ${response.data}');
      
      return Success(GeneratedQuiz.fromJson(response.data));
    } on DioException catch (e) {
      // Extract the actual error message from backend
      final errorMessage = e.response?.data?['detail'] ?? e.message ?? 'Failed to generate quiz';
      print('Quiz generation DioException: $errorMessage');
      return Failure(errorMessage);
    } on TypeError catch (e) {
      // Catch null safety errors during parsing
      print('Quiz generation TypeError: $e');
      return const Failure('Invalid response from server. Please ensure the book has been fully processed.');
    } catch (e) {
      print('Quiz generation unexpected error: $e');
      return Failure('Unexpected error: $e');
    }
  }

  /// Evaluate quiz answers
  Future<Result<QuizEvaluationResponse>> evaluateQuiz({
    required String quizId,
    required List<UserAnswer> attemptedAnswers,
    required String bookId,
    required String topicName,
  }) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.aiEndpoint}/quiz/evaluate',
        data: QuizEvaluationRequest(
          quizId: quizId,
          attemptedAnswers: attemptedAnswers,
          bookId: bookId,
          topicName: topicName,
        ).toJson(),
      );
      return Success(QuizEvaluationResponse.fromJson(response.data));
    } on DioException catch (e) {
      final errorMessage = e.response?.data?['detail'] ?? e.message ?? 'Failed to evaluate quiz';
      return Failure(errorMessage);
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Get flashcard sets for a book
  Future<Result<List<FlashcardSetPublic>>> getFlashcardSets(String bookId) async {
    try {
      final response = await _dioClient.dio.get(
        '${AppConfig.aiEndpoint}/flashcards/sets/$bookId',
      );
      final List<dynamic> data = response.data;
      final flashcardSets = data
          .map((item) => FlashcardSetPublic.fromJson(item as Map<String, dynamic>))
          .toList();
      return Success(flashcardSets);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch flashcard sets');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Get flashcards in a set
  Future<Result<FlashcardSetPublic>> getFlashcards(String setId) async {
    try {
      final response = await _dioClient.dio.get(
        '${AppConfig.aiEndpoint}/flashcards/$setId',
      );
      return Success(FlashcardSetPublic.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch flashcards');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Get all quiz history
  Future<Result<List<QuizHistoryItem>>> getQuizHistory() async {
    try {
      final response = await _dioClient.dio.get(
        '${AppConfig.aiEndpoint}/quiz/history',
      );
      final List<dynamic> data = response.data;
      final history = data
          .map((item) => QuizHistoryItem.fromJson(item as Map<String, dynamic>))
          .toList();
      return Success(history);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch quiz history');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Get quiz history for a specific book
  Future<Result<List<QuizHistoryItem>>> getQuizHistoryByBook(String bookId) async {
    try {
      final response = await _dioClient.dio.get(
        '${AppConfig.aiEndpoint}/quiz/history/$bookId',
      );
      final List<dynamic> data = response.data;
      final history = data
          .map((item) => QuizHistoryItem.fromJson(item as Map<String, dynamic>))
          .toList();
      return Success(history);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch quiz history for book');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }
}
