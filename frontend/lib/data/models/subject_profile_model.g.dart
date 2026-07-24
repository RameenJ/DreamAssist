// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'subject_profile_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SubjectProfileModel _$SubjectProfileModelFromJson(Map<String, dynamic> json) =>
    SubjectProfileModel(
      subject: json['subject'] as String,
      level: json['level'] as String,
      studyPace: json['study_pace'] as String,
      studyStyle: json['study_style'] as String,
      breakPreference: json['break_preference'] as String,
      assessedAt: json['assessed_at'] as String,
      assessmentMethod: json['assessment_method'] as String,
      weakTopics: (json['weak_topics'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$SubjectProfileModelToJson(
  SubjectProfileModel instance,
) => <String, dynamic>{
  'subject': instance.subject,
  'level': instance.level,
  'study_pace': instance.studyPace,
  'study_style': instance.studyStyle,
  'break_preference': instance.breakPreference,
  'assessed_at': instance.assessedAt,
  'assessment_method': instance.assessmentMethod,
  'weak_topics': instance.weakTopics,
};

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

SubjectProfileCreate _$SubjectProfileCreateFromJson(
  Map<String, dynamic> json,
) => SubjectProfileCreate(
  subject: json['subject'] as String,
  level: json['level'] as String,
  studyPace: json['study_pace'] as String,
  studyStyle: json['study_style'] as String,
  breakPreference: json['break_preference'] as String,
);

Map<String, dynamic> _$SubjectProfileCreateToJson(
  SubjectProfileCreate instance,
) => <String, dynamic>{
  'subject': instance.subject,
  'level': instance.level,
  'study_pace': instance.studyPace,
  'study_style': instance.studyStyle,
  'break_preference': instance.breakPreference,
};
