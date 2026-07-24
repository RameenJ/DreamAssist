import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Application configuration loaded from environment variables
class AppConfig {
  static String get apiBaseUrl => dotenv.env['API_BASE_URL'] ?? 'http://localhost:8000';
  static String get wsBaseUrl => dotenv.env['WS_BASE_URL'] ?? 'ws://localhost:8000';
  static String get appName => dotenv.env['APP_NAME'] ?? 'DreamAssist';
  
  // API endpoints
  static String get authEndpoint => '/auth';
  static String get booksEndpoint => '/books';
  static String get categoriesEndpoint => '/categories';
  static String get subjectsEndpoint => '/subjects';
  static String get aiEndpoint => '/ai';
  static String get progressEndpoint => '/progress';
  static String get forumEndpoint => '/forum';
  static String get groupsEndpoint => '/groups';
  static String get chatEndpoint => '/chat';
  static String get usersEndpoint => '/users';
  static String get diagnosticEndpoint => '/diagnostic';
  static String get subjectProfilesEndpoint => '/subject-profiles';
  
  // Token config
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  
  // Timeouts (increased for heavy AI processing)
  static const Duration connectionTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(minutes: 3);
}
