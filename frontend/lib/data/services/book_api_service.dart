import 'package:dio/dio.dart';
import '../../core/network/dio_client.dart';
import '../../core/config/app_config.dart';
import '../../core/utils/result.dart';
import '../models/book_model.dart';

/// API service for book-related endpoints
class BookApiService {
  final DioClient _dioClient;

  BookApiService(this._dioClient);

  /// Upload a new book
  Future<Result<BookModel>> uploadBook({
    required String filePath,
    String? title,
    String? categoryId,
    String? subject,
    Function(int, int)? onProgress,
  }) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(filePath),
        if (title != null) 'title': title,
        if (categoryId != null) 'category_id': categoryId,
        if (subject != null) 'subject': subject,
      });

      final response = await _dioClient.dio.post(
        '${AppConfig.booksEndpoint}/upload',
        data: formData,
        onSendProgress: onProgress,
      );

      return Success(BookModel.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to upload book');
    } catch (e) {
      return Failure('Unexpected error during upload: $e');
    }
  }

  /// Get all books for current user
  Future<Result<List<BookModel>>> getUserBooks() async {
    try {
      final response = await _dioClient.dio.get(AppConfig.booksEndpoint);
      
      final List<dynamic> data = response.data as List;
      final books = data.map((json) => BookModel.fromJson(json)).toList();
      
      return Success(books);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch books');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Get a specific book by ID
  Future<Result<BookModel>> getBookById(String bookId) async {
    try {
      final response = await _dioClient.dio.get('${AppConfig.booksEndpoint}/$bookId');
      return Success(BookModel.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch book');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Update book category
  Future<Result<BookModel>> updateBookCategory(
    String bookId,
    String? categoryId,
  ) async {
    try {
      final response = await _dioClient.dio.put(
        '${AppConfig.booksEndpoint}/$bookId/category',
        data: BookCategoryUpdateRequest(categoryId: categoryId).toJson(),
      );
      return Success(BookModel.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to update book category');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Get extracted text from a book
  Future<Result<BookTextContentResponse>> getBookExtractedText(String bookId) async {
    try {
      final response = await _dioClient.dio.get(
        '${AppConfig.booksEndpoint}/$bookId/extracted-text',
      );
      return Success(BookTextContentResponse.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch extracted text');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Get book PDF URL
  String getBookPdfUrl(String bookId) {
    return '${AppConfig.apiBaseUrl}${AppConfig.booksEndpoint}/$bookId/pdf';
  }

  /// Get book topics (table of contents)
  Future<Result<List<BookTopicModel>>> getBookTopics(String bookId) async {
    try {
      final response = await _dioClient.dio.get(
        '${AppConfig.booksEndpoint}/$bookId/topics',
      );
      
      final List<dynamic> data = response.data as List;
      final topics = data.map((json) => BookTopicModel.fromJson(json)).toList();
      
      return Success(topics);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch book topics');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Get topic text content for summarization/flashcards
  Future<Result<String>> getTopicText(String bookId, String topicId) async {
    try {
      final response = await _dioClient.dio.get(
        '${AppConfig.booksEndpoint}/$bookId/topics/$topicId/text',
      );
      
      final String content = response.data['content'] as String;
      return Success(content);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch topic text');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Delete a book
  Future<Result<void>> deleteBook(String bookId) async {
    try {
      await _dioClient.dio.delete('${AppConfig.booksEndpoint}/$bookId');
      return const Success(null);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to delete book');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }
}
