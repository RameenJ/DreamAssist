/// Base exception class for app-specific errors
class AppException implements Exception {
  final String message;
  final String? code;
  final dynamic details;

  AppException(this.message, {this.code, this.details});

  @override
  String toString() => message;
}

/// Network-related exceptions
class NetworkException extends AppException {
  NetworkException(super.message, {super.code, super.details});
}

/// Authentication exceptions
class AuthException extends AppException {
  AuthException(super.message, {super.code, super.details});
}

/// Unauthorized access exception
class UnauthorizedException extends AppException {
  UnauthorizedException([super.message = 'Unauthorized access'])
      : super(code: '401');
}

/// Server error exception
class ServerException extends AppException {
  ServerException(super.message, {super.code, super.details});
}

/// Validation exception
class ValidationException extends AppException {
  ValidationException(super.message, {super.code, super.details});
}

/// Resource not found exception
class NotFoundException extends AppException {
  NotFoundException([super.message = 'Resource not found'])
      : super(code: '404');
}
