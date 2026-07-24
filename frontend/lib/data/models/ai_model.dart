import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'ai_model.g.dart';

// Chat models for AI Mentor
@JsonSerializable()
class ChatRequest extends Equatable {
  final String query;

  const ChatRequest({required this.query});

  factory ChatRequest.fromJson(Map<String, dynamic> json) =>
      _$ChatRequestFromJson(json);

  Map<String, dynamic> toJson() => _$ChatRequestToJson(this);

  @override
  List<Object?> get props => [query];
}

@JsonSerializable()
class ChatResponse extends Equatable {
  final String answer;
  @JsonKey(name: 'sources')
  final List<String>? sources;

  const ChatResponse({
    required this.answer,
    this.sources,
  });

  factory ChatResponse.fromJson(Map<String, dynamic> json) =>
      _$ChatResponseFromJson(json);

  Map<String, dynamic> toJson() => _$ChatResponseToJson(this);

  @override
  List<Object?> get props => [answer, sources];
}

// Summarization models
@JsonSerializable()
class SummarizeRequest extends Equatable {
  @JsonKey(name: 'text_to_summarize')
  final String textToSummarize;

  const SummarizeRequest({required this.textToSummarize});

  factory SummarizeRequest.fromJson(Map<String, dynamic> json) =>
      _$SummarizeRequestFromJson(json);

  Map<String, dynamic> toJson() => _$SummarizeRequestToJson(this);

  @override
  List<Object?> get props => [textToSummarize];
}

@JsonSerializable()
class SummarizationResponse extends Equatable {
  final String summary;

  const SummarizationResponse({required this.summary});

  factory SummarizationResponse.fromJson(Map<String, dynamic> json) =>
      _$SummarizationResponseFromJson(json);

  Map<String, dynamic> toJson() => _$SummarizationResponseToJson(this);

  @override
  List<Object?> get props => [summary];
}

// Flashcard models
@JsonSerializable()
class FlashcardRequest extends Equatable {
  @JsonKey(name: 'text_to_generate_from')
  final String textForFlashcards;

  const FlashcardRequest({required this.textForFlashcards});

  factory FlashcardRequest.fromJson(Map<String, dynamic> json) =>
      _$FlashcardRequestFromJson(json);

  Map<String, dynamic> toJson() => _$FlashcardRequestToJson(this);

  @override
  List<Object?> get props => [textForFlashcards];
}

@JsonSerializable()
class FlashcardModel extends Equatable {
  @JsonKey(name: 'front')
  final String question;
  @JsonKey(name: 'back')
  final String answer;

  const FlashcardModel({
    required this.question,
    required this.answer,
  });

  factory FlashcardModel.fromJson(Map<String, dynamic> json) =>
      _$FlashcardModelFromJson(json);

  Map<String, dynamic> toJson() => _$FlashcardModelToJson(this);

  @override
  List<Object?> get props => [question, answer];
}

@JsonSerializable()
class FlashcardsResponse extends Equatable {
  final List<FlashcardModel> flashcards;

  const FlashcardsResponse({required this.flashcards});

  factory FlashcardsResponse.fromJson(Map<String, dynamic> json) =>
      _$FlashcardsResponseFromJson(json);

  Map<String, dynamic> toJson() => _$FlashcardsResponseToJson(this);

  @override
  List<Object?> get props => [flashcards];
}

// Quiz models
@JsonSerializable()
class QuizGenerationRequest extends Equatable {
  @JsonKey(name: 'book_id')
  final String? bookId;
  @JsonKey(name: 'topic_id')
  final String? topicId;
  @JsonKey(name: 'num_questions')
  final int numQuestions;

  const QuizGenerationRequest({
    this.bookId,
    this.topicId,
    required this.numQuestions,
  });

  factory QuizGenerationRequest.fromJson(Map<String, dynamic> json) =>
      _$QuizGenerationRequestFromJson(json);

  Map<String, dynamic> toJson() => _$QuizGenerationRequestToJson(this);

  @override
  List<Object?> get props => [bookId, topicId, numQuestions];
}

@JsonSerializable()
class QuizQuestionModel extends Equatable {
  @JsonKey(name: 'question_text')
  final String questionText;
  @JsonKey(name: 'correct_answer')
  final String correctAnswer;
  @JsonKey(name: 'answer_variants')
  final List<String> answerVariants;
  final String explanation;

  const QuizQuestionModel({
    required this.questionText,
    required this.correctAnswer,
    required this.answerVariants,
    required this.explanation,
  });

  factory QuizQuestionModel.fromJson(Map<String, dynamic> json) =>
      _$QuizQuestionModelFromJson(json);

  Map<String, dynamic> toJson() => _$QuizQuestionModelToJson(this);

  @override
  List<Object?> get props => [questionText, correctAnswer, answerVariants, explanation];
}

@JsonSerializable()
class GeneratedQuiz extends Equatable {
  @JsonKey(name: 'quiz_id')
  final String quizId;
  @JsonKey(name: 'book_id')
  final String bookId;
  final List<QuizQuestionModel> questions;

  const GeneratedQuiz({
    required this.quizId,
    required this.bookId,
    required this.questions,
  });

  factory GeneratedQuiz.fromJson(Map<String, dynamic> json) =>
      _$GeneratedQuizFromJson(json);

  Map<String, dynamic> toJson() => _$GeneratedQuizToJson(this);

  @override
  List<Object?> get props => [quizId, bookId, questions];
}

@JsonSerializable()
class UserAnswer extends Equatable {
  @JsonKey(name: 'question_text')
  final String questionText;
  @JsonKey(name: 'user_answer')
  final String userAnswer;

  const UserAnswer({
    required this.questionText,
    required this.userAnswer,
  });

  factory UserAnswer.fromJson(Map<String, dynamic> json) =>
      _$UserAnswerFromJson(json);

  Map<String, dynamic> toJson() => _$UserAnswerToJson(this);

  @override
  List<Object?> get props => [questionText, userAnswer];
}

@JsonSerializable()
class QuizEvaluationRequest extends Equatable {
  @JsonKey(name: 'quiz_id')
  final String quizId;
  @JsonKey(name: 'attempted_answers')
  final List<UserAnswer> attemptedAnswers;
  @JsonKey(name: 'book_id')
  final String bookId;
  @JsonKey(name: 'topic_name')
  final String topicName;

  const QuizEvaluationRequest({
    required this.quizId,
    required this.attemptedAnswers,
    required this.bookId,
    required this.topicName,
  });

  factory QuizEvaluationRequest.fromJson(Map<String, dynamic> json) =>
      _$QuizEvaluationRequestFromJson(json);

  Map<String, dynamic> toJson() => _$QuizEvaluationRequestToJson(this);

  @override
  List<Object?> get props => [quizId, attemptedAnswers, bookId, topicName];
}

@JsonSerializable()
class EvaluatedQuestionResult extends Equatable {
  @JsonKey(name: 'question_text')
  final String questionText;
  @JsonKey(name: 'user_answer')
  final String userAnswer;
  @JsonKey(name: 'correct_answer')
  final String correctAnswer;
  @JsonKey(name: 'correct_explanation')
  final String correctExplanation;
  @JsonKey(name: 'similarity_score')
  final double similarityScore;

  const EvaluatedQuestionResult({
    required this.questionText,
    required this.userAnswer,
    required this.correctAnswer,
    required this.correctExplanation,
    required this.similarityScore,
  });

  factory EvaluatedQuestionResult.fromJson(Map<String, dynamic> json) =>
      _$EvaluatedQuestionResultFromJson(json);

  Map<String, dynamic> toJson() => _$EvaluatedQuestionResultToJson(this);

  @override
  List<Object?> get props => [questionText, userAnswer, correctAnswer, correctExplanation, similarityScore];
}

@JsonSerializable()
class QuizEvaluationResponse extends Equatable {
  @JsonKey(name: 'quiz_id')
  final String quizId;
  @JsonKey(name: 'total_score')
  final double totalScore;
  @JsonKey(name: 'total_grade')
  final String totalGrade;
  final List<EvaluatedQuestionResult> results;
  @JsonKey(name: 'book_id')
  final String? bookId;
  
  // AI Mentor Recommendations
  @JsonKey(name: 'study_recommendations')
  final String? studyRecommendations;
  @JsonKey(name: 'weak_topics')
  final List<String>? weakTopics;
  @JsonKey(name: 'strong_topics')
  final List<String>? strongTopics;
  @JsonKey(name: 'next_steps')
  final List<String>? nextSteps;

  const QuizEvaluationResponse({
    required this.quizId,
    required this.totalScore,
    required this.totalGrade,
    required this.results,
    this.bookId,
    this.studyRecommendations,
    this.weakTopics,
    this.strongTopics,
    this.nextSteps,
  });

  factory QuizEvaluationResponse.fromJson(Map<String, dynamic> json) =>
      _$QuizEvaluationResponseFromJson(json);

  Map<String, dynamic> toJson() => _$QuizEvaluationResponseToJson(this);

  @override
  List<Object?> get props => [quizId, totalScore, totalGrade, results, bookId, studyRecommendations, weakTopics, strongTopics, nextSteps];
}

// Flashcard History Models
@JsonSerializable()
class FlashcardPublic extends Equatable {
  final String id;
  final String front;
  final String back;
  @JsonKey(name: 'created_at')
  final String? createdAt;

  const FlashcardPublic({
    required this.id,
    required this.front,
    required this.back,
    this.createdAt,
  });

  factory FlashcardPublic.fromJson(Map<String, dynamic> json) =>
      _$FlashcardPublicFromJson(json);

  Map<String, dynamic> toJson() => _$FlashcardPublicToJson(this);

  @override
  List<Object?> get props => [id, front, back, createdAt];
}

@JsonSerializable()
class FlashcardSetPublic extends Equatable {
  final String id;
  @JsonKey(name: 'topic_name')
  final String topicName;
  @JsonKey(name: 'flashcard_count')
  final int flashcardCount;
  @JsonKey(name: 'created_at')
  final String? createdAt;
  final List<FlashcardPublic>? flashcards;

  const FlashcardSetPublic({
    required this.id,
    required this.topicName,
    required this.flashcardCount,
    this.createdAt,
    this.flashcards,
  });

  factory FlashcardSetPublic.fromJson(Map<String, dynamic> json) =>
      _$FlashcardSetPublicFromJson(json);

  Map<String, dynamic> toJson() => _$FlashcardSetPublicToJson(this);

  @override
  List<Object?> get props => [id, topicName, flashcardCount, createdAt, flashcards];
}

// Quiz History Models
@JsonSerializable()
class QuizHistoryItem extends Equatable {
  final String id;
  @JsonKey(name: 'book_id')
  final String bookId;
  @JsonKey(name: 'topic_name')
  final String topicName;
  @JsonKey(name: 'total_score')
  final double totalScore;
  @JsonKey(name: 'total_grade')
  final String totalGrade;
  @JsonKey(name: 'attempted_at')
  final String attemptedAt;

  const QuizHistoryItem({
    required this.id,
    required this.bookId,
    required this.topicName,
    required this.totalScore,
    required this.totalGrade,
    required this.attemptedAt,
  });

  factory QuizHistoryItem.fromJson(Map<String, dynamic> json) =>
      _$QuizHistoryItemFromJson(json);

  Map<String, dynamic> toJson() => _$QuizHistoryItemToJson(this);

  @override
  List<Object?> get props => [id, bookId, topicName, totalScore, totalGrade, attemptedAt];
}

@JsonSerializable()
class QuizHistoryResponse extends Equatable {
  final List<QuizHistoryItem> history;

  const QuizHistoryResponse({required this.history});

  factory QuizHistoryResponse.fromJson(Map<String, dynamic> json) =>
      _$QuizHistoryResponseFromJson(json);

  Map<String, dynamic> toJson() => _$QuizHistoryResponseToJson(this);

  @override
  List<Object?> get props => [history];
}
