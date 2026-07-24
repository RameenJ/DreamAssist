import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/api/api_models.dart';
import '../../providers/study_planner_provider.dart';

class AnalyticsDashboardScreen extends ConsumerWidget {
  final String planId;

  const AnalyticsDashboardScreen({
    super.key,
    required this.planId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Use the user‑selected planId – do NOT override.
    final analyticsAsync = ref.watch(planAnalyticsProvider(planId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Study Analytics'),
        elevation: 0,
        centerTitle: true,
      ),
      body: analyticsAsync.when(
        data: (analytics) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildHeaderMetrics(context, analytics),
                const SizedBox(height: 24),
                _buildSubjectProgress(context, analytics),
                const SizedBox(height: 24),
                _buildMoodDistribution(context, analytics),
                const SizedBox(height: 24),
                _buildWeeklySummaries(context, analytics),
                const SizedBox(height: 24),
              ],
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => _buildErrorUI(context, error),
      ),
    );
  }

  // ===================== Error UI =====================

  Widget _buildErrorUI(BuildContext context, Object error) {
    final is404 = error.toString().contains('404') ||
                   error.toString().contains('not found');

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.red),
          const SizedBox(height: 16),
          Text(
            is404 ? 'Plan not found' : 'Error loading analytics',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              is404
                  ? 'This plan may have been deleted or is no longer accessible.'
                  : 'Failed to load analytics. Please check your connection.',
              style: const TextStyle(fontSize: 12, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 24),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ElevatedButton.icon(
                onPressed: () => Navigator.of(context).pop(),
                icon: const Icon(Icons.arrow_back),
                label: const Text('Go Back'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: () => Navigator.of(context).popUntil(
                  (route) => route.settings.name == '/study-planner' || route.isFirst,
                ),
                icon: const Icon(Icons.list),
                label: const Text('View All Plans'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ===================== Existing UI methods (unchanged) =====================

  Widget _buildHeaderMetrics(BuildContext context, PlanAnalytics analytics) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Theme.of(context).primaryColor,
            Theme.of(context).primaryColor.withOpacity(0.7),
          ],
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildMetricCard(
                label: 'Completion',
                value: '${(analytics.overallCompletionRate * 100).toStringAsFixed(1)}%',
                icon: Icons.done_all,
                backgroundColor: Colors.green[300],
              ),
              _buildMetricCard(
                label: 'Productivity',
                value: '${(analytics.productivityScore * 100).toStringAsFixed(1)}%',
                icon: Icons.trending_up,
                backgroundColor: Colors.blue[300],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard({
    required String label,
    required String value,
    required IconData icon,
    required Color? backgroundColor,
  }) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: backgroundColor,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: Colors.white, size: 28),
        ),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 12,
          ),
        ),
      ],
    );
  }

  Widget _buildSubjectProgress(BuildContext context, PlanAnalytics analytics) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Subject-wise Progress',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 16),
        if (analytics.subjectCompletion.isEmpty)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text('No subject data available'),
            ),
          )
        else
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: analytics.subjectCompletion.length,
            itemBuilder: (context, index) {
              final subject = analytics.subjectCompletion.keys.toList()[index];
              final progress = analytics.subjectCompletion[subject]!;
              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(subject, style: const TextStyle(fontWeight: FontWeight.w600)),
                        Text('${(progress * 100).toStringAsFixed(1)}%',
                            style: const TextStyle(fontWeight: FontWeight.w600)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: progress,
                        minHeight: 8,
                        backgroundColor: Colors.grey[200],
                        valueColor: AlwaysStoppedAnimation<Color>(
                          _getProgressColor(progress),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
      ],
    );
  }

  Widget _buildMoodDistribution(BuildContext context, PlanAnalytics analytics) {
    final totalMoodEntries =
        analytics.moodDistribution.values.fold<int>(0, (sum, count) => sum + count);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Mood Distribution',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 16),
        if (analytics.moodDistribution.isEmpty)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text('No mood data available'),
            ),
          )
        else
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey[300]!),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              children: analytics.moodDistribution.entries.map((entry) {
                final mood = entry.key;
                final count = entry.value;
                final percentage = totalMoodEntries > 0 ? count / totalMoodEntries : 0.0;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    children: [
                      SizedBox(
                        width: 80,
                        child: Text(
                          mood,
                          style: TextStyle(
                            color: _getMoodColor(mood),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: percentage,
                            minHeight: 12,
                            backgroundColor: Colors.grey[200],
                            valueColor: AlwaysStoppedAnimation<Color>(_getMoodColor(mood)),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text('$count',
                          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
      ],
    );
  }

  Widget _buildWeeklySummaries(BuildContext context, PlanAnalytics analytics) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Weekly Summary',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 16),
        if (analytics.weeklySummaries.isEmpty)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text('No weekly data available'),
            ),
          )
        else
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: analytics.weeklySummaries.length,
            itemBuilder: (context, index) {
              final summary = analytics.weeklySummaries[index];
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Week ${summary.week}',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            decoration: BoxDecoration(
                              color: _getProgressColor(summary.completionRate),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '${(summary.completionRate * 100).toStringAsFixed(0)}%',
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Sessions Completed',
                                style: TextStyle(color: Colors.grey[600], fontSize: 12),
                              ),
                              Text(
                                '${summary.totalSessionsCompleted}/${summary.totalSessionsPlanned}',
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                              ),
                            ],
                          ),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Average Mood',
                                style: TextStyle(color: Colors.grey[600], fontSize: 12),
                              ),
                              Text(
                                '${(summary.averageMood * 100).toStringAsFixed(0)}%',
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
      ],
    );
  }

  Color _getProgressColor(double progress) {
    if (progress >= 0.8) return Colors.green;
    if (progress >= 0.6) return Colors.amber;
    if (progress >= 0.4) return Colors.orange;
    return Colors.red;
  }

  Color _getMoodColor(String mood) {
    switch (mood.toLowerCase()) {
      case 'motivated':
      case 'engaged':
      case 'confident':
        return Colors.green;
      case 'neutral':
        return Colors.blue;
      case 'stressed':
      case 'frustrated':
      case 'tired':
        return Colors.red;
      case 'bored':
      case 'confused':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }
}