import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'mood_log_model.g.dart';

@JsonSerializable()
class MoodLogModel extends Equatable {
  final String mood;
  final String date;
  @JsonKey(name: 'logged_at')
  final String? loggedAt;

  const MoodLogModel({
    required this.mood,
    required this.date,
    this.loggedAt,
  });

  factory MoodLogModel.fromJson(Map<String, dynamic> json) =>
      _$MoodLogModelFromJson(json);

  Map<String, dynamic> toJson() => _$MoodLogModelToJson(this);

  @override
  List<Object?> get props => [mood, date, loggedAt];
}

@JsonSerializable()
class MoodLogCreateRequest extends Equatable {
  final String mood;

  const MoodLogCreateRequest({required this.mood});

  factory MoodLogCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$MoodLogCreateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$MoodLogCreateRequestToJson(this);

  @override
  List<Object?> get props => [mood];
}

@JsonSerializable()
class MoodLogResponse extends Equatable {
  final bool success;
  final String message;
  final String mood;
  final String date;
  final Map<String, dynamic>? session;

  const MoodLogResponse({
    required this.success,
    required this.message,
    required this.mood,
    required this.date,
    this.session,
  });

  factory MoodLogResponse.fromJson(Map<String, dynamic> json) =>
      _$MoodLogResponseFromJson(json);

  Map<String, dynamic> toJson() => _$MoodLogResponseToJson(this);

  @override
  List<Object?> get props => [success, message, mood, date, session];
}

@JsonSerializable()
class TodayMoodResponse extends Equatable {
  final bool logged;
  final String? mood;
  final String date;

  const TodayMoodResponse({
    required this.logged,
    this.mood,
    required this.date,
  });

  factory TodayMoodResponse.fromJson(Map<String, dynamic> json) =>
      _$TodayMoodResponseFromJson(json);

  Map<String, dynamic> toJson() => _$TodayMoodResponseToJson(this);

  @override
  List<Object?> get props => [logged, mood, date];
}

// Mood emotion data with emojis
class MoodEmotion {
  final String label;
  final String emoji;
  final String description;

  const MoodEmotion({
    required this.label,
    required this.emoji,
    required this.description,
  });

  static const List<MoodEmotion> allMoods = [
    MoodEmotion(label: 'confused', emoji: '😕', description: 'Confused'),
    MoodEmotion(label: 'frustrated', emoji: '😤', description: 'Frustrated'),
    MoodEmotion(label: 'stressed', emoji: '😰', description: 'Stressed'),
    MoodEmotion(label: 'motivated', emoji: '💪', description: 'Motivated'),
    MoodEmotion(label: 'engaged', emoji: '😊', description: 'Engaged'),
    MoodEmotion(label: 'bored', emoji: '😑', description: 'Bored'),
    MoodEmotion(label: 'neutral', emoji: '😐', description: 'Neutral'),
    MoodEmotion(label: 'confident', emoji: '😎', description: 'Confident'),
  ];

  static MoodEmotion? fromLabel(String label) {
    try {
      return allMoods.firstWhere((mood) => mood.label == label.toLowerCase());
    } catch (e) {
      return null;
    }
  }
}

@JsonSerializable()
class MoodHistoryEntry extends Equatable {
  final String date;
  final String mood;
  @JsonKey(name: 'logged_at')
  final String? loggedAt;

  const MoodHistoryEntry({
    required this.date,
    required this.mood,
    this.loggedAt,
  });

  factory MoodHistoryEntry.fromJson(Map<String, dynamic> json) =>
      _$MoodHistoryEntryFromJson(json);

  Map<String, dynamic> toJson() => _$MoodHistoryEntryToJson(this);

  @override
  List<Object?> get props => [date, mood, loggedAt];
}

@JsonSerializable()
class MoodHistoryResponse extends Equatable {
  final List<MoodHistoryEntry> moodLogs;

  const MoodHistoryResponse({
    required this.moodLogs,
  });

  factory MoodHistoryResponse.fromJson(Map<String, dynamic> json) =>
      _$MoodHistoryResponseFromJson(json);

  Map<String, dynamic> toJson() => _$MoodHistoryResponseToJson(this);

  @override
  List<Object?> get props => [moodLogs];
}
