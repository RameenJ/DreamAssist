import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:logger/logger.dart';
import '../network/dio_client.dart';
import '../../data/services/auth_api_service.dart';
import '../../data/services/book_api_service.dart';
import '../../data/services/category_api_service.dart';
import '../../data/services/subject_api_service.dart';
import '../../data/services/ai_api_service.dart';
import '../../data/services/diagnostic_api_service.dart';
import '../../data/services/mood_api_service.dart';

// Core dependencies
final secureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

final loggerProvider = Provider<Logger>((ref) {
  return Logger(
    printer: PrettyPrinter(
      methodCount: 0,
      errorMethodCount: 5,
      lineLength: 50,
      colors: true,
      printEmojis: true,
    ),
  );
});

// Network client
final dioClientProvider = Provider<DioClient>((ref) {
  return DioClient(
    storage: ref.watch(secureStorageProvider),
    logger: ref.watch(loggerProvider),
  );
});

// API Services
final authApiServiceProvider = Provider<AuthApiService>((ref) {
  return AuthApiService(ref.watch(dioClientProvider));
});

final bookApiServiceProvider = Provider<BookApiService>((ref) {
  return BookApiService(ref.watch(dioClientProvider));
});

final categoryApiServiceProvider = Provider<CategoryApiService>((ref) {
  return CategoryApiService(ref.watch(dioClientProvider));
});

final subjectApiServiceProvider = Provider<SubjectApiService>((ref) {
  return SubjectApiService(ref.watch(dioClientProvider));
});

final aiApiServiceProvider = Provider<AiApiService>((ref) {
  return AiApiService(ref.watch(dioClientProvider));
});

final diagnosticApiServiceProvider = Provider<DiagnosticApiService>((ref) {
  return DiagnosticApiService(ref.watch(dioClientProvider));
});

final moodApiServiceProvider = Provider<MoodApiService>((ref) {
  return MoodApiService(ref.watch(dioClientProvider));
});
