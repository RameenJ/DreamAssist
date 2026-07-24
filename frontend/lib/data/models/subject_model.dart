import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'subject_model.g.dart';

@JsonSerializable()
class SubjectModel extends Equatable {
  final String id;
  final String name;
  @JsonKey(name: 'user_id')
  final String userId;
  @JsonKey(name: 'created_at')
  final String createdAt;

  const SubjectModel({
    required this.id,
    required this.name,
    required this.userId,
    required this.createdAt,
  });

  factory SubjectModel.fromJson(Map<String, dynamic> json) =>
      _$SubjectModelFromJson(json);

  Map<String, dynamic> toJson() => _$SubjectModelToJson(this);

  @override
  List<Object?> get props => [id, name, userId, createdAt];
}

@JsonSerializable()
class SubjectCreateRequest extends Equatable {
  final String name;

  const SubjectCreateRequest({required this.name});

  factory SubjectCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$SubjectCreateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$SubjectCreateRequestToJson(this);

  @override
  List<Object?> get props => [name];
}

@JsonSerializable()
class SubjectUpdateRequest extends Equatable {
  final String name;

  const SubjectUpdateRequest({required this.name});

  factory SubjectUpdateRequest.fromJson(Map<String, dynamic> json) =>
      _$SubjectUpdateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$SubjectUpdateRequestToJson(this);

  @override
  List<Object?> get props => [name];
}
