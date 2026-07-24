// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'subject_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SubjectModel _$SubjectModelFromJson(Map<String, dynamic> json) => SubjectModel(
  id: json['id'] as String,
  name: json['name'] as String,
  userId: json['user_id'] as String,
  createdAt: json['created_at'] as String,
);

Map<String, dynamic> _$SubjectModelToJson(SubjectModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'user_id': instance.userId,
      'created_at': instance.createdAt,
    };

SubjectCreateRequest _$SubjectCreateRequestFromJson(
  Map<String, dynamic> json,
) => SubjectCreateRequest(name: json['name'] as String);

Map<String, dynamic> _$SubjectCreateRequestToJson(
  SubjectCreateRequest instance,
) => <String, dynamic>{'name': instance.name};

SubjectUpdateRequest _$SubjectUpdateRequestFromJson(
  Map<String, dynamic> json,
) => SubjectUpdateRequest(name: json['name'] as String);

Map<String, dynamic> _$SubjectUpdateRequestToJson(
  SubjectUpdateRequest instance,
) => <String, dynamic>{'name': instance.name};
