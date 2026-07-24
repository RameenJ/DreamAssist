import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/progress_model.dart';
import '../../data/services/progress_api_service.dart';
import '../../core/providers/app_providers.dart';

final progressApiServiceProvider = Provider<ProgressApiService>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return ProgressApiService(dioClient);
});

class ProgressState {
  final GlobalProgressResponse? progressData;
  final bool isLoading;
  final String? error;

  ProgressState({
    this.progressData,
    this.isLoading = false,
    this.error,
  });

  ProgressState copyWith({
    GlobalProgressResponse? progressData,
    bool? isLoading,
    String? error,
  }) {
    return ProgressState(
      progressData: progressData ?? this.progressData,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class ProgressNotifier extends Notifier<ProgressState> {
  late final ProgressApiService _apiService;

  @override
  ProgressState build() {
    _apiService = ref.read(progressApiServiceProvider);
    return ProgressState();
  }

  Future<void> loadProgress() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final progress = await _apiService.getGlobalProgress();
      state = state.copyWith(progressData: progress, isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<BookProgressResponse?> getBookProgress(String bookId) async {
    try {
      return await _apiService.getBookProgress(bookId);
    } catch (e) {
      print('Error fetching book progress: $e');
      return null;
    }
  }

  void clearError() {
    state = state.copyWith(error: null);
  }
}

final progressProvider =
    NotifierProvider<ProgressNotifier, ProgressState>(() {
  return ProgressNotifier();
});
