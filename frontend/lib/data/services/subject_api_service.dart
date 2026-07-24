import 'package:dio/dio.dart';
import '../../core/network/dio_client.dart';
import '../../core/config/app_config.dart';
import '../../core/utils/result.dart';
import '../models/subject_model.dart';

/// API service for subject-related endpoints
class SubjectApiService {
  final DioClient _dioClient;

  SubjectApiService(this._dioClient);

  /// Get all subjects for current user
  Future<Result<List<SubjectModel>>> getSubjects() async {
    try {
      final response = await _dioClient.dio.get(AppConfig.subjectsEndpoint);
      
      final List<dynamic> data = response.data as List;
      final subjects = data.map((json) => SubjectModel.fromJson(json)).toList();
      
      return Success(subjects);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to fetch subjects');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Create a new subject
  Future<Result<SubjectModel>> createSubject(SubjectCreateRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        AppConfig.subjectsEndpoint,
        data: request.toJson(),
      );
      return Success(SubjectModel.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to create subject');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Update a subject
  Future<Result<SubjectModel>> updateSubject(
    String subjectId,
    SubjectUpdateRequest request,
  ) async {
    try {
      final response = await _dioClient.dio.put(
        '${AppConfig.subjectsEndpoint}/$subjectId',
        data: request.toJson(),
      );
      return Success(SubjectModel.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to update subject');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Delete a subject
  Future<Result<void>> deleteSubject(String subjectId) async {
    try {
      await _dioClient.dio.delete('${AppConfig.subjectsEndpoint}/$subjectId');
      return const Success(null);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to delete subject');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }
}
