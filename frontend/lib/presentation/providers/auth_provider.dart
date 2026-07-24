import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../data/models/user_model.dart';
import '../../data/services/auth_api_service.dart';
import '../../core/providers/app_providers.dart';
import '../../core/utils/result.dart';
import 'subject_profile_provider.dart';
import 'book_provider.dart';
import 'ai_chat_provider.dart';
import 'mood_provider.dart';
import 'diagnostic_provider.dart';
import 'progress_provider.dart';

part 'auth_provider.g.dart';

/// Authentication state
class AuthState {
  final UserModel? user;
  final bool isLoading;
  final String? error;
  final bool isAuthenticated;

  const AuthState({
    this.user,
    this.isLoading = false,
    this.error,
    this.isAuthenticated = false,
  });

  AuthState copyWith({
    UserModel? user,
    bool? isLoading,
    String? error,
    bool? isAuthenticated,
  }) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
    );
  }
}

/// Authentication state notifier
@riverpod
class Auth extends _$Auth {
  @override
  AuthState build() {
    // Schedule auth check after build completes
    Future.microtask(() => _checkAuthStatus());
    return const AuthState();
  }

  AuthApiService get _authService => ref.watch(authApiServiceProvider);

  /// Check if user is already authenticated
  Future<void> _checkAuthStatus() async {
    try {
      state = state.copyWith(isLoading: true);
      
      final isLoggedIn = await _authService.isLoggedIn();
      if (isLoggedIn) {
        final result = await _authService.getCurrentUser();
        result.when(
          success: (user) {
            state = state.copyWith(
              user: user,
              isAuthenticated: true,
              isLoading: false,
            );
          },
          failure: (message) {
            state = state.copyWith(
              isAuthenticated: false,
              isLoading: false,
              error: message,
            );
          },
        );
      } else {
        state = state.copyWith(isLoading: false);
      }
    } catch (e) {
      // Ensure loading state is always cleared even on error
      print('❌ [AUTH] Error checking auth status: $e');
      state = state.copyWith(isLoading: false, isAuthenticated: false);
    }
  }

  /// Sign up a new user
  Future<bool> signUp(UserCreateRequest request) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _authService.signUp(request);
    return result.when(
      success: (user) {
        // After successful signup, log them in
        return login(UserLoginRequest(
          email: request.email,
          password: request.password,
        ));
      },
      failure: (message) {
        state = state.copyWith(
          isLoading: false,
          error: message,
        );
        return false;
      },
    );
  }

  /// Login user
  Future<bool> login(UserLoginRequest request) async {
    state = state.copyWith(isLoading: true, error: null);
    
    // Clear all user-specific state from any previous user
    _clearUserData();

    final result = await _authService.login(request);
    if (result is Failure) {
      state = state.copyWith(
        isLoading: false,
        error: result.errorOrNull,
      );
      return false;
    }

    // Fetch user profile after successful login
    final userResult = await _authService.getCurrentUser();
    if (userResult is Failure) {
      state = state.copyWith(
        isLoading: false,
        error: userResult.errorOrNull,
      );
      return false;
    }

    final user = (userResult as Success).data;
    state = state.copyWith(
      user: user,
      isAuthenticated: true,
      isLoading: false,
    );
    return true;
  }

  /// Logout user
  Future<void> logout() async {
    await _authService.logout();
    
    // Clear all user-specific state to prevent data leakage between users
    _clearUserData();
    
    state = const AuthState();
  }

  /// Clear all user-specific provider data
  void _clearUserData() {
    ref.invalidate(subjectProfileProvider);
    ref.invalidate(bookProvider);
    ref.invalidate(aiChatProvider);
    ref.invalidate(moodProvider);
    ref.invalidate(diagnosticProvider);
    ref.invalidate(progressProvider);
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(error: null);
  }
}
