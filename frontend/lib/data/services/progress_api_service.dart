import 'package:dio/dio.dart';
import '../models/progress_model.dart';
import '../../core/network/dio_client.dart';

class ProgressApiService {
  final DioClient _dioClient;

  ProgressApiService(this._dioClient);

  /// Get global progress for the current user
  Future<GlobalProgressResponse> getGlobalProgress() async {
    try {
      final response = await _dioClient.dio.get('/progress/global');
      return GlobalProgressResponse.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(
            e.response?.data['detail'] ?? 'Failed to fetch progress');
      }
      throw Exception('Network error: ${e.message}');
    }
  }

  /// Get progress for a specific book
  Future<BookProgressResponse> getBookProgress(String bookId) async {
    try {
      final response = await _dioClient.dio.get('/progress/book/$bookId');
      return BookProgressResponse.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(
            e.response?.data['detail'] ?? 'Failed to fetch book progress');
      }
      throw Exception('Network error: ${e.message}');
    }
  }
}
