import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'diagnostic_quiz_model.g.dart';

/// Request to generate a diagnostic quiz
@JsonSerializable()
class DiagnosticQuizRequest extends Equatable {
  final String subject;

  const DiagnosticQuizRequest({required this.subject});

  factory DiagnosticQuizRequest.fromJson(Map<String, dynamic> json) =>
      _$DiagnosticQuizRequestFromJson(json);

  Map<String, dynamic> toJson() => _$DiagnosticQuizRequestToJson(this);

  @override
  List<Object?> get props => [subject];
}

/// A single diagnostic question with multiple choice options
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

/// Response containing generated quiz
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

/// User's answer to a single question
@JsonSerializable()
class DiagnosticAnswer extends Equatable {
  final String question;
  @JsonKey(name: 'user_answer')
  final String userAnswer;

  const DiagnosticAnswer({
    required this.question,
    required this.userAnswer,
  });

  factory DiagnosticAnswer.fromJson(Map<String, dynamic> json) =>
      _$DiagnosticAnswerFromJson(json);

  Map<String, dynamic> toJson() => _$DiagnosticAnswerToJson(this);

  @override
  List<Object?> get props => [question, userAnswer];
}

/// Quiz submission with all answers
@JsonSerializable()
class DiagnosticQuizSubmission extends Equatable {
  final String subject;
  final List<DiagnosticAnswer> answers;

  const DiagnosticQuizSubmission({
    required this.subject,
    required this.answers,
  });

  factory DiagnosticQuizSubmission.fromJson(Map<String, dynamic> json) =>
      _$DiagnosticQuizSubmissionFromJson(json);

  Map<String, dynamic> toJson() => _$DiagnosticQuizSubmissionToJson(this);

  @override
  List<Object?> get props => [subject, answers];
}

/// AI evaluation result with recommendations
@JsonSerializable()
class DiagnosticQuizResult extends Equatable {
  final String level;
  @JsonKey(name: 'study_pace')
  final String studyPace;
  @JsonKey(name: 'study_style')
  final String studyStyle;
  @JsonKey(name: 'break_preference')
  final String breakPreference;

  const DiagnosticQuizResult({
    required this.level,
    required this.studyPace,
    required this.studyStyle,
    required this.breakPreference,
  });

  factory DiagnosticQuizResult.fromJson(Map<String, dynamic> json) =>
      _$DiagnosticQuizResultFromJson(json);

  Map<String, dynamic> toJson() => _$DiagnosticQuizResultToJson(this);

  @override
  List<Object?> get props => [level, studyPace, studyStyle, breakPreference];
}

/// Manual level setting request
@JsonSerializable()
class ManualLevelSetting extends Equatable {
  final String subject;
  final String level;
  @JsonKey(name: 'study_pace')
  final String? studyPace;
  @JsonKey(name: 'study_style')
  final String? studyStyle;
  @JsonKey(name: 'break_preference')
  final String? breakPreference;

  const ManualLevelSetting({
    required this.subject,
    required this.level,
    this.studyPace,
    this.studyStyle,
    this.breakPreference,
  });

  factory ManualLevelSetting.fromJson(Map<String, dynamic> json) =>
      _$ManualLevelSettingFromJson(json);

  Map<String, dynamic> toJson() => _$ManualLevelSettingToJson(this);

  @override
  List<Object?> get props => [subject, level, studyPace, studyStyle, breakPreference];
}

/// Subject profile stored in user document
@JsonSerializable()
class SubjectProfile extends Equatable {
  final String subject;
  final String level;
  @JsonKey(name: 'study_pace')
  final String studyPace;
  @JsonKey(name: 'study_style')
  final String studyStyle;
  @JsonKey(name: 'break_preference')
  final String breakPreference;
  @JsonKey(name: 'assessed_at')
  final String assessedAt;
  @JsonKey(name: 'assessment_method')
  final String assessmentMethod;

  const SubjectProfile({
    required this.subject,
    required this.level,
    required this.studyPace,
    required this.studyStyle,
    required this.breakPreference,
    required this.assessedAt,
    required this.assessmentMethod,
  });

  factory SubjectProfile.fromJson(Map<String, dynamic> json) =>
      _$SubjectProfileFromJson(json);

  Map<String, dynamic> toJson() => _$SubjectProfileToJson(this);

  @override
  List<Object?> get props => [
        subject,
        level,
        studyPace,
        studyStyle,
        breakPreference,
        assessedAt,
        assessmentMethod,
      ];
}
