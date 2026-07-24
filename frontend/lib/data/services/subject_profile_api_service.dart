import 'package:dio/dio.dart';
import '../models/subject_profile_model.dart';
import '../../core/network/dio_client.dart';
import '../../core/config/app_config.dart';

class SubjectProfileApiService {
  final DioClient _dioClient;

  SubjectProfileApiService(this._dioClient);

  /// Generate diagnostic quiz for a subject
  Future<DiagnosticQuizResponse> generateDiagnosticQuiz(String subject) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.subjectProfilesEndpoint}/diagnostic-quiz/generate',
        data: {'subject': subject},
      );
      return DiagnosticQuizResponse.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(
            e.response?.data['detail'] ?? 'Failed to generate quiz');
      }
      throw Exception('Network error: ${e.message}');
    }
  }

  /// Submit diagnostic quiz answers and get evaluated profile
  Future<SubjectProfileModel> evaluateDiagnosticQuiz({
    required String subject,
    required List<String> answers,
  }) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.subjectProfilesEndpoint}/diagnostic-quiz/evaluate',
        data: {
          'subject': subject,
          'answers': answers,
        },
      );
      return SubjectProfileModel.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(
            e.response?.data['detail'] ?? 'Failed to evaluate quiz');
      }
      throw Exception('Network error: ${e.message}');
    }
  }

  /// Create subject profile manually (skip quiz)
  Future<SubjectProfileModel> createSubjectProfileManually(
      SubjectProfileCreate profile) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.subjectProfilesEndpoint}/manual',
        data: profile.toJson(),
      );
      return SubjectProfileModel.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(
            e.response?.data['detail'] ?? 'Failed to create profile');
      }
      throw Exception('Network error: ${e.message}');
    }
  }

  /// Get all subject profiles for current user
  Future<List<SubjectProfileModel>> getAllSubjectProfiles() async {
    try {
      final response = await _dioClient.dio.get('${AppConfig.subjectProfilesEndpoint}/');
      final List<dynamic> data = response.data;
      return data.map((json) => SubjectProfileModel.fromJson(json)).toList();
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(
            e.response?.data['detail'] ?? 'Failed to fetch profiles');
      }
      throw Exception('Network error: ${e.message}');
    }
  }

  /// Update an existing subject profile
  Future<SubjectProfileModel> updateSubjectProfile({
    required String subject,
    String? level,
    String? studyPace,
    String? studyStyle,
    String? breakPreference,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (level != null) data['level'] = level;
      if (studyPace != null) data['study_pace'] = studyPace;
      if (studyStyle != null) data['study_style'] = studyStyle;
      if (breakPreference != null) data['break_preference'] = breakPreference;

      final response = await _dioClient.dio.put(
        '${AppConfig.subjectProfilesEndpoint}/$subject',
        data: data,
      );
      return SubjectProfileModel.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(
            e.response?.data['detail'] ?? 'Failed to update profile');
      }
      throw Exception('Network error: ${e.message}');
    }
  }

  /// Delete a subject profile
  Future<void> deleteSubjectProfile(String subject) async {
    try {
      await _dioClient.dio.delete('${AppConfig.subjectProfilesEndpoint}/$subject');
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(
            e.response?.data['detail'] ?? 'Failed to delete profile');
      }
      throw Exception('Network error: ${e.message}');
    }
  }
}
