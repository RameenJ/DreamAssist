import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';
import 'subject_profile_model.dart';

part 'user_model.g.dart';

@JsonSerializable()
class UserModel extends Equatable {
  final String id;
  final String firstname;
  final String lastname;
  final String email;
  final int? age;
  @JsonKey(name: 'university_name')
  final String? universityName;
  final String? image;
  final bool verified;
  @JsonKey(name: 'subject_profiles')
  final List<SubjectProfileModel>? subjectProfiles;

  const UserModel({
    required this.id,
    required this.firstname,
    required this.lastname,
    required this.email,
    this.age,
    this.universityName,
    this.subjectProfiles,
    this.image,
    this.verified = false,
  });

  String get fullName => '$firstname $lastname';

  factory UserModel.fromJson(Map<String, dynamic> json) =>
      _$UserModelFromJson(json);

  Map<String, dynamic> toJson() => _$UserModelToJson(this);

  @override
  List<Object?> get props => [
        id,
        firstname,
        lastname,
        email,
        age,
        universityName,
        image,
        subjectProfiles,
        verified,
      ];
}

@JsonSerializable()
class UserCreateRequest extends Equatable {
  final String email;
  final String password;
  final String firstname;
  final String lastname;
  final int age;
  @JsonKey(name: 'university_name')
  final String universityName;

  const UserCreateRequest({
    required this.email,
    required this.password,
    required this.firstname,
    required this.lastname,
    required this.age,
    required this.universityName,
  });

  factory UserCreateRequest.fromJson(Map<String, dynamic> json) =>
      _$UserCreateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$UserCreateRequestToJson(this);

  @override
  List<Object?> get props => [
        email,
        password,
        firstname,
        lastname,
        age,
        universityName,
      ];
}

@JsonSerializable()
class UserLoginRequest extends Equatable {
  final String email;
  final String password;

  const UserLoginRequest({
    required this.email,
    required this.password,
  });

  factory UserLoginRequest.fromJson(Map<String, dynamic> json) =>
      _$UserLoginRequestFromJson(json);

  Map<String, dynamic> toJson() => _$UserLoginRequestToJson(this);

  @override
  List<Object?> get props => [email, password];
}

@JsonSerializable()
class TokenResponse extends Equatable {
  @JsonKey(name: 'access_token')
  final String accessToken;
  @JsonKey(name: 'token_type')
  final String tokenType;

  const TokenResponse({
    required this.accessToken,
    required this.tokenType,
  });

  factory TokenResponse.fromJson(Map<String, dynamic> json) =>
      _$TokenResponseFromJson(json);

  Map<String, dynamic> toJson() => _$TokenResponseToJson(this);

  @override
  List<Object?> get props => [accessToken, tokenType];
}

@JsonSerializable()
class UserUpdateRequest extends Equatable {
  final String? firstname;
  final String? lastname;
  final int? age;
  @JsonKey(name: 'university_name')
  final String? universityName;
  final String? image;

  const UserUpdateRequest({
    this.firstname,
    this.lastname,
    this.age,
    this.universityName,
    this.image,
  });

  factory UserUpdateRequest.fromJson(Map<String, dynamic> json) =>
      _$UserUpdateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$UserUpdateRequestToJson(this);

  @override
  List<Object?> get props => [firstname, lastname, age, universityName, image];
}
