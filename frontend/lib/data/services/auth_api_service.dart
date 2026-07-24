import 'package:dio/dio.dart';
import '../../core/network/dio_client.dart';
import '../../core/config/app_config.dart';
import '../../core/utils/result.dart';
import '../models/user_model.dart';

/// API service for authentication endpoints
class AuthApiService {
  final DioClient _dioClient;

  AuthApiService(this._dioClient);

  /// Sign up a new user
  Future<Result<UserModel>> signUp(UserCreateRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.authEndpoint}/signup',
        data: request.toJson(),
      );

      return Success(UserModel.fromJson(response.data));
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to sign up');
    } catch (e) {
      return Failure('Unexpected error during sign up: $e');
    }
  }

  /// Login user and get access token
  Future<Result<TokenResponse>> login(UserLoginRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        '${AppConfig.authEndpoint}/login',
        data: request.toJson(),
      );

      final token = TokenResponse.fromJson(response.data);
      
      // Save token for future requests
      await _dioClient.setAuthToken(token.accessToken);
      
      return Success(token);
    } on DioException catch (e) {
      return Failure(e.message ?? 'Failed to login');
    } catch (e) {
      return Failure('Unexpected error during login: $e');
    }
  }

  /// Logout user
  Future<void> logout() async {
    await _dioClient.clearAuthToken();
  }

  /// Get current user profile
  Future<Result<UserModel>> getCurrentUser() async {
    try {
      final response = await _dioClient.dio.get('${AppConfig.usersEndpoint}/me');
      return Success(UserModel.fromJson(response.data));
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        await _dioClient.clearAuthToken();
        return const Failure('Session expired. Please login again.', code: '401');
      }
      return Failure(e.message ?? 'Failed to get user profile');
    } catch (e) {
      return Failure('Unexpected error: $e');
    }
  }

  /// Check if user is logged in
  Future<bool> isLoggedIn() async {
    final token = await _dioClient.getAuthToken();
    return token != null && token.isNotEmpty;
  }
}
