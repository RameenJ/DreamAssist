import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'subject_profile_model.g.dart';

@JsonSerializable()
class SubjectProfileModel extends Equatable {
  final String subject;
  final String level; // beginner, intermediate, advanced
  @JsonKey(name: 'study_pace')
  final String studyPace; // slow, moderate, fast
  @JsonKey(name: 'study_style')
  final String studyStyle; // theory-focused, practice-focused, mixed, visual, problem-solving based
  @JsonKey(name: 'break_preference')
  final String breakPreference;
  @JsonKey(name: 'assessed_at')
  final String assessedAt;
  @JsonKey(name: 'assessment_method')
  final String assessmentMethod; // quiz or manual
  @JsonKey(name: 'weak_topics')
  final List<String>? weakTopics;

  const SubjectProfileModel({
    required this.subject,
    required this.level,
    required this.studyPace,
    required this.studyStyle,
    required this.breakPreference,
    required this.assessedAt,
    required this.assessmentMethod,
    this.weakTopics,
  });

  factory SubjectProfileModel.fromJson(Map<String, dynamic> json) =>
      _$SubjectProfileModelFromJson(json);

  Map<String, dynamic> toJson() => _$SubjectProfileModelToJson(this);

  @override
  List<Object?> get props => [
        subject,
        level,
        studyPace,
        studyStyle,
        breakPreference,
        assessedAt,
        assessmentMethod,
        weakTopics,
      ];
}

@JsonSerializable()
class DiagnosticQuestion extends Equatable {
  final String question;
  final List<String> options;

  const DiagnosticQuestion({
    required this.question,
    required this.options,
  });

  factory DiagnosticQuestion.fromJson(Map<String, dynamic> json) =>
      _$DiagnosticQuestionFromJson(json);

  Map<String, dynamic> toJson() => _$DiagnosticQuestionToJson(this);

  @override
  List<Object?> get props => [question, options];
}

@JsonSerializable()
class DiagnosticQuizResponse extends Equatable {
  final String subject;
  final List<DiagnosticQuestion> questions;

  const DiagnosticQuizResponse({
    required this.subject,
    required this.questions,
  });

  factory DiagnosticQuizResponse.fromJson(Map<String, dynamic> json) =>
      _$DiagnosticQuizResponseFromJson(json);

  Map<String, dynamic> toJson() => _$DiagnosticQuizResponseToJson(this);

  @override
  List<Object?> get props => [subject, questions];
}

@JsonSerializable()
class SubjectProfileCreate extends Equatable {
  final String subject;
  final String level;
  @JsonKey(name: 'study_pace')
  final String studyPace;
  @JsonKey(name: 'study_style')
  final String studyStyle;
  @JsonKey(name: 'break_preference')
  final String breakPreference;

  const SubjectProfileCreate({
    required this.subject,
    required this.level,
    required this.studyPace,
    required this.studyStyle,
    required this.breakPreference,
  });

  factory SubjectProfileCreate.fromJson(Map<String, dynamic> json) =>
      _$SubjectProfileCreateFromJson(json);

  Map<String, dynamic> toJson() => _$SubjectProfileCreateToJson(this);

  @override
  List<Object?> get props => [
        subject,
        level,
        studyPace,
        studyStyle,
        breakPreference,
      ];
}
