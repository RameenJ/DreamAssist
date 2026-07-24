// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'mood_log_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MoodLogModel _$MoodLogModelFromJson(Map<String, dynamic> json) => MoodLogModel(
  mood: json['mood'] as String,
  date: json['date'] as String,
  loggedAt: json['logged_at'] as String?,
);

Map<String, dynamic> _$MoodLogModelToJson(MoodLogModel instance) =>
    <String, dynamic>{
      'mood': instance.mood,
      'date': instance.date,
      'logged_at': instance.loggedAt,
    };

MoodLogCreateRequest _$MoodLogCreateRequestFromJson(
  Map<String, dynamic> json,
) => MoodLogCreateRequest(mood: json['mood'] as String);

Map<String, dynamic> _$MoodLogCreateRequestToJson(
  MoodLogCreateRequest instance,
) => <String, dynamic>{'mood': instance.mood};

MoodLogResponse _$MoodLogResponseFromJson(Map<String, dynamic> json) =>
    MoodLogResponse(
      success: json['success'] as bool,
      message: json['message'] as String,
      mood: json['mood'] as String,
      date: json['date'] as String,
      session: json['session'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$MoodLogResponseToJson(MoodLogResponse instance) =>
    <String, dynamic>{
      'success': instance.success,
      'message': instance.message,
      'mood': instance.mood,
      'date': instance.date,
      'session': instance.session,
    };

TodayMoodResponse _$TodayMoodResponseFromJson(Map<String, dynamic> json) =>
    TodayMoodResponse(
      logged: json['logged'] as bool,
      mood: json['mood'] as String?,
      date: json['date'] as String,
    );

Map<String, dynamic> _$TodayMoodResponseToJson(TodayMoodResponse instance) =>
    <String, dynamic>{
      'logged': instance.logged,
      'mood': instance.mood,
      'date': instance.date,
    };

MoodHistoryEntry _$MoodHistoryEntryFromJson(Map<String, dynamic> json) =>
    MoodHistoryEntry(
      date: json['date'] as String,
      mood: json['mood'] as String,
      loggedAt: json['logged_at'] as String?,
    );

Map<String, dynamic> _$MoodHistoryEntryToJson(MoodHistoryEntry instance) =>
    <String, dynamic>{
      'date': instance.date,
      'mood': instance.mood,
      'logged_at': instance.loggedAt,
    };

MoodHistoryResponse _$MoodHistoryResponseFromJson(Map<String, dynamic> json) =>
    MoodHistoryResponse(
      moodLogs: (json['moodLogs'] as List<dynamic>)
          .map((e) => MoodHistoryEntry.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$MoodHistoryResponseToJson(
  MoodHistoryResponse instance,
) => <String, dynamic>{'moodLogs': instance.moodLogs};
