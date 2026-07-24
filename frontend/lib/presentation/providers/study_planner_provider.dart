import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../core/api/api_client.dart';
import '../../core/api/endpoints.dart';
import '../../core/api/api_models.dart';
import '../../core/network/dio_client.dart';

// Exceptions
class StudyPlanException implements Exception {
  final String message;
  StudyPlanException(this.message);

  @override
  String toString() => message;
}

// Study Planner Service
class StudyPlannerService {
  final Dio dio;
  final ApiClient apiClient;

  StudyPlannerService({
    required this.dio,
    required this.apiClient,
  });

  Future<StudyPlan> generatePlan({
    required List<String> subjects,
    required DateTime deadline,
    required String mode,
    required int totalStudyHoursPerWeek,
  }) async {
    try {
      final response = await apiClient.post(
        ApiEndpoints.generatePlan,
        data: {
          'subjects': subjects,
          'deadline': deadline.toIso8601String().split('T')[0],
          'mode': mode,
          'total_study_hours_per_week': totalStudyHoursPerWeek,
        },
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return StudyPlan.fromJson(response.data as Map<String, dynamic>);
      } else {
        throw StudyPlanException('Failed to generate plan');
      }
    } catch (e) {
      throw StudyPlanException('Error generating plan: $e');
    }
  }

  Future<StudyPlan?> getPlan(String planId) async {
    try {
      final response = await apiClient.get(ApiEndpoints.getPlan(planId));

      if (response.statusCode == 200) {
        return StudyPlan.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      // 404 means plan not found – return null (no throw)
      if (e is DioException && e.response?.statusCode == 404) {
        print('❌ Plan $planId not found (404).');
        return null;
      }
      throw StudyPlanException('Error fetching plan: $e');
    }
  }

  /// Get the first active plan (optional – can be used elsewhere but NOT in planDetailsProvider)
  Future<StudyPlan?> getFirstActivePlan() async {
    try {
      final plans = await listPlans(status: 'active');
      if (plans.isNotEmpty) {
        print('✅ Found ${plans.length} active plan(s). First one: ${plans.first.id}');
        return plans.first;
      }
      return null;
    } catch (e) {
      throw StudyPlanException('Error fetching active plans: $e');
    }
  }

  Future<List<StudyPlan>> listPlans({String? status}) async {
    try {
      final Map<String, dynamic> params = status != null ? {'status_filter': status} : {};
      final response = await apiClient.get(
        ApiEndpoints.listPlans,
        queryParameters: params,
      );

      if (response.statusCode == 200) {
        final plans = (response.data as List)
            .map((plan) => StudyPlan.fromJson(plan as Map<String, dynamic>))
            .toList();
        return plans;
      }
      return [];
    } catch (e) {
      throw StudyPlanException('Error listing plans: $e');
    }
  }

  Future<StudySession> getTodaySession(String planId) async {
    try {
      final response = await apiClient.get(ApiEndpoints.getTodaySession(planId));

      if (response.statusCode == 200) {
        return StudySession.fromJson(response.data as Map<String, dynamic>);
      } else {
        throw StudyPlanException('Failed to get today session');
      }
    } catch (e) {
      throw StudyPlanException('Error fetching today session: $e');
    }
  }

  Future<StudySession?> getSessionByDate(String planId, String date) async {
    try {
      final response = await apiClient.get(ApiEndpoints.getSessionByDate(planId, date));

      if (response.statusCode == 200) {
        return StudySession.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      if (e is DioException && e.response?.statusCode == 404) {
        return null; // no session for that date
      }
      throw StudyPlanException('Error fetching session for date: $e');
    }
  }

  Future<StudySession?> getAggregatedTodaySession() async {
    try {
      final response = await apiClient.get(ApiEndpoints.getAggregatedTodaySession);

      if (response.statusCode == 200) {
        return StudySession.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      if (e is DioException && e.response?.statusCode == 404) {
        return null;
      }
      throw StudyPlanException('Error fetching aggregated today session: $e');
    }
  }

  Future<StudySession?> getAggregatedSessionByDate(String date) async {
    try {
      final response = await apiClient.get(ApiEndpoints.getAggregatedSessionByDate(date));

      if (response.statusCode == 200) {
        return StudySession.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      if (e is DioException && e.response?.statusCode == 404) {
        return null;
      }
      throw StudyPlanException('Error fetching aggregated session for date: $e');
    }
  }

  Future<Map<String, dynamic>> completeSession({
    required String sessionId,
    required List<String> completedTaskIds,
    required String userMoodEnd,
    required bool interrupted,
  }) async {
    try {
      final response = await apiClient.post(
        ApiEndpoints.completeSession(sessionId),
        data: {
          'completed_task_ids': completedTaskIds,
          'user_mood_end': userMoodEnd,
          'interrupted': interrupted,
        },
      );

      if (response.statusCode == 200) {
        return response.data;
      } else {
        throw StudyPlanException('Failed to complete session');
      }
    } catch (e) {
      throw StudyPlanException('Error completing session: $e');
    }
  }

  Future<PlanAnalytics> getAnalytics(String planId) async {
    try {
      final response = await apiClient.get(ApiEndpoints.getAnalytics(planId));

      if (response.statusCode == 200) {
        return PlanAnalytics.fromJson(response.data as Map<String, dynamic>);
      } else {
        throw StudyPlanException('Failed to get analytics');
      }
    } catch (e) {
      if (e is DioException && e.response?.statusCode == 404) {
        throw StudyPlanException('Plan not found');
      }
      throw StudyPlanException('Error fetching analytics: $e');
    }
  }

  Future<void> reschedule({
    required String planId,
    required DateTime newDeadline,
  }) async {
    try {
      final response = await apiClient.put(
        ApiEndpoints.reschedulePlan(planId),
        data: {
          'new_deadline': newDeadline.toIso8601String().split('T')[0],
        },
      );

      if (response.statusCode != 200) {
        throw StudyPlanException('Failed to reschedule plan');
      }
    } catch (e) {
      throw StudyPlanException('Error rescheduling plan: $e');
    }
  }

  Future<void> pausePlan(String planId) async {
    try {
      final response = await apiClient.post(ApiEndpoints.pausePlan(planId));

      if (response.statusCode != 200) {
        throw StudyPlanException('Failed to pause plan');
      }
    } catch (e) {
      throw StudyPlanException('Error pausing plan: $e');
    }
  }

  Future<void> resumePlan(String planId) async {
    try {
      final response = await apiClient.post(ApiEndpoints.resumePlan(planId));

      if (response.statusCode != 200) {
        throw StudyPlanException('Failed to resume plan');
      }
    } catch (e) {
      throw StudyPlanException('Error resuming plan: $e');
    }
  }

  Future<void> deletePlan(String planId) async {
    try {
      final response = await apiClient.delete(ApiEndpoints.deletePlan(planId));

      if (response.statusCode != 204) {
        throw StudyPlanException('Failed to delete plan');
      }
    } catch (e) {
      throw StudyPlanException('Error deleting plan: $e');
    }
  }

  /// OPTIONAL: Call this endpoint if the backend supports cleaning stale plan IDs.
  /// This can help fix issues where the server still remembers a deleted plan.
  Future<Map<String, dynamic>> cleanupStalePlans() async {
    try {
      final response = await apiClient.post('/api/v1/planner/cleanup/stale-plans');

      if (response.statusCode == 200) {
        print('🧹 Stale plans cleaned successfully');
        return response.data as Map<String, dynamic>;
      } else {
        throw StudyPlanException('Failed to cleanup stale plans');
      }
    } catch (e) {
      throw StudyPlanException('Error cleaning stale plans: $e');
    }
  }

  // ===================== DAILY PROGRESS TRACKING =====================

  Future<Map<String, dynamic>> getDailyProgress(String date) async {
    try {
      final response = await apiClient.get('/api/v1/planner/progress/daily/$date');

      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      return {};
    } catch (e) {
      if (e is DioException && e.response?.statusCode == 404) {
        return {}; // no progress for that date
      }
      throw StudyPlanException('Error fetching daily progress: $e');
    }
  }

  Future<Map<String, dynamic>> getDailyProgressGraph({int days = 30}) async {
    try {
      final response = await apiClient.get(
        '/api/v1/planner/progress/graph',
        queryParameters: {'days': days},
      );

      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      return {};
    } catch (e) {
      throw StudyPlanException('Error fetching progress graph: $e');
    }
  }

  Future<Map<String, dynamic>> getDailySchedule(String date) async {
    try {
      final response = await apiClient.get('/api/v1/planner/schedule/$date');

      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
      return {};
    } catch (e) {
      if (e is DioException && e.response?.statusCode == 404) {
        return {}; // no schedule for that date
      }
      throw StudyPlanException('Error fetching daily schedule: $e');
    }
  }

  // ===================== USER DEADLINES =====================

  Future<List<UserDeadline>> fetchUpcomingDeadlines({int days = 30}) async {
    try {
      final response = await apiClient.get(
        ApiEndpoints.listDeadlines,
        queryParameters: {'days': days},
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data as List<dynamic>;
        return data
            .map((item) => UserDeadline.fromJson(item as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (e) {
      if (e is DioException && e.response?.statusCode == 404) {
        return []; // no deadlines
      }
      throw StudyPlanException('Error fetching deadlines: $e');
    }
  }

  Future<UserDeadline> createDeadline({
    required String title,
    required DateTime dueDate,
    required String deadlineType,
    String? description,
  }) async {
    try {
      final response = await apiClient.post(
        ApiEndpoints.createDeadline,
        data: {
          'title': title,
          'due_date': dueDate.toIso8601String().split('T')[0],
          'deadline_type': deadlineType,
          'description': description,
        },
      );

      if (response.statusCode == 201) {
        return UserDeadline.fromJson(response.data as Map<String, dynamic>);
      } else {
        throw StudyPlanException('Failed to create deadline');
      }
    } catch (e) {
      throw StudyPlanException('Error creating deadline: $e');
    }
  }

  Future<UserDeadline> markDeadlineCompleted(String deadlineId) async {
    try {
      final response = await apiClient.put(
        ApiEndpoints.markDeadlineCompleted(deadlineId),
      );

      if (response.statusCode == 200) {
        return UserDeadline.fromJson(response.data as Map<String, dynamic>);
      } else {
        throw StudyPlanException('Failed to mark deadline as completed');
      }
    } catch (e) {
      throw StudyPlanException('Error marking deadline as completed: $e');
    }
  }

  Future<void> deleteDeadline(String deadlineId) async {
    try {
      final response = await apiClient.delete(
        ApiEndpoints.deleteDeadline(deadlineId),
      );

      if (response.statusCode != 204) {
        throw StudyPlanException('Failed to delete deadline');
      }
    } catch (e) {
      throw StudyPlanException('Error deleting deadline: $e');
    }
  }
}

// ===================== Providers =====================

final studyPlannerServiceProvider = Provider<StudyPlannerService>((ref) {
  final dioClient = DioClient();
  final apiClient = ApiClient(dioClient);
  return StudyPlannerService(
    dio: dioClient.dio,
    apiClient: apiClient,
  );
});

/// ✅ CRITICAL FIX: Auto-dispose to always fetch fresh plan data from backend
/// This prevents stale plan IDs that no longer exist in the database
final activePlansProvider = FutureProvider.autoDispose<List<StudyPlan>>((ref) async {
  final service = ref.watch(studyPlannerServiceProvider);
  return service.listPlans(status: 'active');
});

/// Provides the first active plan (useful for dashboard / default views)
/// ✅ CRITICAL FIX: Auto-dispose to prevent stale plan data
final currentPlanProvider = FutureProvider.autoDispose<StudyPlan?>((ref) async {
  final service = ref.watch(studyPlannerServiceProvider);
  try {
    final activePlans = await service.listPlans(status: 'active');
    if (activePlans.isEmpty) {
      print('⚠️ No active plans found.');
      return null;
    }
    final firstPlan = activePlans.first;
    print('✅ Current plan set to: ${firstPlan.id} (${firstPlan.planName})');
    return firstPlan;
  } catch (e) {
    print('❌ Error fetching current active plan: $e');
    throw StudyPlanException('Error fetching active plan: $e');
  }
});

/// Invalidates the current plan provider – call after plan modifications.
void invalidateCurrentPlan(WidgetRef ref) {
  ref.invalidate(currentPlanProvider);
}

/// ✅ CRITICAL FIX: Provides the ID of the first active plan
/// Always fetches fresh data to avoid stale plan IDs
final activePlanIdProvider = FutureProvider.autoDispose<String?>((ref) async {
  final service = ref.watch(studyPlannerServiceProvider);
  final plans = await service.listPlans(status: 'active');
  return plans.isNotEmpty ? plans.first.id : null;
});

/// Fetches a specific plan by ID. Returns null if not found (404).
/// ✅ CRITICAL FIX: Auto-dispose to always fetch fresh data
final planDetailsProvider = FutureProvider.autoDispose.family<StudyPlan?, String>((ref, planId) async {
  final service = ref.watch(studyPlannerServiceProvider);
  if (planId.isEmpty) {
    throw StudyPlanException('Invalid plan ID: empty string');
  }
  return await service.getPlan(planId);
});

final todaySessionProvider = FutureProvider.family<StudySession, String>((ref, planId) async {
  final service = ref.watch(studyPlannerServiceProvider);
  if (planId.isEmpty) {
    throw StudyPlanException('Invalid plan ID: empty string');
  }
  try {
    return await service.getTodaySession(planId);
  } catch (e) {
    if (e.toString().contains('404') || e.toString().contains('not found')) {
      throw StudyPlanException('Plan does not exist or has been deleted');
    }
    rethrow;
  }
});

final sessionByDateProvider = FutureProvider.family<StudySession?, ({String planId, String date})>(
  (ref, params) async {
    final service = ref.watch(studyPlannerServiceProvider);
    if (params.planId.isEmpty) {
      throw StudyPlanException('Invalid plan ID: empty string');
    }
    return await service.getSessionByDate(params.planId, params.date);
  },
);

final aggregatedTodaySessionProvider = FutureProvider.autoDispose<StudySession?>((ref) async {
  final service = ref.watch(studyPlannerServiceProvider);
  return await service.getAggregatedTodaySession();
});

final aggregatedSessionByDateProvider = FutureProvider.autoDispose.family<StudySession?, String>(
  (ref, date) async {
    final service = ref.watch(studyPlannerServiceProvider);
    return await service.getAggregatedSessionByDate(date);
  },
);

final planAnalyticsProvider = FutureProvider.family<PlanAnalytics, String>((ref, planId) async {
  final service = ref.watch(studyPlannerServiceProvider);
  return service.getAnalytics(planId);
});

final planGenerationProvider = FutureProvider.family<StudyPlan?, Map<dynamic, dynamic>>(
  (ref, params) async {
    final service = ref.watch(studyPlannerServiceProvider);
    try {
      return await service.generatePlan(
        subjects: List<String>.from((params['subjects'] as List?) ?? []),
        deadline: DateTime.parse(params['deadline'] as String),
        mode: (params['mode'] as String?) ?? 'unified',
        totalStudyHoursPerWeek: (params['totalStudyHoursPerWeek'] as int?) ?? 20,
      );
    } catch (e) {
      return null;
    }
  },
);

/// Provider to cleanup stale plan IDs from backend
/// Call this after login or when plans change to ensure no dead IDs are cached
final cleanupStalePlansProvider = FutureProvider<void>((ref) async {
  final service = ref.watch(studyPlannerServiceProvider);
  try {
    await service.cleanupStalePlans();
    print('🧹 Stale plans cleaned successfully on app startup');
  } catch (e) {
    print('⚠️ Failed to cleanup stale plans: $e');
    // Don't throw - this is non-critical
  }
});

// ===================== DAILY PROGRESS PROVIDERS =====================

/// Get daily progress analytics for a specific date
final dailyProgressProvider = FutureProvider.family<Map<String, dynamic>, String>(
  (ref, date) async {
    final service = ref.watch(studyPlannerServiceProvider);
    return await service.getDailyProgress(date);
  },
);

/// Get daily progress graph data for the past N days
final dailyProgressGraphProvider = FutureProvider.family<Map<String, dynamic>, int>(
  (ref, days) async {
    final service = ref.watch(studyPlannerServiceProvider);
    return await service.getDailyProgressGraph(days: days);
  },
);

/// Get daily schedule for a specific date
final dailyScheduleProvider = FutureProvider.family<Map<String, dynamic>, String>(
  (ref, date) async {
    final service = ref.watch(studyPlannerServiceProvider);
    return await service.getDailySchedule(date);
  },
);

// ===================== USER DEADLINES PROVIDERS =====================

/// Provides list of upcoming deadlines for the user
/// Auto-dispose ensures fresh data on each access
final upcomingDeadlinesProvider = FutureProvider.autoDispose.family<List<UserDeadline>, int>(
  (ref, days) async {
    final service = ref.watch(studyPlannerServiceProvider);
    return await service.fetchUpcomingDeadlines(days: days);
  },
);

/// Convenience provider for default 30 days look-ahead
final upcomingDeadlinesDefaultProvider = FutureProvider.autoDispose<List<UserDeadline>>((ref) async {
  final service = ref.watch(studyPlannerServiceProvider);
  return await service.fetchUpcomingDeadlines(days: 30);
});
