import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'category_model.g.dart';

@JsonSerializable()
class CategoryModel extends Equatable {
  final String id;
  final String name;
  @JsonKey(name: 'user_id')
  final String userId;
  @JsonKey(name: 'created_at')
  final String createdAt;

  const CategoryModel({
    required this.id,
    required this.name,
    required this.userId,
    required this.createdAt,
  });

  factory CategoryModel.fromJson(Map<String, dynamic> json) =>
      _$CategoryModelFromJson(json);

  Map<String, dynamic> toJson() => _$CategoryModelToJson(this);

  @override
  List<Object?> get props => [id, name, userId, createdAt];
}

@JsonSerializable()
class CategoryCreateRequest extends Equatable {
  final String name;

  const CategoryCreateRequest({required this.name});

  factory CategoryCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$CategoryCreateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$CategoryCreateRequestToJson(this);

  @override
  List<Object?> get props => [name];
}

@JsonSerializable()
class CategoryUpdateRequest extends Equatable {
  final String name;

  const CategoryUpdateRequest({required this.name});

  factory CategoryUpdateRequest.fromJson(Map<String, dynamic> json) =>
      _$CategoryUpdateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$CategoryUpdateRequestToJson(this);

  @override
  List<Object?> get props => [name];
}
