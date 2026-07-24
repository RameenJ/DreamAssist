import 'package:dio/dio.dart';
import '../../core/network/dio_client.dart';
import '../../core/config/app_config.dart';
import '../../core/utils/result.dart';
import '../models/diagnostic_quiz_model.dart';

/// API service for diagnostic quiz endpoints
class DiagnosticApiService {
  final DioClient _dioClient;

  DiagnosticApiService(this._dioClient);

  /// Generate a diagnostic quiz for a subject
  Future<Result<DiagnosticQuizResponse>> generateQuiz(String subject) async {
    try {
      final request = DiagnosticQuizRequest(subject: subject);
      final response = await _dioClient.dio.post(
        '${AppConfig.diagnosticEndpoint}/generate-quiz',
        data: request.toJson(),
      );

      return Success(DiagnosticQuizResponse.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(
        e.response?.data['detail'] ?? e.message ?? 'Failed to generate quiz',
      );
    } catch (e) {
      return Failure('Unexpected error generating quiz: $e');
    }
  }

  /// Submit quiz answers and get evaluation
  Future<Result<DiagnosticQuizResult>> submitQuiz(
    DiagnosticQuizSubmission submission,
  ) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.diagnosticEndpoint}/submit-quiz',
        data: submission.toJson(),
      );

      return Success(DiagnosticQuizResult.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(
        e.response?.data['detail'] ?? e.message ?? 'Failed to submit quiz',
      );
    } catch (e) {
      return Failure('Unexpected error submitting quiz: $e');
    }
  }

  /// Set manual level for a subject
  Future<Result<Map<String, dynamic>>> setManualLevel(
    ManualLevelSetting setting,
  ) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.diagnosticEndpoint}/set-manual-level',
        data: setting.toJson(),
      );

      return Success(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      return Failure(
        e.response?.data['detail'] ?? e.message ?? 'Failed to set level',
      );
    } catch (e) {
      return Failure('Unexpected error setting level: $e');
    }
  }

  /// Get all subject profiles for current user
  Future<Result<List<SubjectProfile>>> getMyProfiles() async {
    try {
      final response = await _dioClient.dio.get(
        '${AppConfig.diagnosticEndpoint}/my-profiles',
      );

      final profiles = (response.data['subject_profiles'] as List)
          .map((json) => SubjectProfile.fromJson(json))
          .toList();

      return Success(profiles);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        await _dioClient.clearAuthToken();
        return const Failure(
          'Session expired. Please login again.',
          code: '401',
        );
      }
      return Failure(
        e.response?.data['detail'] ?? e.message ?? 'Failed to get profiles',
      );
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }
}
