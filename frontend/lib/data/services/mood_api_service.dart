import 'package:dio/dio.dart';
import '../../core/network/dio_client.dart';
import '../../core/config/app_config.dart';
import '../../core/utils/result.dart';
import '../models/mood_log_model.dart';

/// API service for mood logging endpoints
class MoodApiService {
  final DioClient _dioClient;

  MoodApiService(this._dioClient);

  /// Log user's daily mood
  Future<Result<MoodLogResponse>> logMood(String mood) async {
    try {
      final request = MoodLogCreateRequest(mood: mood);
      final response = await _dioClient.dio.post(
        '${AppConfig.usersEndpoint}/me/mood-log',
        data: request.toJson(),
      );

      return Success(MoodLogResponse.fromJson(response.data));
    } on DioException catch (e) {
      String errorMessage = 'Failed to log mood';
      if (e.response?.data != null && e.response!.data['detail'] != null) {
        errorMessage = e.response!.data['detail'];
      } else if (e.message != null) {
        errorMessage = e.message!;
      }
      return Failure(errorMessage);
    } catch (e) {
      return Failure('Unexpected error logging mood: $e');
    }
  }

  /// Check if user has logged mood today
  Future<Result<TodayMoodResponse>> checkTodayMood() async {
    try {
      final response = await _dioClient.dio.get(
        '${AppConfig.usersEndpoint}/me/mood-log/today',
      );

      return Success(TodayMoodResponse.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to check mood status');
    } catch (e) {
      return Failure('Unexpected error checking mood: $e');
    }
  }

  /// Fetch mood history for the last N days
  Future<Result<MoodHistoryResponse>> getMoodHistory({int days = 7}) async {
    try {
      final response = await _dioClient.dio.get(
        '${AppConfig.usersEndpoint}/me/mood-log/history',
        queryParameters: {'days': days},
      );

      return Success(MoodHistoryResponse.fromJson(response.data));
    } on DioException catch (e) {
      String errorMessage = 'Failed to fetch mood history';
      if (e.response?.data != null && e.response!.data['detail'] != null) {
        errorMessage = e.response!.data['detail'];
      }
      return Failure(errorMessage);
    } catch (e) {
      return Failure('Unexpected error fetching mood history: $e');
    }
  }
}
