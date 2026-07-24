// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'diagnostic_quiz_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DiagnosticQuizRequest _$DiagnosticQuizRequestFromJson(
  Map<String, dynamic> json,
) => DiagnosticQuizRequest(subject: json['subject'] as String);

Map<String, dynamic> _$DiagnosticQuizRequestToJson(
  DiagnosticQuizRequest instance,
) => <String, dynamic>{'subject': instance.subject};

DiagnosticQuestion _$DiagnosticQuestionFromJson(Map<String, dynamic> json) =>
    DiagnosticQuestion(
      question: json['question'] as String,
      options: (json['options'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$DiagnosticQuestionToJson(DiagnosticQuestion instance) =>
    <String, dynamic>{
      'question': instance.question,
      'options': instance.options,
    };

DiagnosticQuizResponse _$DiagnosticQuizResponseFromJson(
  Map<String, dynamic> json,
) => DiagnosticQuizResponse(
  subject: json['subject'] as String,
  questions: (json['questions'] as List<dynamic>)
      .map((e) => DiagnosticQuestion.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$DiagnosticQuizResponseToJson(
  DiagnosticQuizResponse instance,
) => <String, dynamic>{
  'subject': instance.subject,
  'questions': instance.questions,
};

DiagnosticAnswer _$DiagnosticAnswerFromJson(Map<String, dynamic> json) =>
    DiagnosticAnswer(
      question: json['question'] as String,
      userAnswer: json['user_answer'] as String,
    );

Map<String, dynamic> _$DiagnosticAnswerToJson(DiagnosticAnswer instance) =>
    <String, dynamic>{
      'question': instance.question,
      'user_answer': instance.userAnswer,
    };

DiagnosticQuizSubmission _$DiagnosticQuizSubmissionFromJson(
  Map<String, dynamic> json,
) => DiagnosticQuizSubmission(
  subject: json['subject'] as String,
  answers: (json['answers'] as List<dynamic>)
      .map((e) => DiagnosticAnswer.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$DiagnosticQuizSubmissionToJson(
  DiagnosticQuizSubmission instance,
) => <String, dynamic>{
  'subject': instance.subject,
  'answers': instance.answers,
};

DiagnosticQuizResult _$DiagnosticQuizResultFromJson(
  Map<String, dynamic> json,
) => DiagnosticQuizResult(
  level: json['level'] as String,
  studyPace: json['study_pace'] as String,
  studyStyle: json['study_style'] as String,
  breakPreference: json['break_preference'] as String,
);

Map<String, dynamic> _$DiagnosticQuizResultToJson(
  DiagnosticQuizResult instance,
) => <String, dynamic>{
  'level': instance.level,
  'study_pace': instance.studyPace,
  'study_style': instance.studyStyle,
  'break_preference': instance.breakPreference,
};

ManualLevelSetting _$ManualLevelSettingFromJson(Map<String, dynamic> json) =>
    ManualLevelSetting(
      subject: json['subject'] as String,
      level: json['level'] as String,
      studyPace: json['study_pace'] as String?,
      studyStyle: json['study_style'] as String?,
      breakPreference: json['break_preference'] as String?,
    );

Map<String, dynamic> _$ManualLevelSettingToJson(ManualLevelSetting instance) =>
    <String, dynamic>{
      'subject': instance.subject,
      'level': instance.level,
      'study_pace': instance.studyPace,
      'study_style': instance.studyStyle,
      'break_preference': instance.breakPreference,
    };

SubjectProfile _$SubjectProfileFromJson(Map<String, dynamic> json) =>
    SubjectProfile(
      subject: json['subject'] as String,
      level: json['level'] as String,
      studyPace: json['study_pace'] as String,
      studyStyle: json['study_style'] as String,
      breakPreference: json['break_preference'] as String,
      assessedAt: json['assessed_at'] as String,
      assessmentMethod: json['assessment_method'] as String,
    );

Map<String, dynamic> _$SubjectProfileToJson(SubjectProfile instance) =>
    <String, dynamic>{
      'subject': instance.subject,
      'level': instance.level,
      'study_pace': instance.studyPace,
      'study_style': instance.studyStyle,
      'break_preference': instance.breakPreference,
      'assessed_at': instance.assessedAt,
      'assessment_method': instance.assessmentMethod,
    };
