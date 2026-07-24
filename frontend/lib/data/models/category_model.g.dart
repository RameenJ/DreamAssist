// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'category_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CategoryModel _$CategoryModelFromJson(Map<String, dynamic> json) =>
    CategoryModel(
      id: json['id'] as String,
      name: json['name'] as String,
      userId: json['user_id'] as String,
      createdAt: json['created_at'] as String,
    );

Map<String, dynamic> _$CategoryModelToJson(CategoryModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'user_id': instance.userId,
      'created_at': instance.createdAt,
    };

CategoryCreateRequest _$CategoryCreateRequestFromJson(
  Map<String, dynamic> json,
) => CategoryCreateRequest(name: json['name'] as String);

Map<String, dynamic> _$CategoryCreateRequestToJson(
  CategoryCreateRequest instance,
) => <String, dynamic>{'name': instance.name};

CategoryUpdateRequest _$CategoryUpdateRequestFromJson(
  Map<String, dynamic> json,
) => CategoryUpdateRequest(name: json['name'] as String);

Map<String, dynamic> _$CategoryUpdateRequestToJson(
  CategoryUpdateRequest instance,
) => <String, dynamic>{'name': instance.name};
