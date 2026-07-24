import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'progress_model.g.dart';

/// Global statistics for user progress
@JsonSerializable()
class GlobalStats extends Equatable {
  @JsonKey(name: 'total_quizzes')
  final int totalQuizzes;
  @JsonKey(name: 'average_score')
  final double averageScore;
  @JsonKey(name: 'weakest_subject')
  final String? weakestSubject;
  @JsonKey(name: 'total_ai_chats')
  final int totalAiChats;
  @JsonKey(name: 'total_summaries')
  final int totalSummaries;
  @JsonKey(name: 'total_flashcards')
  final int totalFlashcards;
  @JsonKey(name: 'total_study_notes')
  final int totalStudyNotes;
  @JsonKey(name: 'total_qna')
  final int totalQna;
  @JsonKey(name: 'total_quiz_generated')
  final int totalQuizGenerated;

  const GlobalStats({
    required this.totalQuizzes,
    required this.averageScore,
    this.weakestSubject,
    this.totalAiChats = 0,
    this.totalSummaries = 0,
    this.totalFlashcards = 0,
    this.totalStudyNotes = 0,
    this.totalQna = 0,
    this.totalQuizGenerated = 0,
  });

  factory GlobalStats.fromJson(Map<String, dynamic> json) =>
      _$GlobalStatsFromJson(json);

  Map<String, dynamic> toJson() => _$GlobalStatsToJson(this);

  @override
  List<Object?> get props => [
        totalQuizzes,
        averageScore,
        weakestSubject,
        totalAiChats,
        totalSummaries,
        totalFlashcards,
        totalStudyNotes,
        totalQna,
        totalQuizGenerated,
      ];
}

/// Chart data point for line and bar charts
@JsonSerializable()
class ChartDataPoint extends Equatable {
  final String label;
  final double value;

  const ChartDataPoint({
    required this.label,
    required this.value,
  });

  factory ChartDataPoint.fromJson(Map<String, dynamic> json) =>
      _$ChartDataPointFromJson(json);

  Map<String, dynamic> toJson() => _$ChartDataPointToJson(this);

  @override
  List<Object?> get props => [label, value];
}

/// Pie chart data point
@JsonSerializable()
class PieChartDataPoint extends Equatable {
  final String name;
  final int value;

  const PieChartDataPoint({
    required this.name,
    required this.value,
  });

  factory PieChartDataPoint.fromJson(Map<String, dynamic> json) =>
      _$PieChartDataPointFromJson(json);

  Map<String, dynamic> toJson() => _$PieChartDataPointToJson(this);

  @override
  List<Object?> get props => [name, value];
}

/// Global progress response (all data for progress page)
@JsonSerializable()
class GlobalProgressResponse extends Equatable {
  final GlobalStats stats;
  @JsonKey(name: 'score_over_time')
  final List<ChartDataPoint> scoreOverTime;
  @JsonKey(name: 'performance_by_subject')
  final List<ChartDataPoint> performanceBySubject;
  @JsonKey(name: 'grade_distribution')
  final List<PieChartDataPoint> gradeDistribution;

  const GlobalProgressResponse({
    required this.stats,
    required this.scoreOverTime,
    required this.performanceBySubject,
    required this.gradeDistribution,
  });

  factory GlobalProgressResponse.fromJson(Map<String, dynamic> json) =>
      _$GlobalProgressResponseFromJson(json);

  Map<String, dynamic> toJson() => _$GlobalProgressResponseToJson(this);

  @override
  List<Object?> get props => [
        stats,
        scoreOverTime,
        performanceBySubject,
        gradeDistribution,
      ];
}

/// Topic status for book progress
@JsonSerializable()
class TopicStatus extends Equatable {
  @JsonKey(name: 'topic_title')
  final String topicTitle;
  final String status; // 'completed', 'failed', 'not_attempted'
  final double? score;

  const TopicStatus({
    required this.topicTitle,
    required this.status,
    this.score,
  });

  factory TopicStatus.fromJson(Map<String, dynamic> json) =>
      _$TopicStatusFromJson(json);

  Map<String, dynamic> toJson() => _$TopicStatusToJson(this);

  @override
  List<Object?> get props => [topicTitle, status, score];
}

/// Book progress response
@JsonSerializable()
class BookProgressResponse extends Equatable {
  @JsonKey(name: 'completion_status')
  final List<TopicStatus> completionStatus;
  @JsonKey(name: 'performance_by_topic')
  final List<ChartDataPoint> performanceByTopic;

  const BookProgressResponse({
    required this.completionStatus,
    required this.performanceByTopic,
  });

  factory BookProgressResponse.fromJson(Map<String, dynamic> json) =>
      _$BookProgressResponseFromJson(json);

  Map<String, dynamic> toJson() => _$BookProgressResponseToJson(this);

  @override
  List<Object?> get props => [completionStatus, performanceByTopic];
}
