// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'book_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BookModel _$BookModelFromJson(Map<String, dynamic> json) => BookModel(
  id: json['id'] as String,
  title: json['title'] as String,
  filename: json['filename'] as String?,
  uploadDate: json['upload_date'] as String,
  categoryId: json['category_id'] as String?,
  status: json['status'] as String,
);

Map<String, dynamic> _$BookModelToJson(BookModel instance) => <String, dynamic>{
  'id': instance.id,
  'title': instance.title,
  'filename': instance.filename,
  'upload_date': instance.uploadDate,
  'category_id': instance.categoryId,
  'status': instance.status,
};

BookCategoryUpdateRequest _$BookCategoryUpdateRequestFromJson(
  Map<String, dynamic> json,
) => BookCategoryUpdateRequest(categoryId: json['category_id'] as String?);

Map<String, dynamic> _$BookCategoryUpdateRequestToJson(
  BookCategoryUpdateRequest instance,
) => <String, dynamic>{'category_id': instance.categoryId};

BookTextContentResponse _$BookTextContentResponseFromJson(
  Map<String, dynamic> json,
) => BookTextContentResponse(
  id: json['id'] as String,
  title: json['title'] as String,
  content: json['content'] as String,
);

Map<String, dynamic> _$BookTextContentResponseToJson(
  BookTextContentResponse instance,
) => <String, dynamic>{
  'id': instance.id,
  'title': instance.title,
  'content': instance.content,
};

BookTopicModel _$BookTopicModelFromJson(Map<String, dynamic> json) =>
    BookTopicModel(
      id: json['id'] as String,
      bookId: json['book_id'] as String,
      topicTitle: json['topic_title'] as String,
      pageStart: (json['page_start'] as num).toInt(),
    );

Map<String, dynamic> _$BookTopicModelToJson(BookTopicModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'book_id': instance.bookId,
      'topic_title': instance.topicTitle,
      'page_start': instance.pageStart,
    };
