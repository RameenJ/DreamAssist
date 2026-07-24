// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'progress_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

GlobalStats _$GlobalStatsFromJson(Map<String, dynamic> json) => GlobalStats(
  totalQuizzes: (json['total_quizzes'] as num).toInt(),
  averageScore: (json['average_score'] as num).toDouble(),
  weakestSubject: json['weakest_subject'] as String?,
  totalAiChats: (json['total_ai_chats'] as num?)?.toInt() ?? 0,
  totalSummaries: (json['total_summaries'] as num?)?.toInt() ?? 0,
  totalFlashcards: (json['total_flashcards'] as num?)?.toInt() ?? 0,
  totalStudyNotes: (json['total_study_notes'] as num?)?.toInt() ?? 0,
  totalQna: (json['total_qna'] as num?)?.toInt() ?? 0,
  totalQuizGenerated: (json['total_quiz_generated'] as num?)?.toInt() ?? 0,
);

Map<String, dynamic> _$GlobalStatsToJson(GlobalStats instance) =>
    <String, dynamic>{
      'total_quizzes': instance.totalQuizzes,
      'average_score': instance.averageScore,
      'weakest_subject': instance.weakestSubject,
      'total_ai_chats': instance.totalAiChats,
      'total_summaries': instance.totalSummaries,
      'total_flashcards': instance.totalFlashcards,
      'total_study_notes': instance.totalStudyNotes,
      'total_qna': instance.totalQna,
      'total_quiz_generated': instance.totalQuizGenerated,
    };

ChartDataPoint _$ChartDataPointFromJson(Map<String, dynamic> json) =>
    ChartDataPoint(
      label: json['label'] as String,
      value: (json['value'] as num).toDouble(),
    );

Map<String, dynamic> _$ChartDataPointToJson(ChartDataPoint instance) =>
    <String, dynamic>{'label': instance.label, 'value': instance.value};

PieChartDataPoint _$PieChartDataPointFromJson(Map<String, dynamic> json) =>
    PieChartDataPoint(
      name: json['name'] as String,
      value: (json['value'] as num).toInt(),
    );

Map<String, dynamic> _$PieChartDataPointToJson(PieChartDataPoint instance) =>
    <String, dynamic>{'name': instance.name, 'value': instance.value};

GlobalProgressResponse _$GlobalProgressResponseFromJson(
  Map<String, dynamic> json,
) => GlobalProgressResponse(
  stats: GlobalStats.fromJson(json['stats'] as Map<String, dynamic>),
  scoreOverTime: (json['score_over_time'] as List<dynamic>)
      .map((e) => ChartDataPoint.fromJson(e as Map<String, dynamic>))
      .toList(),
  performanceBySubject: (json['performance_by_subject'] as List<dynamic>)
      .map((e) => ChartDataPoint.fromJson(e as Map<String, dynamic>))
      .toList(),
  gradeDistribution: (json['grade_distribution'] as List<dynamic>)
      .map((e) => PieChartDataPoint.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$GlobalProgressResponseToJson(
  GlobalProgressResponse instance,
) => <String, dynamic>{
  'stats': instance.stats,
  'score_over_time': instance.scoreOverTime,
  'performance_by_subject': instance.performanceBySubject,
  'grade_distribution': instance.gradeDistribution,
};

TopicStatus _$TopicStatusFromJson(Map<String, dynamic> json) => TopicStatus(
  topicTitle: json['topic_title'] as String,
  status: json['status'] as String,
  score: (json['score'] as num?)?.toDouble(),
);

Map<String, dynamic> _$TopicStatusToJson(TopicStatus instance) =>
    <String, dynamic>{
      'topic_title': instance.topicTitle,
      'status': instance.status,
      'score': instance.score,
    };

BookProgressResponse _$BookProgressResponseFromJson(
  Map<String, dynamic> json,
) => BookProgressResponse(
  completionStatus: (json['completion_status'] as List<dynamic>)
      .map((e) => TopicStatus.fromJson(e as Map<String, dynamic>))
      .toList(),
  performanceByTopic: (json['performance_by_topic'] as List<dynamic>)
      .map((e) => ChartDataPoint.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$BookProgressResponseToJson(
  BookProgressResponse instance,
) => <String, dynamic>{
  'completion_status': instance.completionStatus,
  'performance_by_topic': instance.performanceByTopic,
};
