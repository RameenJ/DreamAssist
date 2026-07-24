import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';

part 'book_model.g.dart';

@JsonSerializable()
class BookModel extends Equatable {
  final String id;
  final String title;
  final String? filename;
  @JsonKey(name: 'upload_date')
  final String uploadDate;
  @JsonKey(name: 'category_id')
  final String? categoryId;
  final String status; // processing, completed, error

  const BookModel({
    required this.id,
    required this.title,
    this.filename,
    required this.uploadDate,
    this.categoryId,
    required this.status,
  });

  bool get isProcessing => status == 'processing';
  bool get isCompleted => status == 'completed';
  bool get hasError => status == 'error';

  factory BookModel.fromJson(Map<String, dynamic> json) =>
      _$BookModelFromJson(json);

  Map<String, dynamic> toJson() => _$BookModelToJson(this);

  @override
  List<Object?> get props => [
        id,
        title,
        filename,
        uploadDate,
        categoryId,
        status,
      ];
}

@JsonSerializable()
class BookCategoryUpdateRequest extends Equatable {
  @JsonKey(name: 'category_id')
  final String? categoryId;

  const BookCategoryUpdateRequest({this.categoryId});

  factory BookCategoryUpdateRequest.fromJson(Map<String, dynamic> json) =>
      _$BookCategoryUpdateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$BookCategoryUpdateRequestToJson(this);

  @override
  List<Object?> get props => [categoryId];
}

@JsonSerializable()
class BookTextContentResponse extends Equatable {
  final String id;
  final String title;
  final String content;

  const BookTextContentResponse({
    required this.id,
    required this.title,
    required this.content,
  });

  factory BookTextContentResponse.fromJson(Map<String, dynamic> json) =>
      _$BookTextContentResponseFromJson(json);

  Map<String, dynamic> toJson() => _$BookTextContentResponseToJson(this);

  @override
  List<Object?> get props => [id, title, content];
}

@JsonSerializable()
class BookTopicModel extends Equatable {
  final String id;
  @JsonKey(name: 'book_id')
  final String bookId;
  @JsonKey(name: 'topic_title')
  final String topicTitle;
  @JsonKey(name: 'page_start')
  final int pageStart;

  const BookTopicModel({
    required this.id,
    required this.bookId,
    required this.topicTitle,
    required this.pageStart,
  });

  factory BookTopicModel.fromJson(Map<String, dynamic> json) =>
      _$BookTopicModelFromJson(json);

  Map<String, dynamic> toJson() => _$BookTopicModelToJson(this);

  @override
  List<Object?> get props => [id, bookId, topicTitle, pageStart];
}
