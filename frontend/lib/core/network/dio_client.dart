import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:logger/logger.dart';
import '../config/app_config.dart';

/// Dio client with interceptors for authentication and error handling
class DioClient {
  late final Dio _dio;
  final FlutterSecureStorage _storage;
  final Logger _logger;

  DioClient({
    FlutterSecureStorage? storage,
    Logger? logger,
  })  : _storage = storage ?? const FlutterSecureStorage(),
        _logger = logger ?? Logger() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: AppConfig.connectionTimeout,
        receiveTimeout: AppConfig.receiveTimeout,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(_AuthInterceptor(_storage, _logger));
    _dio.interceptors.add(_LoggingInterceptor(_logger));
    _dio.interceptors.add(_ErrorInterceptor(_logger, _storage));
  }

  Dio get dio => _dio;

  Future<void> setAuthToken(String token) async {
    await _storage.write(key: AppConfig.accessTokenKey, value: token);
  }

  Future<void> clearAuthToken() async {
    await _storage.delete(key: AppConfig.accessTokenKey);
  }

  Future<String?> getAuthToken() async {
    return await _storage.read(key: AppConfig.accessTokenKey);
  }
}

/// Interceptor to add authentication token to requests
class _AuthInterceptor extends Interceptor {
  final FlutterSecureStorage _storage;
  final Logger _logger;

  _AuthInterceptor(this._storage, this._logger);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Skip auth for login/signup endpoints
    if (options.path.contains('/auth/login') ||
        options.path.contains('/auth/signup')) {
      return handler.next(options);
    }

    final token = await _storage.read(key: AppConfig.accessTokenKey);
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
      _logger.d('Added auth token to request: ${options.path}');
    }

    return handler.next(options);
  }
}

/// Interceptor for logging requests and responses
class _LoggingInterceptor extends Interceptor {
  final Logger _logger;

  _LoggingInterceptor(this._logger);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    _logger.i('REQUEST[${options.method}] => ${options.path}');
    _logger.d('Headers: ${options.headers}');
    _logger.d('Data: ${options.data}');
    return handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    _logger.i(
      'RESPONSE[${response.statusCode}] => ${response.requestOptions.path}',
    );
    _logger.d('Data: ${response.data}');
    return handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _logger.e(
      'ERROR[${err.response?.statusCode}] => ${err.requestOptions.path}',
    );
    _logger.e('Error: ${err.message}');
    _logger.e('Response: ${err.response?.data}');
    return handler.next(err);
  }
}

/// Interceptor for handling errors
class _ErrorInterceptor extends Interceptor {
  final Logger _logger;
  final FlutterSecureStorage _storage;

  _ErrorInterceptor(this._logger, this._storage);

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    String errorMessage = 'An error occurred';

    switch (err.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        errorMessage = 'Connection timeout. Please check your internet connection.';
        break;
      case DioExceptionType.badResponse:
        // Handle 401 specially - clear token
        if (err.response?.statusCode == 401) {
          _logger.w('Received 401 Unauthorized - clearing stored token');
          await _storage.delete(key: AppConfig.accessTokenKey);
          errorMessage = 'Session expired. Please login again.';
        } else {
          errorMessage = _handleStatusCode(err.response?.statusCode, err.response?.data);
        }
        break;
      case DioExceptionType.cancel:
        errorMessage = 'Request was cancelled';
        break;
      case DioExceptionType.connectionError:
        errorMessage = 'No internet connection';
        break;
      default:
        errorMessage = err.message ?? 'Unknown error occurred';
    }

    _logger.e('Intercepted error: $errorMessage');
    
    // Modify the error with a user-friendly message
    return handler.next(
      DioException(
        requestOptions: err.requestOptions,
        response: err.response,
        type: err.type,
        error: errorMessage,
        message: errorMessage,
      ),
    );
  }

  String _handleStatusCode(int? statusCode, dynamic responseData) {
    switch (statusCode) {
      case 400:
        // Try to extract detail from FastAPI response
        if (responseData is Map && responseData.containsKey('detail')) {
          return responseData['detail'].toString();
        }
        return 'Bad request';
      case 401:
        return 'Unauthorized. Please login again.';
      case 403:
        return 'Access forbidden';
      case 404:
        return 'Resource not found';
      case 422:
        // Validation error from FastAPI
        if (responseData is Map && responseData.containsKey('detail')) {
          return _extractValidationErrors(responseData['detail']);
        }
        return 'Validation error';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return 'Error: $statusCode';
    }
  }

  String _extractValidationErrors(dynamic detail) {
    if (detail is List) {
      return detail
          .map((e) => '${e['loc']?.join(' > ')}: ${e['msg']}')
          .join('\n');
    }
    return detail.toString();
  }
}
