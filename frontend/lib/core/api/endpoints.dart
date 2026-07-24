/// API endpoints for the DreamAssist application
class ApiEndpoints {
  // Base paths
  static const String planner = '/api/v1/planner';
  static const String goals = '/api/v1/goals';
  static const String conflicts = '/api/v1/conflicts';

  // Study Plan Endpoints
  static const String generatePlan = '$planner/plans/generate';
  static const String listPlans = '$planner/plans';
  static String getPlan(String planId) => '$planner/plans/$planId';
  static String updatePlan(String planId) => '$planner/plans/$planId';
  static String deletePlan(String planId) => '$planner/plans/$planId';
  static String pausePlan(String planId) => '$planner/plans/$planId/pause';
  static String resumePlan(String planId) => '$planner/plans/$planId/resume';
  static String reschedulePlan(String planId) => '$planner/plans/$planId/reschedule';

  // Study Session Endpoints
  static String getTodaySession(String planId) => '$planner/plans/$planId/sessions/today';
  static String getSessionByDate(String planId, String date) =>
      '$planner/plans/$planId/sessions/$date';
  static String completeSession(String sessionId) =>
      '$planner/sessions/$sessionId/complete';
  static String skipSession(String sessionId) => '$planner/sessions/$sessionId/skip';

  // Aggregated Study Session Endpoints (for multiple active plans)
  static const String getAggregatedTodaySession = '$planner/sessions/today/aggregated';
  static String getAggregatedSessionByDate(String date) =>
      '$planner/sessions/$date/aggregated';

  // Analytics Endpoints
  static String getAnalytics(String planId) => '$planner/plans/$planId/analytics';
  static String getWeeklyAnalytics(String planId) =>
      '$planner/plans/$planId/analytics/weekly';
  static String getMonthlyAnalytics(String planId) =>
      '$planner/plans/$planId/analytics/monthly';

  // Goal-Based Planning Endpoints (Phase 2b)
  static const String createGoal = '$goals/create';
  static const String listGoals = '$goals/list';
  static String getGoal(String goalId) => '$goals/$goalId';
  static String updateGoalStatus(String goalId) => '$goals/$goalId/status';
  static String generateGoalPlan(String goalId) => '$goals/$goalId/generate-plan';
  static String getGoalProgress(String goalId) => '$goals/$goalId/progress';
  static String updateGoalProgress(String goalId) =>
      '$goals/$goalId/update-progress';
  static String getGoalRecommendations(String goalId) =>
      '$goals/$goalId/recommendations';

  // Conflict Detection Endpoints (Phase 2c)
  static const String detectConflicts = '$conflicts/detect';
  static const String listConflicts = '$conflicts/list';
  static String getConflict(String conflictId) => '$conflicts/$conflictId';
  static String getConflictSuggestions(String conflictId) =>
      '$conflicts/$conflictId/suggestions';
  static String resolveConflict(String conflictId) =>
      '$conflicts/$conflictId/resolve';
  static const String autoResolveConflicts = '$conflicts/resolve/auto';
  static const String batchResolveConflicts = '$conflicts/resolve/batch';
  static const String conflictDashboard = '$conflicts/dashboard/summary';

  // User Deadlines Endpoints (Assignment/Quiz/Exam dates)
  static const String createDeadline = '$planner/deadlines';
  static const String listDeadlines = '$planner/deadlines';
  static String markDeadlineCompleted(String deadlineId) =>
      '$planner/deadlines/$deadlineId/complete';
  static String deleteDeadline(String deadlineId) =>
      '$planner/deadlines/$deadlineId';
}
