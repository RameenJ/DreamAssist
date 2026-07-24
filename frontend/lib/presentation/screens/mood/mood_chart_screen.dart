import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../providers/mood_provider.dart';
import '../../../data/models/mood_log_model.dart';

/// Screen for displaying mood trends and history
class MoodChartScreen extends ConsumerStatefulWidget {
  const MoodChartScreen({super.key});

  @override
  ConsumerState<MoodChartScreen> createState() => _MoodChartScreenState();
}

class _MoodChartScreenState extends ConsumerState<MoodChartScreen> {
  late int _selectedDays;

  @override
  void initState() {
    super.initState();
    _selectedDays = 7;
  }

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

  @override
  Widget build(BuildContext context) {
    final historyState = ref.watch(moodHistoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mood Trends'),
        elevation: 0,
      ),
      body: historyState.isLoading
          ? const Center(child: CircularProgressIndicator())
          : historyState.error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline,
                          size: 48, color: Colors.red.shade400),
                      const SizedBox(height: 16),
                      Text(
                        'Error: ${historyState.error}',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.red.shade400),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () {
                          ref
                              .read(moodHistoryProvider.notifier)
                              .fetchMoodHistory(days: _selectedDays);
                        },
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Date range selector
                      _buildDateRangeSelector(),
                      const SizedBox(height: 24),

                      // Chart section
                      Card(
                        elevation: 0,
                        color: Colors.grey.shade50,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Mood History',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              const SizedBox(height: 16),
                              if (historyState.history?.moodLogs.isEmpty ??
                                  true)
                                Center(
                                  child: Padding(
                                    padding: const EdgeInsets.symmetric(
                                        vertical: 40),
                                    child: Column(
                                      children: [
                                        Icon(Icons.sentiment_satisfied_alt,
                                            size: 48,
                                            color: Colors.grey.shade400),
                                        const SizedBox(height: 12),
                                        Text(
                                          'No mood data available',
                                          style: TextStyle(
                                              color: Colors.grey.shade600),
                                        ),
                                      ],
                                    ),
                                  ),
                                )
                              else
                                _buildMoodChart(
                                    historyState.history!.moodLogs),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Mood distribution
                      if (historyState.history?.moodLogs.isNotEmpty ?? false)
                        _buildMoodDistribution(
                            historyState.history!.moodLogs),
                      const SizedBox(height: 24),

                      // Statistics
                      if (historyState.history?.moodLogs.isNotEmpty ?? false)
                        _buildStatistics(historyState.history!.moodLogs),
                    ],
                  ),
                ),
    );
  }

  Widget _buildDateRangeSelector() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _buildDateRangeButton(7, '7 Days'),
        const SizedBox(width: 16),
        _buildDateRangeButton(14, '14 Days'),
      ],
    );
  }

  Widget _buildDateRangeButton(int days, String label) {
    final isSelected = _selectedDays == days;
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor:
            isSelected ? Theme.of(context).primaryColor : Colors.grey.shade200,
        foregroundColor: isSelected ? Colors.white : Colors.black87,
        elevation: 0,
      ),
      onPressed: () {
        setState(() => _selectedDays = days);
        ref
            .read(moodHistoryProvider.notifier)
            .switchDayRange(days);
      },
      child: Text(label),
    );
  }

  Widget _buildMoodChart(List<MoodHistoryEntry> moodLogs) {
    if (moodLogs.isEmpty) {
      return const SizedBox.shrink();
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

    return SizedBox(
      height: 300,
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
                      radius: 5,
                      color: Colors.white,
                      strokeColor: Theme.of(context).primaryColor,
                      strokeWidth: 2,
                    );
                  }
                  return FlDotCirclePainter(radius: 4);
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
    );
  }

  Widget _buildMoodDistribution(List<MoodHistoryEntry> moodLogs) {
    // Count mood occurrences
    final moodCounts = <String, int>{};
    for (final log in moodLogs) {
      moodCounts[log.mood] = (moodCounts[log.mood] ?? 0) + 1;
    }

    // Sort by count descending
    final sortedMoods = moodCounts.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return Card(
      elevation: 0,
      color: Colors.grey.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Mood Distribution',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16),
            ...sortedMoods.map((entry) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          _getMoodEmoji(entry.key),
                          style: const TextStyle(fontSize: 20),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            entry.key.capitalize(),
                            style: const TextStyle(fontWeight: FontWeight.w500),
                          ),
                        ),
                        Text(
                          '${entry.value} times',
                          style: TextStyle(
                            color: Colors.grey.shade600,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: entry.value / moodLogs.length,
                        minHeight: 6,
                        backgroundColor: Colors.grey.shade300,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          _getMoodBarColor(entry.key),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildStatistics(List<MoodHistoryEntry> moodLogs) {
    // Calculate statistics
    final values = moodLogs.map((log) => _getMoodValue(log.mood)).toList();
    final avgMood = values.isEmpty ? 4 : values.reduce((a, b) => a + b) / values.length;
    final maxMood = values.isEmpty ? 4 : values.reduce((a, b) => a > b ? a : b);

    return Card(
      elevation: 0,
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Your Statistics',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatisticCard(
                  'Average Mood',
                  _getMoodEmoji(_getMoodLabel(avgMood.toInt())),
                  avgMood.toStringAsFixed(1),
                ),
                _buildStatisticCard(
                  'Best Mood',
                  _getMoodEmoji(_getMoodLabel(maxMood)),
                  _getMoodLabel(maxMood).capitalize(),
                ),
                _buildStatisticCard(
                  'Total Logs',
                  '📊',
                  '${moodLogs.length}',
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatisticCard(String label, String emoji, String value) {
    return Column(
      children: [
        Text(emoji, style: const TextStyle(fontSize: 32)),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
          ),
        ),
      ],
    );
  }

  String _getMoodLabel(int value) {
    const moods = {
      1: 'stressed',
      2: 'confused',
      3: 'bored',
      4: 'neutral',
      5: 'engaged',
      6: 'motivated',
      7: 'confident',
    };
    return moods[value] ?? 'neutral';
  }

  Color _getMoodBarColor(String mood) {
    switch (mood.toLowerCase()) {
      case 'stressed':
      case 'frustrated':
        return Colors.red.shade400;
      case 'confused':
      case 'bored':
        return Colors.orange.shade400;
      case 'neutral':
      case 'engaged':
        return Colors.blue.shade400;
      case 'motivated':
      case 'confident':
        return Colors.green.shade400;
      default:
        return Colors.grey.shade400;
    }
  }
}

extension on String {
  String capitalize() {
    return this[0].toUpperCase() + substring(1);
  }
}
