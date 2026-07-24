import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/study_planner_provider.dart';
import 'dart:ui' as ui;


class DailyProgressGraphScreen extends ConsumerStatefulWidget {
  const DailyProgressGraphScreen({super.key});

  @override
  ConsumerState<DailyProgressGraphScreen> createState() =>
      _DailyProgressGraphScreenState();
}

class _DailyProgressGraphScreenState
    extends ConsumerState<DailyProgressGraphScreen> {
  int _selectedDays = 30;

  @override
  Widget build(BuildContext context) {
    final graphDataAsync = ref.watch(dailyProgressGraphProvider(_selectedDays));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Daily Progress Analytics'),
        elevation: 0,
        centerTitle: true,
      ),
      body: graphDataAsync.when(
        data: (graphData) => _buildGraphView(graphData, context),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => _buildErrorView(error),
      ),
    );
  }

  Widget _buildErrorView(Object error) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.red),
          const SizedBox(height: 16),
          const Text('Error loading progress data'),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              error.toString(),
              style: const TextStyle(fontSize: 12, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              ref.invalidate(dailyProgressGraphProvider(_selectedDays));
            },
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildGraphView(Map<String, dynamic> graphData, BuildContext context) {
    final dates = List<String>.from(graphData['dates'] as List? ?? []);
    final completionRates =
        List<double>.from(graphData['completion_rates'] as List? ?? []);
    final productivityScores =
        List<double>.from(graphData['productivity_scores'] as List? ?? []);
    final focusScores =
        List<double>.from(graphData['focus_scores'] as List? ?? []);
    final studyTimeMins =
        List<int>.from(graphData['study_time_mins'] as List? ?? []);
    final streakCount = graphData['streak_count'] as int? ?? 0;
    final avgCompletion = graphData['average_completion_rate'] as double? ?? 0.0;
    final avgProductivity = graphData['average_productivity'] as double? ?? 0.0;

    return SingleChildScrollView(
      child: Column(
        children: [
          // ========== STREAK & STATS CARDS ==========
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: _buildStatCard(
                    icon: Icons.local_fire_department,
                    label: 'Current Streak',
                    value: '$streakCount days',
                    color: Colors.orange,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildStatCard(
                    icon: Icons.check_circle,
                    label: 'Avg Completion',
                    value: '${(avgCompletion * 100).toStringAsFixed(0)}%',
                    color: Colors.green,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildStatCard(
                    icon: Icons.trending_up,
                    label: 'Avg Productivity',
                    value: '${(avgProductivity * 100).toStringAsFixed(0)}%',
                    color: Colors.blue,
                  ),
                ),
              ],
            ),
          ),
          const Divider(),

          // ========== DAYS FILTER ==========
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Show past:',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                ),
                Wrap(
                  spacing: 8,
                  children: [7, 14, 30, 90, 365].map((days) {
                    return FilterChip(
                      label: Text('${days}d'),
                      selected: _selectedDays == days,
                      onSelected: (selected) {
                        setState(() => _selectedDays = days);
                      },
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
          const Divider(),

          // ========== COMPLETION RATE CHART ==========
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Completion Rate Over Time',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                if (dates.isNotEmpty)
                  SizedBox(
                    height: 200,
                    child: _buildLineChart(
                      dates: dates,
                      values: completionRates,
                      label: 'Completion %',
                      color: Colors.green,
                    ),
                  )
                else
                  const Center(
                    child: Text('No data available'),
                  ),
              ],
            ),
          ),

          // ========== PRODUCTIVITY SCORE CHART ==========
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Productivity & Focus Scores',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                if (dates.isNotEmpty)
                  SizedBox(
                    height: 200,
                    child: _buildMultiLineChart(
                      dates: dates,
                      values1: productivityScores,
                      label1: 'Productivity',
                      color1: Colors.blue,
                      values2: focusScores,
                      label2: 'Focus',
                      color2: Colors.purple,
                    ),
                  )
                else
                  const Center(
                    child: Text('No data available'),
                  ),
              ],
            ),
          ),

          // ========== STUDY TIME CHART ==========
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Daily Study Time',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                if (dates.isNotEmpty)
                  SizedBox(
                    height: 200,
                    child: _buildBarChart(
                      dates: dates,
                      values: studyTimeMins,
                      label: 'Minutes',
                      color: Colors.indigo,
                    ),
                  )
                else
                  const Center(
                    child: Text('No data available'),
                  ),
              ],
            ),
          ),

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Card(
      elevation: 2,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          gradient: LinearGradient(
            colors: [color.withOpacity(0.1), color.withOpacity(0.05)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLineChart({
    required List<String> dates,
    required List<double> values,
    required String label,
    required Color color,
  }) {
    return CustomPaint(
      painter: LineChartPainter(
        dates: dates,
        values: values,
        label: label,
        color: color,
        maxValue: 1.0,
      ),
      size: const Size(double.infinity, 200),
    );
  }

  Widget _buildMultiLineChart({
    required List<String> dates,
    required List<double> values1,
    required String label1,
    required Color color1,
    required List<double> values2,
    required String label2,
    required Color color2,
  }) {
    return CustomPaint(
      painter: MultiLineChartPainter(
        dates: dates,
        values1: values1,
        label1: label1,
        color1: color1,
        values2: values2,
        label2: label2,
        color2: color2,
        maxValue: 1.0,
      ),
      size: const Size(double.infinity, 200),
    );
  }

  Widget _buildBarChart({
    required List<String> dates,
    required List<int> values,
    required String label,
    required Color color,
  }) {
    final maxValue = values.isEmpty ? 1 : values.reduce((a, b) => a > b ? a : b);

    return CustomPaint(
      painter: BarChartPainter(
        dates: dates,
        values: values,
        label: label,
        color: color,
        maxValue: maxValue.toDouble(),
      ),
      size: const Size(double.infinity, 200),
    );
  }
}

// ===================== CUSTOM PAINTERS FOR CHARTS =====================

class LineChartPainter extends CustomPainter {
  final List<String> dates;
  final List<double> values;
  final String label;
  final Color color;
  final double maxValue;

  LineChartPainter({
    required this.dates,
    required this.values,
    required this.label,
    required this.color,
    required this.maxValue,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (values.isEmpty) return;

    final paint = Paint()
      ..color = color
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final fillPaint = Paint()
      ..color = color.withOpacity(0.2)
      ..style = PaintingStyle.fill;

    final pointPaint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final padding = 40.0;
    final graphWidth = size.width - padding * 2;
    final graphHeight = size.height - padding;

    // Draw grid lines and labels
    final xStep = graphWidth / (values.length - 1).clamp(1, double.infinity);

    // Draw points and lines
    Path path = Path();
    for (int i = 0; i < values.length; i++) {
      final x = padding + i * xStep;
      final y = size.height -
          padding +
          10 -
          (values[i] / maxValue) * graphHeight;

      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }

    // Draw fill area
    path.lineTo(
      padding + (values.length - 1) * xStep,
      size.height - padding + 10,
    );
    path.lineTo(padding, size.height - padding + 10);
    path.close();
    canvas.drawPath(path, fillPaint);

    // Draw line
    path = Path();
    for (int i = 0; i < values.length; i++) {
      final x = padding + i * xStep;
      final y = size.height -
          padding +
          10 -
          (values[i] / maxValue) * graphHeight;

      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    canvas.drawPath(path, paint);

    // Draw points
    for (int i = 0; i < values.length; i++) {
      final x = padding + i * xStep;
      final y = size.height -
          padding +
          10 -
          (values[i] / maxValue) * graphHeight;
      canvas.drawCircle(Offset(x, y), 3, pointPaint);
    }

    // Draw Y-axis label
    final textPainter = TextPainter(
      text: TextSpan(
        text: label,
        style: const TextStyle(color: Colors.grey, fontSize: 10),
      ),
      textDirection: ui.TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(
      canvas,
      Offset(10, size.height / 2 - textPainter.height / 2),
    );
  }

  @override
  bool shouldRepaint(LineChartPainter oldDelegate) => false;
}

class MultiLineChartPainter extends CustomPainter {
  final List<String> dates;
  final List<double> values1;
  final String label1;
  final Color color1;
  final List<double> values2;
  final String label2;
  final Color color2;
  final double maxValue;

  MultiLineChartPainter({
    required this.dates,
    required this.values1,
    required this.label1,
    required this.color1,
    required this.values2,
    required this.label2,
    required this.color2,
    required this.maxValue,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (values1.isEmpty || values2.isEmpty) return;

    final padding = 40.0;
    final graphWidth = size.width - padding * 2;
    final graphHeight = size.height - padding;
    final xStep = graphWidth / (values1.length - 1).clamp(1, double.infinity);

    // Draw line 1
    _drawLine(canvas, size, values1, color1, padding, xStep, graphWidth, graphHeight);

    // Draw line 2
    _drawLine(canvas, size, values2, color2, padding, xStep, graphWidth, graphHeight);
  }

  void _drawLine(
    Canvas canvas,
    Size size,
    List<double> values,
    Color color,
    double padding,
    double xStep,
    double graphWidth,
    double graphHeight,
  ) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final pointPaint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    Path path = Path();
    for (int i = 0; i < values.length; i++) {
      final x = padding + i * xStep;
      final y = size.height -
          padding +
          10 -
          (values[i] / maxValue) * graphHeight;

      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }

    canvas.drawPath(path, paint);

    // Draw points
    for (int i = 0; i < values.length; i++) {
      final x = padding + i * xStep;
      final y = size.height -
          padding +
          10 -
          (values[i] / maxValue) * graphHeight;
      canvas.drawCircle(Offset(x, y), 2.5, pointPaint);
    }
  }

  @override
  bool shouldRepaint(MultiLineChartPainter oldDelegate) => false;
}

class BarChartPainter extends CustomPainter {
  final List<String> dates;
  final List<int> values;
  final String label;
  final Color color;
  final double maxValue;

  BarChartPainter({
    required this.dates,
    required this.values,
    required this.label,
    required this.color,
    required this.maxValue,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (values.isEmpty) return;

    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final padding = 40.0;
    final graphWidth = size.width - padding * 2;
    final graphHeight = size.height - padding;
    final barWidth = graphWidth / values.length * 0.7;
    final spacing = graphWidth / values.length;

    for (int i = 0; i < values.length; i++) {
      final x = padding + i * spacing + spacing / 2 - barWidth / 2;
      final barHeight = (values[i] / maxValue) * graphHeight;
      final y = size.height - padding + 10 - barHeight;

      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(x, y, barWidth, barHeight),
          const Radius.circular(4),
        ),
        paint,
      );
    }

    // Draw Y-axis label
    final textPainter = TextPainter(
      text: TextSpan(
        text: label,
        style: const TextStyle(color: Colors.grey, fontSize: 10),
      ),
      textDirection: ui.TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(
      canvas,
      Offset(10, size.height / 2 - textPainter.height / 2),
    );
  }

  @override
  bool shouldRepaint(BarChartPainter oldDelegate) => false;
}
