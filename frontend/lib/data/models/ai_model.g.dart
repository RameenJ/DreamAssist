// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ai_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ChatRequest _$ChatRequestFromJson(Map<String, dynamic> json) =>
    ChatRequest(query: json['query'] as String);

Map<String, dynamic> _$ChatRequestToJson(ChatRequest instance) =>
    <String, dynamic>{'query': instance.query};

ChatResponse _$ChatResponseFromJson(Map<String, dynamic> json) => ChatResponse(
  answer: json['answer'] as String,
  sources: (json['sources'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
);

Map<String, dynamic> _$ChatResponseToJson(ChatResponse instance) =>
    <String, dynamic>{'answer': instance.answer, 'sources': instance.sources};

SummarizeRequest _$SummarizeRequestFromJson(Map<String, dynamic> json) =>
    SummarizeRequest(textToSummarize: json['text_to_summarize'] as String);

Map<String, dynamic> _$SummarizeRequestToJson(SummarizeRequest instance) =>
    <String, dynamic>{'text_to_summarize': instance.textToSummarize};

SummarizationResponse _$SummarizationResponseFromJson(
  Map<String, dynamic> json,
) => SummarizationResponse(summary: json['summary'] as String);

Map<String, dynamic> _$SummarizationResponseToJson(
  SummarizationResponse instance,
) => <String, dynamic>{'summary': instance.summary};

FlashcardRequest _$FlashcardRequestFromJson(Map<String, dynamic> json) =>
    FlashcardRequest(
      textForFlashcards: json['text_to_generate_from'] as String,
    );

Map<String, dynamic> _$FlashcardRequestToJson(FlashcardRequest instance) =>
    <String, dynamic>{'text_to_generate_from': instance.textForFlashcards};

FlashcardModel _$FlashcardModelFromJson(Map<String, dynamic> json) =>
    FlashcardModel(
      question: json['front'] as String,
      answer: json['back'] as String,
    );

Map<String, dynamic> _$FlashcardModelToJson(FlashcardModel instance) =>
    <String, dynamic>{'front': instance.question, 'back': instance.answer};

FlashcardsResponse _$FlashcardsResponseFromJson(Map<String, dynamic> json) =>
    FlashcardsResponse(
      flashcards: (json['flashcards'] as List<dynamic>)
          .map((e) => FlashcardModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$FlashcardsResponseToJson(FlashcardsResponse instance) =>
    <String, dynamic>{'flashcards': instance.flashcards};

QuizGenerationRequest _$QuizGenerationRequestFromJson(
  Map<String, dynamic> json,
) => QuizGenerationRequest(
  bookId: json['book_id'] as String?,
  topicId: json['topic_id'] as String?,
  numQuestions: (json['num_questions'] as num).toInt(),
);

Map<String, dynamic> _$QuizGenerationRequestToJson(
  QuizGenerationRequest instance,
) => <String, dynamic>{
  'book_id': instance.bookId,
  'topic_id': instance.topicId,
  'num_questions': instance.numQuestions,
};

QuizQuestionModel _$QuizQuestionModelFromJson(Map<String, dynamic> json) =>
    QuizQuestionModel(
      questionText: json['question_text'] as String,
      correctAnswer: json['correct_answer'] as String,
      answerVariants: (json['answer_variants'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      explanation: json['explanation'] as String,
    );

Map<String, dynamic> _$QuizQuestionModelToJson(QuizQuestionModel instance) =>
    <String, dynamic>{
      'question_text': instance.questionText,
      'correct_answer': instance.correctAnswer,
      'answer_variants': instance.answerVariants,
      'explanation': instance.explanation,
    };

GeneratedQuiz _$GeneratedQuizFromJson(Map<String, dynamic> json) =>
    GeneratedQuiz(
      quizId: json['quiz_id'] as String,
      bookId: json['book_id'] as String,
      questions: (json['questions'] as List<dynamic>)
          .map((e) => QuizQuestionModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$GeneratedQuizToJson(GeneratedQuiz instance) =>
    <String, dynamic>{
      'quiz_id': instance.quizId,
      'book_id': instance.bookId,
      'questions': instance.questions,
    };

UserAnswer _$UserAnswerFromJson(Map<String, dynamic> json) => UserAnswer(
  questionText: json['question_text'] as String,
  userAnswer: json['user_answer'] as String,
);

Map<String, dynamic> _$UserAnswerToJson(UserAnswer instance) =>
    <String, dynamic>{
      'question_text': instance.questionText,
      'user_answer': instance.userAnswer,
    };

QuizEvaluationRequest _$QuizEvaluationRequestFromJson(
  Map<String, dynamic> json,
) => QuizEvaluationRequest(
  quizId: json['quiz_id'] as String,
  attemptedAnswers: (json['attempted_answers'] as List<dynamic>)
      .map((e) => UserAnswer.fromJson(e as Map<String, dynamic>))
      .toList(),
  bookId: json['book_id'] as String,
  topicName: json['topic_name'] as String,
);

Map<String, dynamic> _$QuizEvaluationRequestToJson(
  QuizEvaluationRequest instance,
) => <String, dynamic>{
  'quiz_id': instance.quizId,
  'attempted_answers': instance.attemptedAnswers,
  'book_id': instance.bookId,
  'topic_name': instance.topicName,
};

EvaluatedQuestionResult _$EvaluatedQuestionResultFromJson(
  Map<String, dynamic> json,
) => EvaluatedQuestionResult(
  questionText: json['question_text'] as String,
  userAnswer: json['user_answer'] as String,
  correctAnswer: json['correct_answer'] as String,
  correctExplanation: json['correct_explanation'] as String,
  similarityScore: (json['similarity_score'] as num).toDouble(),
);

Map<String, dynamic> _$EvaluatedQuestionResultToJson(
  EvaluatedQuestionResult instance,
) => <String, dynamic>{
  'question_text': instance.questionText,
  'user_answer': instance.userAnswer,
  'correct_answer': instance.correctAnswer,
  'correct_explanation': instance.correctExplanation,
  'similarity_score': instance.similarityScore,
};

QuizEvaluationResponse _$QuizEvaluationResponseFromJson(
  Map<String, dynamic> json,
) => QuizEvaluationResponse(
  quizId: json['quiz_id'] as String,
  totalScore: (json['total_score'] as num).toDouble(),
  totalGrade: json['total_grade'] as String,
  results: (json['results'] as List<dynamic>)
      .map((e) => EvaluatedQuestionResult.fromJson(e as Map<String, dynamic>))
      .toList(),
  bookId: json['book_id'] as String?,
  studyRecommendations: json['study_recommendations'] as String?,
  weakTopics: (json['weak_topics'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  strongTopics: (json['strong_topics'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
  nextSteps: (json['next_steps'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
);

Map<String, dynamic> _$QuizEvaluationResponseToJson(
  QuizEvaluationResponse instance,
) => <String, dynamic>{
  'quiz_id': instance.quizId,
  'total_score': instance.totalScore,
  'total_grade': instance.totalGrade,
  'results': instance.results,
  'book_id': instance.bookId,
  'study_recommendations': instance.studyRecommendations,
  'weak_topics': instance.weakTopics,
  'strong_topics': instance.strongTopics,
  'next_steps': instance.nextSteps,
};

FlashcardPublic _$FlashcardPublicFromJson(Map<String, dynamic> json) =>
    FlashcardPublic(
      id: json['id'] as String,
      front: json['front'] as String,
      back: json['back'] as String,
      createdAt: json['created_at'] as String?,
    );

Map<String, dynamic> _$FlashcardPublicToJson(FlashcardPublic instance) =>
    <String, dynamic>{
      'id': instance.id,
      'front': instance.front,
      'back': instance.back,
      'created_at': instance.createdAt,
    };

FlashcardSetPublic _$FlashcardSetPublicFromJson(Map<String, dynamic> json) =>
    FlashcardSetPublic(
      id: json['id'] as String,
      topicName: json['topic_name'] as String,
      flashcardCount: (json['flashcard_count'] as num).toInt(),
      createdAt: json['created_at'] as String?,
      flashcards: (json['flashcards'] as List<dynamic>?)
          ?.map((e) => FlashcardPublic.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$FlashcardSetPublicToJson(FlashcardSetPublic instance) =>
    <String, dynamic>{
      'id': instance.id,
      'topic_name': instance.topicName,
      'flashcard_count': instance.flashcardCount,
      'created_at': instance.createdAt,
      'flashcards': instance.flashcards,
    };

QuizHistoryItem _$QuizHistoryItemFromJson(Map<String, dynamic> json) =>
    QuizHistoryItem(
      id: json['id'] as String,
      bookId: json['book_id'] as String,
      topicName: json['topic_name'] as String,
      totalScore: (json['total_score'] as num).toDouble(),
      totalGrade: json['total_grade'] as String,
      attemptedAt: json['attempted_at'] as String,
    );

Map<String, dynamic> _$QuizHistoryItemToJson(QuizHistoryItem instance) =>
    <String, dynamic>{
      'id': instance.id,
      'book_id': instance.bookId,
      'topic_name': instance.topicName,
      'total_score': instance.totalScore,
      'total_grade': instance.totalGrade,
      'attempted_at': instance.attemptedAt,
    };

QuizHistoryResponse _$QuizHistoryResponseFromJson(Map<String, dynamic> json) =>
    QuizHistoryResponse(
      history: (json['history'] as List<dynamic>)
          .map((e) => QuizHistoryItem.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$QuizHistoryResponseToJson(
  QuizHistoryResponse instance,
) => <String, dynamic>{'history': instance.history};
