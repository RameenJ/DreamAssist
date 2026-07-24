import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../providers/mood_provider.dart';
import '../../../data/models/mood_log_model.dart';
import 'mood_chart_screen.dart';

/// Screen for logging user's mood
class MoodLogScreen extends ConsumerStatefulWidget {
  const MoodLogScreen({super.key});

  @override
  ConsumerState<MoodLogScreen> createState() => _MoodLogScreenState();
}

class _MoodLogScreenState extends ConsumerState<MoodLogScreen> {
  String? _selectedMood;
  bool _isSubmitting = false;

  int _getMoodValue(String mood) {
    // Map mood labels to numeric values for visualization
    const moodValues = {
      'stressed': 1,
      'confused': 2,
      'frustrated': 2,
      'bored': 3,
      'neutral': 4,
      'engaged': 5,
      'motivated': 6,
      'confident': 7,
    };
    return moodValues[mood.toLowerCase()] ?? 4;
  }

  String _getMoodEmoji(String mood) {
    return MoodEmotion.fromLabel(mood)?.emoji ?? '😐';
  }

  Color _getMoodBarColor(String mood) {
    final moodValue = _getMoodValue(mood);
    // Create a color gradient from red (stressed) to green (confident)
    if (moodValue <= 1) return Colors.red;
    if (moodValue == 2) return Colors.orange;
    if (moodValue == 3) return Colors.yellow;
    if (moodValue == 4) return Colors.blue;
    if (moodValue == 5) return Colors.lightGreen;
    if (moodValue == 6) return Colors.green;
    return Colors.teal;
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Check today's mood status
      ref.read(moodProvider.notifier).checkTodayMood();
      // Fetch mood history
      ref.read(moodHistoryProvider.notifier).fetchMoodHistory(days: 7);
    });
  }

  Future<void> _logMood(String mood) async {
    if (_isSubmitting) return;

    setState(() => _isSubmitting = true);

    final success = await ref.read(moodProvider.notifier).logMood(mood);

    if (!mounted) return;

    setState(() => _isSubmitting = false);

    if (success) {
      // Show success feedback
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.check_circle, color: Colors.white),
              const SizedBox(width: 12),
              const Text('Mood logged successfully!'),
            ],
          ),
          backgroundColor: Colors.green,
          duration: const Duration(seconds: 2),
        ),
      );

      // Update selected mood
      setState(() => _selectedMood = mood);

      // Refresh mood history
      await ref
          .read(moodHistoryProvider.notifier)
          .fetchMoodHistory(days: 7);
    } else {
      // Show error
      final error = ref.read(moodProvider).error;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error ?? 'Failed to log mood'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final moodState = ref.watch(moodProvider);
    final todayMood = moodState.todayMood;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mood Logger'),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.trending_up),
            tooltip: 'View mood trends',
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (context) => const MoodChartScreen(),
                ),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header section
            Card(
              elevation: 0,
              color: Colors.blue.shade50,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'How are you feeling today?',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      DateFormat('EEEE, MMMM d, yyyy').format(DateTime.now()),
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade700,
                      ),
                    ),
                    if (todayMood?.logged == true) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: Colors.green.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.check_circle,
                                color: Colors.green.shade700, size: 18),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Already logged: ${todayMood?.mood ?? "Unknown"}',
                                style: TextStyle(
                                  color: Colors.green.shade700,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 30),

            // Mood selection grid
            const Text(
              'Select your mood:',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16),
            GridView.builder(
              physics: const NeverScrollableScrollPhysics(),
              shrinkWrap: true,
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 1.1,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
              ),
              itemCount: MoodEmotion.allMoods.length,
              itemBuilder: (context, index) {
                final mood = MoodEmotion.allMoods[index];
                final isSelected = _selectedMood == mood.label;

                return _buildMoodButton(
                  mood: mood,
                  isSelected: isSelected,
                  onPressed: () {
                    if (!_isSubmitting) {
                      _logMood(mood.label);
                    }
                  },
                );
              },
            ),
            const SizedBox(height: 20),

            // Loading indicator if submitting
            if (_isSubmitting)
              Center(
                child: Column(
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 12),
                    Text(
                      'Logging mood...',
                      style: TextStyle(color: Colors.grey.shade600),
                    ),
                  ],
                ),
              ),

            // Error message
            if (moodState.error != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  border: Border.all(color: Colors.red.shade200),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(Icons.error_outline, color: Colors.red.shade700),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        moodState.error!,
                        style: TextStyle(color: Colors.red.shade700),
                      ),
                    ),
                  ],
                ),
              ),

            const SizedBox(height: 24),

            // Tips section
            Card(
              elevation: 0,
              color: Colors.amber.shade50,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.lightbulb_outline,
                            color: Colors.amber.shade700),
                        const SizedBox(width: 8),
                        Text(
                          'Did you know?',
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            color: Colors.amber.shade900,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Logging your mood helps DreamAssist personalize your study plan. '
                      'When you\'re stressed, we lighten your workload. When you\'re confident, '
                      'we add more challenging tasks!',
                      style: TextStyle(
                        color: Colors.amber.shade900,
                        height: 1.5,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 30),

            // 7-Day Mood Graph
            _buildMoodGraph(),
          ],
        ),
      ),
    );
  }

  Widget _buildMoodGraph() {
    return Consumer(
      builder: (context, ref, child) {
        final historyState = ref.watch(moodHistoryProvider);
        
        if (historyState.isLoading) {
          return Card(
            elevation: 0,
            color: Colors.grey.shade50,
            child: const Padding(
              padding: EdgeInsets.all(16),
              child: Center(child: CircularProgressIndicator()),
            ),
          );
        }

        if (historyState.error != null) {
          return Card(
            elevation: 0,
            color: Colors.red.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Icon(Icons.error_outline, color: Colors.red.shade400, size: 32),
                  const SizedBox(height: 8),
                  Text(
                    'Error loading mood history',
                    style: TextStyle(color: Colors.red.shade700),
                  ),
                ],
              ),
            ),
          );
        }

        final moodLogs = historyState.history?.moodLogs ?? [];
        
        if (moodLogs.isEmpty) {
          return Card(
            elevation: 0,
            color: Colors.grey.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Icon(Icons.sentiment_satisfied_alt,
                      size: 40, color: Colors.grey.shade400),
                  const SizedBox(height: 12),
                  Text(
                    'No mood data for the past 7 days yet',
                    style: TextStyle(color: Colors.grey.shade600),
                  ),
                ],
              ),
            ),
          );
        }

        // Sort by date
        final sortedLogs = List<MoodHistoryEntry>.from(moodLogs)
          ..sort((a, b) => a.date.compareTo(b.date));

        // Convert to line chart data
        final spots = sortedLogs.asMap().entries.map((entry) {
          return FlSpot(
            entry.key.toDouble(),
            _getMoodValue(entry.value.mood).toDouble(),
          );
        }).toList();

        return Card(
          elevation: 0,
          color: Colors.grey.shade50,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '7-Day Mood Trend',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  height: 250,
                  child: LineChart(
                    LineChartData(
                      gridData: FlGridData(
                        show: true,
                        drawVerticalLine: true,
                        horizontalInterval: 1,
                        verticalInterval: 1,
                        getDrawingHorizontalLine: (value) {
                          return FlLine(
                            color: Colors.grey.shade200,
                            strokeWidth: 1,
                          );
                        },
                        getDrawingVerticalLine: (value) {
                          return FlLine(
                            color: Colors.grey.shade200,
                            strokeWidth: 1,
                          );
                        },
                      ),
                      titlesData: FlTitlesData(
                        show: true,
                        rightTitles: const AxisTitles(),
                        topTitles: const AxisTitles(),
                        bottomTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 30,
                            getTitlesWidget: (value, meta) {
                              int index = value.toInt();
                              if (index < 0 || index >= sortedLogs.length) {
                                return const Text('');
                              }
                              try {
                                final date = DateTime.parse(sortedLogs[index].date);
                                return Text(
                                  DateFormat('M/d').format(date),
                                  style: const TextStyle(fontSize: 10),
                                );
                              } catch (_) {
                                return const Text('');
                              }
                            },
                          ),
                        ),
                        leftTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 40,
                            getTitlesWidget: (value, meta) {
                              const moods = [
                                '',
                                '😰 Stressed',
                                '😕 Confused',
                                '😑 Bored',
                                '😐 Neutral',
                                '😊 Engaged',
                                '💪 Motivated',
                                '😎 Confident',
                              ];
                              int index = value.toInt();
                              if (index < 0 || index >= moods.length) {
                                return const Text('');
                              }
                              return Text(
                                moods[index],
                                style: const TextStyle(fontSize: 9),
                              );
                            },
                          ),
                        ),
                      ),
                      borderData: FlBorderData(
                        show: true,
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      lineBarsData: [
                        LineChartBarData(
                          spots: spots,
                          isCurved: true,
                          gradient: LinearGradient(
                            colors: [
                              Theme.of(context).primaryColor.withOpacity(0.8),
                              Theme.of(context).primaryColor.withOpacity(0.2),
                            ],
                          ),
                          barWidth: 3,
                          isStrokeCapRound: true,
                          dotData: FlDotData(
                            show: true,
                            getDotPainter: (spot, percent, barData, index) {
                              if (index < sortedLogs.length) {
                                return FlDotCirclePainter(
                                  radius: 4,
                                  color: Colors.white,
                                  strokeColor: Theme.of(context).primaryColor,
                                  strokeWidth: 2,
                                );
                              }
                              return FlDotCirclePainter(radius: 3);
                            },
                          ),
                          belowBarData: BarAreaData(
                            show: true,
                            gradient: LinearGradient(
                              colors: [
                                Theme.of(context).primaryColor.withOpacity(0.3),
                                Theme.of(context).primaryColor.withOpacity(0.0),
                              ],
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                            ),
                          ),
                        ),
                      ],
                      minY: 0,
                      maxY: 8,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildMoodButton({
    required MoodEmotion mood,
    required bool isSelected,
    required VoidCallback onPressed,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: _isSubmitting ? null : onPressed,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected
                  ? Theme.of(context).primaryColor
                  : Colors.grey.shade300,
              width: isSelected ? 3 : 1,
            ),
            color: isSelected
                ? Theme.of(context).primaryColor.withOpacity(0.1)
                : Colors.grey.shade50,
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                mood.emoji,
                style: const TextStyle(fontSize: 40),
              ),
              const SizedBox(height: 8),
              Text(
                mood.label,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: isSelected
                      ? Theme.of(context).primaryColor
                      : Colors.grey.shade700,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
