import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/signup_screen.dart';
import '../screens/home/home_screen.dart';
import '../screens/books/books_screen.dart';
import '../screens/books/book_detail_screen.dart';
import '../screens/books/pdf_viewer_screen.dart';
import '../screens/subjects/subjects_screen.dart';
import '../screens/profile/profile_screen.dart';
import '../screens/ai/ai_chat_screen.dart';
import '../screens/ai/summarization_screen.dart';
import '../screens/ai/flashcards_screen.dart';
import '../screens/ai/quiz_screen.dart';
import '../screens/ai/quiz_taking_screen.dart';
import '../screens/ai/quiz_results_screen.dart';
import '../screens/progress/progress_screen.dart';
import '../screens/preferences/preferences_screen.dart';
import '../screens/preferences/diagnostic_quiz_screen.dart';
import '../screens/study_planner/study_planner_list_screen.dart';
import '../screens/study_planner/study_planner_create_screen.dart';
import '../screens/study_planner/calendar_screen.dart';
import '../screens/study_planner/analytics_dashboard_screen.dart';
import '../screens/study_planner/daily_aggregated_schedule_screen.dart';
import '../screens/study_planner/weekly_schedule_screen.dart';
import '../screens/mood/mood_log_screen.dart';
import '../screens/persona/persona_chat_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/splash',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isLoading = authState.isLoading;
      
      final isAuthRoute = state.matchedLocation == '/login' ||
          state.matchedLocation == '/signup';
      final isSplash = state.matchedLocation == '/splash';

      // Still loading auth status - show splash screen
      if (isLoading && !isSplash) return '/splash';

      // Done loading and on splash - redirect based on auth state
      if (!isLoading && isSplash) {
        return isAuthenticated ? '/home' : '/login';
      }

      // Not authenticated and not on auth route -> redirect to login
      if (!isAuthenticated && !isAuthRoute && !isSplash) {
        return '/login';
      }

      // Authenticated and on auth route -> redirect to home
      if (isAuthenticated && isAuthRoute) {
        return '/home';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const Scaffold(
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Loading...', style: TextStyle(fontSize: 18)),
              ],
            ),
          ),
        ),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/signup',
        builder: (context, state) => const SignupScreen(),
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/books',
        builder: (context, state) => const BooksScreen(),
      ),
      GoRoute(
        path: '/books/:id',
        builder: (context, state) {
          final bookId = state.pathParameters['id']!;
          return BookDetailScreen(bookId: bookId);
        },
      ),
      GoRoute(
        path: '/books/:id/pdf',
        builder: (context, state) {
          final bookId = state.pathParameters['id']!;
          final bookTitle = state.uri.queryParameters['title'] ?? 'PDF Viewer';
          return PdfViewerScreen(bookId: bookId, bookTitle: bookTitle);
        },
      ),
      GoRoute(
        path: '/subjects',
        builder: (context, state) => const SubjectsScreen(),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) => const ProfileScreen(),
      ),
      // Preferences and diagnostic quiz
      GoRoute(
        path: '/preferences',
        builder: (context, state) {
          final isInitialSetup = state.uri.queryParameters['initial'] == 'true';
          return PreferencesScreen(isInitialSetup: isInitialSetup);
        },
      ),
      GoRoute(
        path: '/diagnostic-quiz/:subject',
        builder: (context, state) {
          final subject = state.pathParameters['subject']!;
          return DiagnosticQuizScreen(subject: subject);
        },
      ),
      // AI Features
      GoRoute(
        path: '/ai/chat/:bookId',
        builder: (context, state) {
          final bookId = state.pathParameters['bookId']!;
          return AiChatScreen(bookId: bookId);
        },
      ),
      GoRoute(
        path: '/ai/summarize',
        builder: (context, state) => const SummarizationScreen(),
      ),
      GoRoute(
        path: '/ai/summarize/:bookId',
        builder: (context, state) {
          final bookId = state.pathParameters['bookId'];
          return SummarizationScreen(bookId: bookId);
        },
      ),
      GoRoute(
        path: '/ai/flashcards',
        builder: (context, state) => const FlashcardsScreen(),
      ),
      // Quiz routes - IMPORTANT: Specific routes MUST come before parameterized routes
      GoRoute(
        path: '/quiz/results',
        builder: (context, state) => const QuizResultsScreen(),
      ),
      GoRoute(
        path: '/quiz/:bookId/take',
        builder: (context, state) {
          final bookId = state.pathParameters['bookId']!;
          return QuizTakingScreen(bookId: bookId);
        },
      ),
      GoRoute(
        path: '/quiz/:bookId',
        builder: (context, state) {
          final bookId = state.pathParameters['bookId']!;
          return QuizScreen(bookId: bookId);
        },
      ),
      // Study Planner - IMPORTANT: Specific routes MUST come before parameterized routes
      GoRoute(
        path: '/study-planner',
        builder: (context, state) => const StudyPlannerListScreen(),
      ),
      GoRoute(
        path: '/study-planner/create',
        builder: (context, state) => const StudyPlannerCreateScreen(),
      ),
      GoRoute(
        path: '/study-planner/:planId/calendar',
        builder: (context, state) {
          final planId = state.pathParameters['planId']!;
          return StudyPlannerCalendarScreen(planId: planId);
        },
      ),
      GoRoute(
        path: '/study-planner/:planId/analytics',
        builder: (context, state) {
          final planId = state.pathParameters['planId']!;
          return AnalyticsDashboardScreen(planId: planId);
        },
      ),
      GoRoute(
        path: '/daily-schedule',
        builder: (context, state) => const DailyAggregatedScheduleScreen(),
      ),
      GoRoute(
        path: '/weekly-schedule',
        builder: (context, state) => const WeeklyScheduleScreen(),
      ),
      // Progress
      GoRoute(
        path: '/progress',
        builder: (context, state) => const ProgressScreen(),
      ),
      // Mood Logger
      GoRoute(
        path: '/mood-log',
        builder: (context, state) => const MoodLogScreen(),
      ),
      // AI Personas Chat
      GoRoute(
        path: '/persona-chat',
        builder: (context, state) => const PersonaChatScreen(),
      ),
    ],
  );
});
